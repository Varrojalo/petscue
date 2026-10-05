from datetime import date

from django.test import TestCase

from apps.adoptions.models import Adoption
from apps.core.testing import DatabaseRuleAssertions, make_animal, make_person


def web_request(animal, **fields):
    defaults = {"animal": animal, "person": make_person(), "housing": "house", "has_other_pets": False}
    return Adoption.objects.create(**{**defaults, **fields})


SIGNED = {"status": "signed", "contract_signed_at": date(2026, 3, 1), "fee_charged": 30000}


class AdoptionRuleTests(DatabaseRuleAssertions, TestCase):
    def test_many_requests_for_the_same_animal(self):
        animal = make_animal()
        web_request(animal)
        web_request(animal)
        self.assertEqual(animal.adoptions.count(), 2)

    def test_only_one_signed_adoption_per_animal(self):
        animal = make_animal()
        web_request(animal, **SIGNED)
        with self.assertRejectedByDatabase():
            web_request(animal, **SIGNED)

    def test_a_returned_animal_can_be_adopted_again(self):
        animal = make_animal()
        web_request(animal, **{**SIGNED, "status": "returned", "returned_at": date(2026, 6, 1)})
        web_request(animal, **SIGNED)
        self.assertEqual(animal.adoptions.filter(status="signed").count(), 1)

    def test_signed_needs_contract_data(self):
        with self.assertRejectedByDatabase():
            web_request(make_animal(), status="signed")

    def test_returned_needs_return_date_and_only_returned_has_one(self):
        with self.assertRejectedByDatabase():
            web_request(make_animal(), **{**SIGNED, "status": "returned"})
        with self.assertRejectedByDatabase():
            web_request(make_animal(), **SIGNED, returned_at=date(2026, 6, 1))

    def test_return_cannot_precede_the_contract(self):
        with self.assertRejectedByDatabase():
            web_request(make_animal(), **{**SIGNED, "status": "returned", "returned_at": date(2026, 1, 1)})

    def test_web_request_needs_housing_data(self):
        with self.assertRejectedByDatabase():
            Adoption.objects.create(animal=make_animal(), person=make_person())

    def test_imported_adoption_without_housing_data(self):
        adoption = Adoption.objects.create(animal=make_animal(), person=make_person(), source="import", **SIGNED)
        self.assertEqual(adoption.housing, "")
