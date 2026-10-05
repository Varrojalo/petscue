from datetime import date

from django.test import TestCase

from apps.adoptions.models import Adoption
from apps.animals.models import Animal, AnimalExit
from apps.core.testing import DatabaseRuleAssertions, make_animal, make_person, make_user
from apps.people.models import ReviewStatus, TeamMember


def sign_adoption(animal):
    return Adoption.objects.create(
        animal=animal, person=make_person(), source="import", status="signed",
        contract_signed_at=date(2026, 2, 1), fee_charged=30000,
    )


class StatusTests(TestCase):
    def test_available_by_default(self):
        self.assertEqual(make_animal().status, Animal.Status.AVAILABLE)

    def test_in_treatment(self):
        self.assertEqual(make_animal(in_treatment=True).status, Animal.Status.TREATMENT)

    def test_foster_home_wins_over_treatment(self):
        home = TeamMember.objects.create(
            person=make_person(), status=ReviewStatus.APPROVED, joined_at=date(2026, 1, 1), is_foster_home=True
        )
        self.assertEqual(make_animal(in_treatment=True, foster_home=home).status, Animal.Status.FOSTER)

    def test_signed_adoption_means_adopted(self):
        animal = make_animal()
        sign_adoption(animal)
        self.assertEqual(animal.status, Animal.Status.ADOPTED)

    def test_exit_wins_over_everything(self):
        animal = make_animal()
        sign_adoption(animal)
        AnimalExit.objects.create(animal=animal, kind="deceased", exit_date=date(2026, 5, 1), recorded_by=make_user())
        animal.refresh_from_db()
        self.assertEqual(animal.status, Animal.Status.DECEASED)


class AnimalRuleTests(DatabaseRuleAssertions, TestCase):
    def test_microchip_unique_but_many_animals_without_one(self):
        make_animal(microchip_number="")
        make_animal(microchip_number="")
        make_animal(microchip_number="941000024817356")
        with self.assertRejectedByDatabase():
            make_animal(microchip_number="941000024817356")

    def test_cannot_arrive_before_being_born(self):
        with self.assertRejectedByDatabase():
            make_animal(birth_date_approx=date(2026, 1, 1), intake_date=date(2025, 1, 1))

    def test_at_most_one_exit_per_animal(self):
        animal, user = make_animal(), make_user()
        AnimalExit.objects.create(animal=animal, kind="transferred", exit_date=date(2026, 5, 1), recorded_by=user)
        with self.assertRejectedByDatabase():
            AnimalExit.objects.create(animal=animal, kind="deceased", exit_date=date(2026, 6, 1), recorded_by=user)

    def test_photo_positions_are_unique_per_animal(self):
        from apps.animals.models import AnimalPhoto

        animal = make_animal()
        AnimalPhoto.objects.create(animal=animal, image="animals/a.jpg", position=0)
        with self.assertRejectedByDatabase():
            AnimalPhoto.objects.create(animal=animal, image="animals/b.jpg", position=0)

    def test_species_in_use_cannot_be_deleted(self):
        from django.db.models import ProtectedError

        animal = make_animal()
        with self.assertRaises(ProtectedError):
            animal.species.delete()
