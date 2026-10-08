from datetime import date, datetime

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Field, Query, Router, Schema
from ninja.pagination import paginate

from apps.animals.models import Animal
from apps.animals.services import in_care, publicly_visible
from apps.core import rut
from apps.core.api import Mapped, Page20, bad_request, conflict, team_auth
from apps.organization.models import OrganizationSettings
from apps.people.api import PersonIn, person_data
from apps.people.services import find_or_create_person
from apps.restrictions import services as restrictions

from .models import Adoption

public_router = Router(tags=["web pública: adopción"])
dashboard_router = Router(tags=["panel: adopciones"], auth=team_auth)

OPEN = [Adoption.Status.NEW, Adoption.Status.INTERVIEW]


class AdoptionRequestIn(PersonIn):
    housing: Adoption.Housing
    has_other_pets: bool
    message: str = Field("", max_length=2000)


@public_router.post("/animals/{slug}/adoption-requests", response={201: dict})
def request_adoption(request, slug: str, payload: AdoptionRequestIn):
    """Adoption form. Never reveals whether the person is on the restriction list."""
    animal = get_object_or_404(publicly_visible(), slug=slug)
    data = person_data(payload)
    with transaction.atomic():
        person = find_or_create_person(data)
        if Adoption.objects.filter(animal=animal, person=person, status__in=OPEN).exists():
            raise conflict(f"Ya enviaste una solicitud para adoptar a {animal.name}. La fundación te contactará.")
        Adoption.objects.create(
            animal=animal, person=person, housing=payload.housing, has_other_pets=payload.has_other_pets, message=payload.message.strip()
        )
    return 201, {"detail": f"Recibimos tu solicitud para adoptar a {animal.name}. La fundación te contactará."}


# ---------- Dashboard ----------

class Ref(Schema):
    id: int
    name: str


class PersonContact(Ref):
    rut: str
    phone: str
    email: str | None
    locality: str | None


class RestrictionCheck(Schema):
    can_adopt: bool
    blocking: list[str]
    other: list[str]


class AdoptionOut(Schema):
    id: int
    animal: Ref
    person: PersonContact
    source: str
    status: str
    status_code: str
    housing: str
    has_other_pets: bool | None
    message: str
    restriction_check: RestrictionCheck
    foster_home: Ref | None
    is_foster_home_priority: bool
    foster_notice_required: bool
    foster_notified_at: datetime | None
    contract_signed_at: date | None
    fee_charged: int | None
    discount: int | None
    returned_at: date | None
    return_reason: str
    created_at: datetime


class SignIn(Schema):
    contract_signed_at: date
    fee_charged: int = Field(ge=0)
    discount: int = Field(0, ge=0)


class ReturnIn(Schema):
    returned_at: date
    reason: str = Field(min_length=1)


class Filters(Schema):
    status: Adoption.Status | None = None
    animal: int | None = None


def foster_info(adoption):
    home = adoption.animal.foster_home
    if not home:
        return None, False, False
    priority = home.person_id == adoption.person_id
    return home, priority, not priority


def out(adoption):
    check = restrictions.check(adoption.person, adoption.animal.species)
    home, priority, needs_notice = foster_info(adoption)
    p = adoption.person
    describe = lambda r: f"{r['reason']} · {r['species']}"  # noqa: E731
    return {
        "id": adoption.id,
        "animal": {"id": adoption.animal_id, "name": adoption.animal.name},
        "person": {"id": p.id, "name": p.full_name, "rut": rut.display(p.document_number), "phone": p.phone, "email": p.email,
                   "locality": p.locality.name if p.locality_id else None},
        "source": adoption.get_source_display(),
        "status": adoption.get_status_display(),
        "status_code": adoption.status,
        "housing": adoption.get_housing_display() if adoption.housing else "",
        "has_other_pets": adoption.has_other_pets,
        "message": adoption.message,
        "restriction_check": {
            "can_adopt": check["can_adopt"],
            "blocking": [describe(r) for r in check["restrictions"] if r["blocks_this_animal"]],
            "other": [describe(r) for r in check["restrictions"] if not r["blocks_this_animal"]],
        },
        "foster_home": {"id": home.id, "name": home.person.full_name} if home else None,
        "is_foster_home_priority": priority,
        "foster_notice_required": needs_notice and adoption.status in OPEN and adoption.foster_notified_at is None,
        "foster_notified_at": adoption.foster_notified_at,
        "contract_signed_at": adoption.contract_signed_at,
        "fee_charged": adoption.fee_charged,
        "discount": adoption.discount,
        "returned_at": adoption.returned_at,
        "return_reason": adoption.return_reason,
        "created_at": adoption.created_at,
    }


def queryset():
    return Adoption.objects.select_related(
        "animal__species", "animal__foster_home__person", "person__locality"
    )


