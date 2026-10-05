from django.test import TestCase

from apps.core.testing import DatabaseRuleAssertions
from apps.organization.models import OrganizationSettings, Region


class OrganizationSettingsTests(DatabaseRuleAssertions, TestCase):
    def test_always_a_single_row(self):
        OrganizationSettings.load()
        OrganizationSettings(name="Otra").save()
        self.assertEqual(OrganizationSettings.objects.count(), 1)
        self.assertEqual(OrganizationSettings.objects.get().name, "Otra")

    def test_database_rejects_a_second_row(self):
        OrganizationSettings.load()
        with self.assertRejectedByDatabase():
            OrganizationSettings.objects.bulk_create([OrganizationSettings(id=2, name="Otra")])

    def test_retention_days_between_1_and_365(self):
        OrganizationSettings.load()
        with self.assertRejectedByDatabase():
            OrganizationSettings.objects.update(backup_retention_days=0)
        with self.assertRejectedByDatabase():
            OrganizationSettings.objects.update(backup_retention_days=400)

    def test_colors_must_be_hexadecimal(self):
        OrganizationSettings.load()
        with self.assertRejectedByDatabase():
            OrganizationSettings.objects.update(brand_color="verde")


class RegionDataTests(TestCase):
    def test_sixteen_chilean_regions_are_loaded(self):
        self.assertEqual(Region.objects.count(), 16)
        self.assertTrue(Region.objects.filter(code="16", name="Ñuble").exists())
