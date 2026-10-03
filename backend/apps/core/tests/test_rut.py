from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.core import formatting, rut


class ComputeCheckDigitTests(SimpleTestCase):
    def test_known_ruts(self):
        cases = {"12345678": "5", "15432876": "9", "9876543": "3", "18765432": "7", "16111222": "4"}
        for body, expected in cases.items():
            with self.subTest(body=body):
                self.assertEqual(rut.compute_check_digit(body), expected)

    def test_remainder_ten_is_k_and_eleven_is_zero(self):
        self.assertEqual(rut.compute_check_digit("10000013"), "K")
        self.assertEqual(rut.compute_check_digit("10000004"), "0")


class NormalizeTests(SimpleTestCase):
    def test_accepts_common_ways_of_writing_it(self):
        for value in ["12.345.678-5", "12345678-5", "123456785", " 12 345 678 5 ", "012.345.678-5"]:
            with self.subTest(value=value):
                self.assertEqual(rut.normalize(value), "12345678-5")

    def test_lowercase_k(self):
        self.assertEqual(rut.normalize("10.000.013-k"), "10000013-K")

    def test_seven_digit_body(self):
        self.assertEqual(rut.normalize("9.876.543-3"), "9876543-3")

    def test_wrong_check_digit_says_which_one_is_right(self):
        with self.assertRaises(ValidationError) as ctx:
            rut.normalize("12.345.678-0")
        self.assertEqual(ctx.exception.code, "rut_check_digit")
        self.assertIn("debería ser 5", ctx.exception.message)

    def test_rejects_incomplete_or_malformed_values(self):
        for value in ["", None, "123", "1234567890-1", "12.345.678-X", "abc"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                rut.normalize(value)

    def test_stored_form_matches_database_pattern(self):
        import re

        self.assertRegex(rut.normalize("10.000.013-k"), re.compile(rut.STORED_PATTERN))


class DisplayTests(SimpleTestCase):
    def test_groups_thousands(self):
        self.assertEqual(rut.display("12345678-5"), "12.345.678-5")
        self.assertEqual(rut.display("9876543-3"), "9.876.543-3")


class MoneyTests(SimpleTestCase):
    def test_chilean_pesos(self):
        self.assertEqual(formatting.money(30000), "$30.000")
        self.assertEqual(formatting.money(0), "$0")
        self.assertEqual(formatting.money(1250000), "$1.250.000")
