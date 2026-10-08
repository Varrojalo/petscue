from django.db import IntegrityError, transaction
from django.utils import timezone
from ninja.errors import HttpError

from apps.core import rut

from .models import Person, User


def find_or_create_person(data):
    """Reuses the person when the RUT already exists; a public form never overwrites someone's data."""
    document_number = rut.normalize(data["rut"])
    person = Person.objects.filter(document_number=document_number).first()
    if person:
        return person
    try:
        with transaction.atomic():
            return Person.objects.create(
                document_number=document_number,
                first_names=data["first_names"].strip(),
                paternal_surname=data["paternal_surname"].strip(),
                maternal_surname=(data.get("maternal_surname") or "").strip(),
                phone=(data.get("phone") or "").strip(),
                email=data.get("email") or None,
                locality_id=data.get("locality_id"),
                data_consent_at=timezone.now(),
            )
    except IntegrityError:
        raise HttpError(409, "Ese correo ya está registrado con otro RUT. Revisa el correo o el RUT.") from None


def revoke_access(user, by):
    if user.is_active and user.is_admin and not User.objects.filter(is_active=True, role=User.Role.ADMIN).exclude(pk=user.pk).exists():
        raise HttpError(400, "No se puede quitar el acceso a la última cuenta de administración.")
    if user.is_active:
        user.is_active = False
        user.deactivated_at = timezone.now()
        user.deactivated_by = by
        user.save(update_fields=["is_active", "deactivated_at", "deactivated_by", "updated_at"])
