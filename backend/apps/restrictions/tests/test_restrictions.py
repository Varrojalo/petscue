from django.test import TestCase
from django.utils import timezone

from apps.core.testing import DatabaseRuleAssertions, make_person, make_species, make_user
from apps.restrictions.models import Restriction


class RestrictionRuleTests(DatabaseRuleAssertions, TestCase):
    def setUp(self):
        self.admin = make_user(role="admin")
        self.person = make_person()
        self.dogs = make_species("Perro", "Perros")
        self.cats = make_species("Gato", "Gatos")

    def restrict(self, species=None, **fields):
        return Restriction.objects.create(
            person=self.person, species=species, reason="abuse", notes="Detalle", created_by=self.admin, **fields
        )

    def test_one_active_restriction_per_species(self):
        self.restrict(self.cats)
        self.restrict(self.dogs)
        with self.assertRejectedByDatabase():
            self.restrict(self.cats)

    def test_only_one_active_general_restriction(self):
        # NULLS NOT DISTINCT: two rows with species NULL count as duplicates.
        self.restrict(None)
        with self.assertRejectedByDatabase():
            self.restrict(None)

    def test_lifting_allows_a_new_restriction(self):
        old = self.restrict(self.cats)
        old.lifted_at, old.lifted_by = timezone.now(), self.admin
        old.save()
        self.restrict(self.cats)
        self.assertEqual(self.person.restrictions.count(), 2)

    def test_lifting_records_who_did_it(self):
        old = self.restrict(self.cats)
        with self.assertRejectedByDatabase():
            Restriction.objects.filter(pk=old.pk).update(lifted_at=timezone.now())

    def test_applies_to(self):
        cats_only = self.restrict(self.cats)
        self.assertTrue(cats_only.applies_to(self.cats))
        self.assertFalse(cats_only.applies_to(self.dogs))
        cats_only.delete()
        self.assertTrue(self.restrict(None).applies_to(self.dogs))