def _get(adoption_id):
    return get_object_or_404(queryset(), pk=adoption_id)


def _move(adoption, request, status, **fields):
    adoption.status = status
    adoption.reviewed_by, adoption.reviewed_at = request.auth, timezone.now()
    for key, value in fields.items():
        setattr(adoption, key, value)
    adoption.save()
    return out(adoption)


def _require(adoption, allowed, action):
    if adoption.status not in allowed:
        raise bad_request(f"No se puede {action}: la solicitud está en estado “{adoption.get_status_display()}”.")


@dashboard_router.get("/adoptions", response=list[AdoptionOut])
@paginate(Page20)
def list_adoptions(request, filters: Query[Filters]):
    qs = queryset().order_by("-created_at")
    if filters.status:
        qs = qs.filter(status=filters.status)
    if filters.animal:
        qs = qs.filter(animal_id=filters.animal)
    return Mapped(qs, out)


@dashboard_router.get("/adoptions/{adoption_id}", response=AdoptionOut)
def get_adoption(request, adoption_id: int):
    return out(_get(adoption_id))


@dashboard_router.post("/adoptions/{adoption_id}/interview", response=AdoptionOut)
def schedule_interview(request, adoption_id: int):
    adoption = _get(adoption_id)
    _require(adoption, [Adoption.Status.NEW], "citar a entrevista")
    if not in_care().filter(pk=adoption.animal_id).exists():
        raise bad_request(f"{adoption.animal.name} ya no está a cargo de la fundación.")
    if not restrictions.check(adoption.person, adoption.animal.species)["can_adopt"]:
        raise bad_request("No se puede citar: esta persona tiene una restricción que aplica a esta especie.")
    return _move(adoption, request, Adoption.Status.INTERVIEW)


@dashboard_router.post("/adoptions/{adoption_id}/notify-foster", response=AdoptionOut)
def notify_foster(request, adoption_id: int):
    """Records that the foster home was told about this request."""
    adoption = _get(adoption_id)
    _require(adoption, OPEN, "avisar a la casa de acogida")
    _, priority, needs_notice = foster_info(adoption)
    if not needs_notice:
        raise bad_request("Esta solicitud no necesita aviso a una casa de acogida.")
    adoption.foster_notified_at = timezone.now()
    adoption.save(update_fields=["foster_notified_at", "updated_at"])
    return out(adoption)


@dashboard_router.post("/adoptions/{adoption_id}/sign", response=AdoptionOut)
def sign_contract(request, adoption_id: int, payload: SignIn):
    """Contract signed: the animal is adopted, leaves its foster home and the home page."""
    adoption = _get(adoption_id)
    _require(adoption, [Adoption.Status.INTERVIEW], "firmar el contrato")
    if payload.discount > payload.fee_charged:
        raise bad_request("El descuento no puede ser mayor que el aporte cobrado.")
    if payload.contract_signed_at > date.today() or payload.contract_signed_at < adoption.animal.intake_date:
        raise bad_request("La fecha del contrato debe estar entre la llegada del animal y hoy.")
    if not restrictions.check(adoption.person, adoption.animal.species)["can_adopt"]:
        raise bad_request("No se puede firmar: esta persona tiene una restricción que aplica a esta especie.")
    _, _, needs_notice = foster_info(adoption)
    if needs_notice and adoption.foster_notified_at is None:
        raise bad_request("Primero avisa a la casa de acogida de esta solicitud.")
    animal = adoption.animal
    try:
        with transaction.atomic():
            _move(adoption, request, Adoption.Status.SIGNED, **payload.dict())
            Animal.objects.filter(pk=animal.pk).update(foster_home=None)
            OrganizationSettings.objects.filter(featured_animal=animal).update(featured_animal=None)
    except IntegrityError:
        raise conflict(f"{animal.name} ya tiene una adopción firmada.") from None
    return out(_get(adoption_id))


@dashboard_router.post("/adoptions/{adoption_id}/reject", response=AdoptionOut)
def reject(request, adoption_id: int):
    adoption = _get(adoption_id)
    _require(adoption, OPEN, "rechazar")
    return _move(adoption, request, Adoption.Status.REJECTED)


@dashboard_router.post("/adoptions/{adoption_id}/return", response=AdoptionOut)
def register_return(request, adoption_id: int, payload: ReturnIn):
    """The animal came back: it is in the organization's care again."""
    adoption = _get(adoption_id)
    _require(adoption, [Adoption.Status.SIGNED], "registrar la devolución")
    if not adoption.contract_signed_at <= payload.returned_at <= date.today():
        raise bad_request("La fecha de devolución debe estar entre el contrato y hoy.")
    return _move(adoption, request, Adoption.Status.RETURNED, returned_at=payload.returned_at, return_reason=payload.reason.strip())
