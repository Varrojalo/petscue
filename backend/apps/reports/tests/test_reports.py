from django.test import TestCase

from apps.reports.models import StreetReport


class StreetReportTests(TestCase):
    def test_code_is_derived_from_the_id(self):
        report = StreetReport.objects.create(address="Av. Grecia 1500, Ñuñoa")
        self.assertEqual(report.code, f"AV-{report.pk:04d}")
