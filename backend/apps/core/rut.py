"""Chilean RUT handling.

This module is the only place that knows the RUT format. Forms, the API, imports and the restriction lookup
must all go through it, so that supporting other countries' documents later means replacing this module only.
"""

import re

from django.core.exceptions import ValidationError

_NOT_RUT_CHAR = re.compile(r"[^0-9K]")

# Stored form: body without dots or leading zeros, a dash and the check digit ("12345678-5").
STORED_PATTERN = r"^[1-9][0-9]{6,7}-[0-9K]$"


def compute_check_digit(body: str) -> str:
    """Modulo 11 check digit for the numeric body of a RUT."""
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    remainder = 11 - total % 11
    return {11: "0", 10: "K"}.get(remainder, str(remainder))


def normalize(value) -> str:
    """Turn any common way of writing a RUT into its stored form, or raise ValidationError explaining the problem."""
    cleaned = _NOT_RUT_CHAR.sub("", str(value or "").upper())
    body, check = cleaned[:-1].lstrip("0"), cleaned[-1:]
    if not 7 <= len(body) <= 8:
        raise ValidationError(
            "Escribe el RUT completo con su dígito verificador, por ejemplo 12.345.678-5.", code="rut_length"
        )
    if not body.isdigit():
        raise ValidationError("El RUT solo lleva números y un dígito verificador (0–9 o K).", code="rut_format")
    expected = compute_check_digit(body)
    if check != expected:
        raise ValidationError(
            f"El dígito verificador no coincide. Para {_group_thousands(body)} debería ser {expected}.",
            code="rut_check_digit",
        )
    return f"{body}-{check}"


def validate(value) -> None:
    """Field validator: accepts the value only if it normalizes cleanly."""
    normalize(value)


def display(stored: str) -> str:
    """'12345678-5' -> '12.345.678-5'."""
    body, check = stored.split("-")
    return f"{_group_thousands(body)}-{check}"


def _group_thousands(body: str) -> str:
    return f"{int(body):,}".replace(",", ".")
