from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Field, Query, Router, Schema
from ninja.pagination import paginate

from apps.animals.models import Species
from apps.core import rut
from apps.core.api import Mapped, Page20, admin_only, bad_request, conflict, team_auth
from apps.people.models import Person

from . import services
from .models import Restriction

dashboard_router = Router(tags=["panel: restricciones"], auth=team_auth)


class RestrictionItem(Schema):
    id: int
    reason: str
    species: str
    notes: str
    created_at: datetime
    blocks_this_animal: bool


class CheckOut(Schema):
    rut: str
    name: str | None
    can_adopt: bool
    restrictions: list[RestrictionItem]


class RestrictionRow(Schema):
    id: int
    person_id: int
    name: str
    rut: str
    reason: str
    species: str
    notes: str
    created_by: str
    created_at: datetime
    lifted_at: datetime | None


class RestrictionIn(Schema):
    rut: str
    first_names: str = Field("", max_length=120)
    paternal_surname: str = Field("", max_length=80)
    maternal_surname: str = Field("", max_length=80)
    reason: Restriction.Reason
    species_id: int | None = None
    notes: str = Field(min_length=1)


def row(r):
    return {
        "id": r.id, "person_id": r.person_id, "name": r.person.full_name, "rut": rut.display(r.person.document_number),
        "reason": r.get_reason_display(), "species": r.species.plural_name if r.species else "Todas las especies",
        "notes": r.notes, "created_by": r.created_by.person.full_name, "created_at": r.created_at, "lifted_at": r.lifted_at,
    }


def _normalize(value):
    try:
        return rut.normalize(value)
    except ValidationError as exc:
        raise bad_request(exc.message) from None


@dashboard_router.get("/restrictions/check", response=CheckOut)
def check(request, rut_value: str = Query(..., alias="rut")):
    """Whether a RUT may adopt and, if not, why."""
    document_number = _normalize(rut_value)
    person = Person.objects.filter(document_number=document_number).first()
    return {"rut": rut.display(document_number), "name": person.full_name if person else None, **services.check(person)}


@dashboard_router.get("/restrictions", response=list[RestrictionRow])
@paginate(Page20)
def list_restrictions(request, include_lifted: bool = False):
    qs = Restriction.objects.select_related("person", "species", "created_by__person").order_by("-created_at")
    if not include_lifted:
        qs = qs.filter(lifted_at__isnull=True)
    return Mapped(qs, row)


@dashboard_router.post("/restrictions", response={201: RestrictionRow})
@admin_only
def create_restriction(request, payload: RestrictionIn):
    """Adds someone to the list. Creates the person if their RUT is new (then their names are required)."""
    document_number = _normalize(payload.rut)
    species = get_object_or_404(Species, pk=payload.species_id) if payload.species_id else None
    with transaction.atomic():
        person = Person.objects.filter(document_number=document_number).first()
        if not person:
            if not payload.first_names.strip() or not payload.paternal_surname.strip():
                raise bad_request("Es la primera vez que se registra este RUT: escribe sus nombres y primer apellido.")
            person = Person.objects.create(
                document_number=document_number, first_names=payload.first_names.strip(),
                paternal_surname=payload.paternal_surname.strip(), maternal_surname=payload.maternal_surname.strip(),
            )
        try:
            with transaction.atomic():
                restriction = Restriction.objects.create(
                    person=person, species=species, reason=payload.reason, notes=payload.notes.strip(), created_by=request.auth
                )
        except IntegrityError:
            raise conflict("Esta persona ya tiene una restricción vigente para esa especie.") from None
    return 201, row(restriction)


@dashboard_router.post("/restrictions/{restriction_id}/lift", response=RestrictionRow)
@admin_only
def lift(request, restriction_id: int):
    restriction = get_object_or_404(Restriction.objects.select_related("person", "species", "created_by__person"), pk=restriction_id)
    if restriction.lifted_at:
        raise bad_request("Esta restricción ya fue levantada.")
    restriction.lifted_at, restriction.lifted_by = timezone.now(), request.auth
    restriction.save(update_fields=["lifted_at", "lifted_by", "updated_at"])
    return row(restriction)
