import shutil
import tempfile
from datetime import date
from io import BytesIO

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.adoptions.models import Adoption
from apps.animals.models import AnimalDailyViews, AnimalExit, LifeStage
from apps.animals.services import thumbnail_name
from apps.core.testing import make_animal, make_person, make_species, make_user
from apps.core.testing_api import ApiClient, signed_in
from apps.organization.models import OrganizationSettings


def months_ago(n):
    today = date.today()
    total = today.year * 12 + today.month - 1 - n
    return date(total // 12, total % 12 + 1, 1)


class PublicAnimalsTests(TestCase):
    def setUp(self):
        self.client = ApiClient()
        self.dogs = make_species("Perro", "Perros")

    def test_lists_only_animals_in_care_of_visible_species(self):
        visible = make_animal(species=self.dogs)
        adopted = make_animal(species=self.dogs)
        Adoption.objects.create(animal=adopted, person=make_person(), source="import", status="signed",
                                contract_signed_at=date(2026, 1, 2), fee_charged=0)
        gone = make_animal(species=self.dogs)
        AnimalExit.objects.create(animal=gone, kind="deceased", exit_date=date(2026, 1, 2), recorded_by=make_user())
        rabbits = make_species("Conejo", "Conejos")
        rabbits.is_active = False
        rabbits.save()
        make_animal(species=rabbits)
        names = [a["name"] for a in self.client.get("/api/public/animals").json()["items"]]
        self.assertEqual(names, [visible.name])

    def test_adopted_animal_page_is_no_longer_available(self):
        animal = make_animal(species=self.dogs)
        Adoption.objects.create(animal=animal, person=make_person(), source="import", status="signed",
                                contract_signed_at=date(2026, 1, 2), fee_charged=0)
        response = self.client.get(f"/api/public/animals/{animal.slug}")
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()["detail"], "Esta ficha ya no está disponible.")

    def test_one_visit_per_device_per_day(self):
        animal = make_animal(species=self.dogs)
        self.client.get(f"/api/public/animals/{animal.slug}")
        self.client.get(f"/api/public/animals/{animal.slug}")
        ApiClient().get(f"/api/public/animals/{animal.slug}")  # another device
        self.assertEqual(AnimalDailyViews.objects.get(animal=animal).views, 2)

    def test_life_stage_filter_uses_the_species_stages(self):
        # Perro comes preloaded with Cachorro (0), Joven (12), Adulto (24) and Mayor (96 months).
        puppy = make_animal(species=self.dogs, birth_date_approx=months_ago(4), intake_date=date.today())
        make_animal(species=self.dogs, birth_date_approx=months_ago(40), intake_date=date.today())
        stage = LifeStage.objects.get(name="Cachorro")
        items = self.client.get("/api/public/animals", {"life_stage": stage.id}).json()["items"]
        self.assertEqual([(a["name"], a["life_stage"]) for a in items], [(puppy.name, "Cachorro")])


class DashboardAnimalsTests(TestCase):
    def setUp(self):
        self.client, self.user = signed_in("worker")
        self.dogs = make_species("Perro", "Perros")

    def payload(self, **extra):
        return {"name": "Canela", "species_id": self.dogs.id, "birth_date_approx": "2023-03-01", "intake_date": "2026-05-12", **extra}

    def test_any_team_account_creates_animals_with_a_unique_address(self):
        first = self.client.post_json("/api/dashboard/animals", self.payload())
        second = self.client.post_json("/api/dashboard/animals", self.payload())
        self.assertEqual(first.status_code, 201)
        self.assertEqual((first.json()["slug"], second.json()["slug"]), ("canela", "canela-2"))

    def test_spanish_validation_messages(self):
        response = self.client.post_json("/api/dashboard/animals", {"species_id": self.dogs.id})
        self.assertEqual(response.status_code, 422)
        errors = {e["field"]: e["message"] for e in response.json()["errors"]}
        self.assertEqual(errors["name"], "Este dato es obligatorio.")

    def test_requires_sign_in(self):
        response = ApiClient().get("/api/dashboard/animals")
        self.assertEqual((response.status_code, response.json()["detail"]), (401, "Inicia sesión para continuar."))

    def test_feature_and_exit(self):
        animal_id = self.client.post_json("/api/dashboard/animals", self.payload()).json()["id"]
        self.assertTrue(self.client.post_json(f"/api/dashboard/animals/{animal_id}/feature").json()["featured"])
        exit_ = self.client.post_json(f"/api/dashboard/animals/{animal_id}/exit", {"kind": "transferred", "exit_date": str(date.today())})
        self.assertEqual(exit_.json()["status"], "Trasladado")
        self.assertIsNone(OrganizationSettings.load().featured_animal_id)
        again = self.client.post_json(f"/api/dashboard/animals/{animal_id}/feature")
        self.assertEqual(again.status_code, 400)

    def test_only_administration_manages_species(self):
        response = self.client.post_json("/api/dashboard/species", {"name": "Conejo", "plural_name": "Conejos"})
        self.assertEqual(response.status_code, 403)

    def test_life_stages_must_start_at_zero(self):
        admin, _ = signed_in("admin")
        bad = admin.put_json(f"/api/dashboard/species/{self.dogs.id}/life-stages", [{"name": "Adulto", "from_months": 12}])
        self.assertEqual(bad.status_code, 400)
        ok = admin.put_json(
            f"/api/dashboard/species/{self.dogs.id}/life-stages",
            [{"name": "Adulto", "from_months": 12}, {"name": "Cachorro", "from_months": 0}],
        )
        self.assertEqual([s["name"] for s in ok.json()["life_stages"]], ["Cachorro", "Adulto"])


class PhotoTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.client, _ = signed_in("worker")
        self.animal = make_animal()

    def image(self, name="foto.png", size=(1600, 1200)):
        buffer = BytesIO()
        Image.new("RGB", size, "green").save(buffer, "PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    def test_upload_creates_light_version_and_order_defines_main_photo(self):
        first = self.client.post(f"/api/dashboard/animals/{self.animal.id}/photos", {"image": self.image()}).json()
        second = self.client.post(f"/api/dashboard/animals/{self.animal.id}/photos", {"image": self.image()}).json()
        self.assertEqual((first["position"], second["position"]), (0, 1))
        photo = self.animal.photos.get(pk=first["id"])
        with default_storage.open(thumbnail_name(photo.image.name)) as thumb, Image.open(thumb) as img:
            self.assertEqual(img.width, 800)
        order = self.client.put_json(f"/api/dashboard/animals/{self.animal.id}/photos/order", {"photo_ids": [second["id"], first["id"]]})
        self.assertEqual(order.json()[0]["id"], second["id"])

    def test_rejects_files_that_are_not_images(self):
        fake = SimpleUploadedFile("foto.png", b"no soy una imagen", content_type="image/png")
        response = self.client.post(f"/api/dashboard/animals/{self.animal.id}/photos", {"image": fake})
        self.assertEqual((response.status_code, response.json()["detail"]), (400, "El archivo no es una imagen válida."))

    def test_size_limit_is_set_by_the_organization(self):
        settings = OrganizationSettings.load()
        settings.max_upload_mb = 1
        settings.save()
        big = SimpleUploadedFile("foto.png", b"0" * (1024 * 1024 + 1), content_type="image/png")
        response = self.client.post(f"/api/dashboard/animals/{self.animal.id}/photos", {"image": big})
        self.assertIn("más de 1 MB", response.json()["detail"])



class DashboardListTests(TestCase):
    def test_rows_include_visits_returns_and_exits_filter(self):
        client, user = signed_in("worker")
        returned = make_animal(name="Rocco", intake_date=date(2025, 1, 1))
        Adoption.objects.create(animal=returned, person=make_person(), source="import", status="returned",
                                contract_signed_at=date(2025, 3, 1), fee_charged=0, returned_at=date(2025, 6, 1))
        gone = make_animal(name="Maui")
        AnimalExit.objects.create(animal=gone, kind="deceased", exit_date=date(2026, 1, 2), recorded_by=user)
        AnimalDailyViews.objects.create(animal=returned, day=date.today(), views=7)
        rows = {r["name"]: r for r in client.get("/api/dashboard/animals").json()["items"]}
        self.assertEqual((rows["Rocco"]["returns_count"], rows["Rocco"]["visits_last_30_days"]), (1, 7))
        self.assertEqual(rows["Rocco"]["status_code"], "available")
        exited = client.get("/api/dashboard/animals", {"status": "exited"}).json()["items"]
        self.assertEqual([(r["name"], r["status"]) for r in exited], [("Maui", "Falleció")])
