from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core import rut
from apps.people.models import Person, User


class Command(BaseCommand):
    help = "Crea una cuenta de administración (y su persona) para entrar al panel."

    def handle(self, *args, **options):
        document_number = self._ask("RUT", rut.normalize)
        person = Person.objects.filter(document_number=document_number).first()
        if person and hasattr(person, "user"):
            raise CommandError("Esta persona ya tiene una cuenta.")
        if person:
            self.stdout.write(f"Se usará la persona existente: {person}")
        else:
            person = Person(
                document_number=document_number,
                first_names=self._ask("Nombres"),
                paternal_surname=self._ask("Primer apellido"),
                maternal_surname=input("Segundo apellido (opcional): ").strip(),
            )
        if not person.email:
            person.email = self._ask("Correo", lambda v: v.lower())
            if Person.objects.filter(email=person.email).exclude(pk=person.pk).exists():
                raise CommandError("Ese correo ya pertenece a otra persona.")

        while True:
            password = getpass("Contraseña: ")
            if password != getpass("Repite la contraseña: "):
                self.stderr.write("Las contraseñas no coinciden.")
                continue
            try:
                validate_password(password)
                break
            except ValidationError as error:
                self.stderr.write(" ".join(error.messages))

        with transaction.atomic():
            person.save()
            User.objects.create_superuser(person, password)
        self.stdout.write(self.style.SUCCESS(f"Cuenta creada. Inicia sesión con {person.email}."))

    def _ask(self, label, clean=lambda v: v):
        while True:
            value = input(f"{label}: ").strip()
            if not value:
                self.stderr.write("Este dato es obligatorio.")
                continue
            try:
                return clean(value)
            except ValidationError as error:
                self.stderr.write(" ".join(error.messages))
