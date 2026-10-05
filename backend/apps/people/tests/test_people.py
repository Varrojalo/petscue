from datetime import date
from io import StringIO
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.core.testing import DatabaseRuleAssertions, make_animal, make_person, make_user
from apps.people.models import Membership, Person, ReviewStatus, TeamMember, User


class PersonTests(DatabaseRuleAssertions, TestCase):
    def test_rut_is_stored_in_normal_form(self):
        person = make_person(document_number="12.345.678-5")
        self.assertEqual(person.document_number, "12345678-5")

    def test_invalid_rut_never_reaches_the_database(self):
        with self.assertRaises(ValidationError):
            make_person(document_number="12.345.678-0")
        self.assertFalse(Person.objects.exists())

    def test_database_rejects_a_rut_not_in_stored_form(self):
        person = make_person()
        with self.assertRejectedByDatabase():
            Person.objects.filter(pk=person.pk).update(document_number="12.345.678-5")

    def test_rut_is_unique(self):
        make_person(document_number="12345678-5")
        with self.assertRejectedByDatabase():
            make_person(document_number="12.345.678-5")

    def test_email_is_unique_and_case_insensitive_on_save(self):
        make_person(email="Rosa@Example.org")
        with self.assertRejectedByDatabase():
            make_person(email="rosa@example.org")

    def test_many_people_without_email(self):
        make_person(email="")
        make_person(email=None)
        self.assertEqual(Person.objects.filter(email__isnull=True).count(), 2)


class UserTests(DatabaseRuleAssertions, TestCase):
    def test_signs_in_with_the_persons_email(self):
        user = make_user(email="marta@example.org", password="una-clave-segura-123")
        self.assertTrue(self.client.login(username="MARTA@example.org", password="una-clave-segura-123"))
        self.assertEqual(user.get_username(), "marta@example.org")

    def test_revoked_account_cannot_sign_in(self):
        user = make_user(email="diego@example.org")
        user.is_active = False
        user.deactivated_at = timezone.now()
        user.save()
        self.assertFalse(self.client.login(username="diego@example.org", password="una-clave-segura-123"))

    def test_database_requires_revocation_date_when_inactive(self):
        user = make_user()
        with self.assertRejectedByDatabase():
            User.objects.filter(pk=user.pk).update(is_active=False)

    def test_one_account_per_person(self):
        user = make_user()
        with self.assertRejectedByDatabase():
            User.objects.create(person=user.person, password="x")

    def test_person_without_email_cannot_have_account(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(make_person(), "una-clave-segura-123")

    def test_admin_panel_follows_role(self):
        make_user(role="admin", email="admin@example.org")
        make_user(role="worker", email="worker@example.org")
        self.client.login(username="admin@example.org", password="una-clave-segura-123")
        self.assertEqual(self.client.get("/admin/animals/animal/").status_code, 200)
        self.client.logout()
        self.client.login(username="worker@example.org", password="una-clave-segura-123")
        self.assertEqual(self.client.get("/admin/animals/animal/").status_code, 403)


class TeamMemberTests(DatabaseRuleAssertions, TestCase):
    def test_pending_application_has_no_dates(self):
        member = TeamMember.objects.create(person=make_person())
        self.assertEqual(member.status, ReviewStatus.PENDING)
        with self.assertRejectedByDatabase():
            TeamMember.objects.filter(pk=member.pk).update(joined_at=date(2026, 1, 1))

    def test_approved_member_needs_joined_date(self):
        with self.assertRejectedByDatabase():
            TeamMember.objects.create(person=make_person(), status=ReviewStatus.APPROVED)

    def test_only_approved_members_can_be_foster_homes(self):
        with self.assertRejectedByDatabase():
            TeamMember.objects.create(person=make_person(), is_foster_home=True)
        member = TeamMember.objects.create(
            person=make_person(), status=ReviewStatus.APPROVED, joined_at=date(2026, 1, 1), is_foster_home=True
        )
        self.assertTrue(member.is_active_member)


class MembershipTests(DatabaseRuleAssertions, TestCase):
    def test_sponsorship_needs_an_animal(self):
        with self.assertRejectedByDatabase():
            Membership.objects.create(person=make_person(), kind="sponsorship", monthly_amount=7000)

    def test_donation_cannot_point_to_an_animal(self):
        with self.assertRejectedByDatabase():
            Membership.objects.create(person=make_person(), kind="donation", monthly_amount=5000, animal=make_animal())

    def test_approved_membership_needs_start_date(self):
        with self.assertRejectedByDatabase():
            Membership.objects.create(
                person=make_person(), kind="donation", monthly_amount=5000, status=ReviewStatus.APPROVED
            )

    def test_a_person_can_hold_several_memberships(self):
        person = make_person()
        Membership.objects.create(person=person, kind="donation", monthly_amount=5000)
        Membership.objects.create(person=person, kind="sponsorship", monthly_amount=7000, animal=make_animal())
        self.assertEqual(person.memberships.count(), 2)


class CreateAdminCommandTests(TestCase):
    def test_creates_person_and_admin_account(self):
        answers = iter(["12.345.678-5", "Marta", "González", "", "Marta@Example.org"])
        with mock.patch("builtins.input", lambda _: next(answers)), mock.patch(
            "apps.people.management.commands.create_admin.getpass", return_value="una-clave-segura-123"
        ):
            call_command("create_admin", stdout=StringIO(), stderr=StringIO())
        user = User.objects.get()
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertEqual(user.person.document_number, "12345678-5")
        self.assertTrue(self.client.login(username="marta@example.org", password="una-clave-segura-123"))
