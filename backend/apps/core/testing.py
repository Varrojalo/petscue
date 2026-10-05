"""Helpers shared by the test suites of every app."""

from contextlib import contextmanager
from datetime import date
from itertools import count

from django.db import IntegrityError, transaction

from apps.core import rut

_seq = count(10_000_000)


def next_rut():
    body = str(next(_seq))
    return f"{body}-{rut.compute_check_digit(body)}"


def make_person(**fields):
    from apps.people.models import Person

    defaults = {"document_number": next_rut(), "first_names": "Ana", "paternal_surname": "Pérez"}
    return Person.objects.create(**{**defaults, **fields})


def make_user(role="worker", password="una-clave-segura-123", **person_fields):
    from apps.people.models import User

    person = make_person(email=person_fields.pop("email", f"{next(_seq)}@example.org"), **person_fields)
    return User.objects.create_user(person, password, role=role)


def make_species(name="Perro", plural="Perros"):
    from apps.animals.models import Species

    return Species.objects.get_or_create(name=name, defaults={"plural_name": plural})[0]


def make_animal(**fields):
    from apps.animals.models import Animal

    n = next(_seq)
    defaults = {
        "slug": f"animal-{n}",
        "name": f"Animal {n}",
        "species": fields.pop("species", None) or make_species(),
        "birth_date_approx": date(2022, 1, 1),
        "intake_date": date(2025, 1, 1),
    }
    return Animal.objects.create(**{**defaults, **fields})


class DatabaseRuleAssertions:
    @contextmanager
    def assertRejectedByDatabase(self):
        """The block must fail with an IntegrityError raised by PostgreSQL itself."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            yield
