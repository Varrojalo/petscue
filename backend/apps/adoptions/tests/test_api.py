from datetime import date

from django.test import TestCase

from apps.adoptions.models import Adoption
from apps.core.testing import make_animal, make_person, make_species, next_rut
from apps.core.testing_api import ApiClient, signed_in
from apps.organization.models import Locality, OrganizationSettings
from apps.people.models import Person, ReviewStatus, TeamMember
from apps.restrictions.models import Restriction


def form(**extra):
    return {
        "rut": next_rut(), "first_names": "Elena", "paternal_surname": "Ruiz", "phone": "+56 9 6231 9087",
        "email": "elena@example.org", "locality_id": Locality.objects.get(code="13120").id, "consent": True,
        "housing": "house_with_yard", "has_other_pets": False, **extra,
    }


class PublicAdoptionRequestTests(TestCase):
    def setUp(self):
        self.client = ApiClient()
        self.animal = make_animal(name="Canela")

    def url(self):
        return f"/api/public/animals/{self.animal.slug}/adoption-requests"

    def test_creates_person_and_request(self):
        response = self.client.post_json(self.url(), form())
        self.assertEqual(response.status_code, 201)
        adoption = Adoption.objects.get()
        self.assertEqual((adoption.status, adoption.person.first_names), ("new", "Elena"))
        self.assertIsNotNone(adoption.person.data_consent_at)

    def test_existing_person_is_reused_and_not_overwritten(self):
        person = make_person(first_names="Rosa")
        self.client.post_json(self.url(), form(rut=person.document_number, first_names="Otra", email="otra@example.org"))
        self.assertEqual(Person.objects.count(), 1)
        self.assertEqual(Person.objects.get().first_names, "Rosa")

    def test_same_open_request_twice(self):
        data = form()
        self.client.post_json(self.url(), data)
        self.assertEqual(self.client.post_json(self.url(), data).status_code, 409)

    def test_invalid_rut_and_missing_consent_in_spanish(self):
        response = self.client.post_json(self.url(), form(rut="12.345.678-0", consent=False))
        errors = {e["field"]: e["message"] for e in response.json()["errors"]}
        self.assertIn("debería ser 5", errors["rut"])
        self.assertEqual(errors["consent"], "Debes aceptar que la fundación guarde tus datos.")

    def test_restricted_person_gets_the_same_answer(self):
        person = make_person()
        admin = signed_in("admin")[1]
        Restriction.objects.create(person=person, reason="abuse", notes="x", created_by=admin)
        response = self.client.post_json(self.url(), form(rut=person.document_number))
        self.assertEqual(response.status_code, 201)


class AdoptionFlowTests(TestCase):
    def setUp(self):
        self.client, self.user = signed_in("worker")
        self.dogs = make_species("Perro", "Perros")
        self.animal = make_animal(species=self.dogs, intake_date=date(2026, 1, 1))
        self.adoption = Adoption.objects.create(animal=self.animal, person=make_person(), housing="house", has_other_pets=False)

    def act(self, action, data=None):
        return self.client.post_json(f"/api/dashboard/adoptions/{self.adoption.id}/{action}", data)

    def sign_data(self):
        return {"contract_signed_at": str(date.today()), "fee_charged": 30000, "discount": 0}

    def test_full_cycle_with_return(self):
        self.assertEqual(self.act("interview").json()["status_code"], "interview")
        signed = self.act("sign", self.sign_data()).json()
        self.assertEqual(signed["status_code"], "signed")
        animal = self.client.get(f"/api/dashboard/animals/{self.animal.id}").json()
        self.assertEqual(animal["status"], "Adoptado")
        returned = self.act("return", {"returned_at": str(date.today()), "reason": "La familia se mudó"}).json()
        self.assertEqual(returned["status_code"], "returned")
        self.assertEqual(self.client.get(f"/api/dashboard/animals/{self.animal.id}").json()["status"], "Disponible")

    def test_restriction_for_the_species_blocks_the_interview(self):
        admin = signed_in("admin")[1]
        Restriction.objects.create(person=self.adoption.person, species=self.dogs, reason="abuse", notes="x", created_by=admin)
        response = self.act("interview")
        self.assertEqual(response.status_code, 400)
        detail = self.client.get(f"/api/dashboard/adoptions/{self.adoption.id}").json()["restriction_check"]
        self.assertEqual((detail["can_adopt"], detail["blocking"]), (False, ["Maltrato · Perros"]))

    def test_restriction_for_another_species_does_not_block(self):
        admin = signed_in("admin")[1]
        cats = make_species("Gato", "Gatos")
        Restriction.objects.create(person=self.adoption.person, species=cats, reason="abuse", notes="x", created_by=admin)
        self.assertEqual(self.act("interview").status_code, 200)

    def test_foster_home_must_be_notified_before_signing(self):
        home = TeamMember.objects.create(person=make_person(), status=ReviewStatus.APPROVED, joined_at=date(2026, 1, 1), is_foster_home=True)
        self.animal.foster_home = home
        self.animal.save()
        OrganizationSettings.objects.update_or_create(pk=1, defaults={"name": "F", "featured_animal": self.animal})
        self.act("interview")
        blocked = self.act("sign", self.sign_data())
        self.assertEqual(blocked.json()["detail"], "Primero avisa a la casa de acogida de esta solicitud.")
        self.act("notify-foster")
        self.assertEqual(self.act("sign", self.sign_data()).status_code, 200)
        self.animal.refresh_from_db()
        self.assertIsNone(self.animal.foster_home)
        self.assertIsNone(OrganizationSettings.load().featured_animal)

    def test_foster_home_adopting_its_animal_needs_no_notice(self):
        home = TeamMember.objects.create(person=self.adoption.person, status=ReviewStatus.APPROVED, joined_at=date(2026, 1, 1), is_foster_home=True)
        self.animal.foster_home = home
        self.animal.save()
        detail = self.client.get(f"/api/dashboard/adoptions/{self.adoption.id}").json()
        self.assertEqual((detail["is_foster_home_priority"], detail["foster_notice_required"]), (True, False))

    def test_discount_cannot_exceed_fee(self):
        self.act("interview")
        response = self.act("sign", {**self.sign_data(), "discount": 40000})
        self.assertEqual(response.status_code, 400)
