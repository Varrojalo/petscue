from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Field, Query, Router, Schema
from ninja.pagination import paginate
from pydantic import field_validator

from apps.animals.services import publicly_visible
from apps.core import rut
from apps.core.api import Email, Mapped, Page20, admin_only, bad_request, conflict, team_auth
from apps.organization.models import Locality

from . import services
from .models import AvailabilityOption, Membership, Person, ReviewStatus, TeamMember

auth_router = Router(tags=["sesión"])
public_router = Router(tags=["web pública: postulaciones"])
dashboard_router = Router(tags=["panel: personas y postulaciones"], auth=team_auth)


# ---------- Shared schemas ----------

class PersonIn(Schema):
    """Contact data asked by every public form."""

    rut: str
    first_names: str = Field(min_length=1, max_length=120)
    paternal_surname: str = Field(min_length=1, max_length=80)
    maternal_surname: str = Field("", max_length=80)
    phone: str = Field(min_length=9, max_length=20)
    email: Email | None = None
    locality_id: int
    consent: bool

    @field_validator("rut")
    @classmethod
    def valid_rut(cls, value):
        from django.core.exceptions import ValidationError

        try:
            return rut.normalize(value)
        except ValidationError as exc:
            raise ValueError(exc.message) from None

    @field_validator("consent")
    @classmethod
    def must_consent(cls, value):
        if not value:
            raise ValueError("Debes aceptar que la fundación guarde tus datos.")
        return value

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value):
        if sum(ch.isdigit() for ch in value) < 9:
            raise ValueError("Escribe un teléfono de al menos 9 números.")
        return value.strip()


def person_data(payload):
    data = payload.dict()
    if not Locality.objects.filter(pk=data["locality_id"]).exists():
        raise bad_request("La comuna elegida no existe.")
    return data


class Named(Schema):
    id: int
    name: str


# ---------- Session ----------

class LoginIn(Schema):
    email: Email
    password: str


class MeOut(Schema):
    id: int
    name: str
    email: str
    role: str


@auth_router.get("/csrf")
def csrf(request):
    """Sets the CSRF cookie. The frontend sends its value in the X-CSRFToken header of every change."""
    return {"csrf_token": get_token(request)}


@auth_router.post("/login", response=MeOut)
def login_view(request, payload: LoginIn):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        raise bad_request("Correo o contraseña incorrectos.")
    login(request, user)
    return me_out(user)


@auth_router.post("/logout", response={204: None})
def logout_view(request):
    logout(request)
    return 204, None


@auth_router.get("/me", response=MeOut, auth=team_auth)
def me(request):
    return me_out(request.auth)


def me_out(user):
    return {"id": user.id, "name": user.person.full_name, "email": user.person.email, "role": user.role}


# ---------- Public: applications ----------

class MembershipWish(Schema):
    kind: Membership.Kind
    monthly_amount: int = Field(gt=0)
    animal_id: int | None = None


class VolunteerWish(Schema):
    availability_ids: list[int] = []


class ApplicationIn(PersonIn):
    membership: MembershipWish | None = None
    volunteer: VolunteerWish | None = None


@public_router.get("/availability-options", response=list[Named])
def availability_options(request):
    return [{"id": o.id, "name": o.label} for o in AvailabilityOption.objects.all()]


@public_router.post("/applications", response={201: dict})
def apply(request, payload: ApplicationIn):
    """'Súmate' form: as member, as volunteer, or both. Everything starts pending until the administration reviews it."""
    if not payload.membership and not payload.volunteer:
        raise bad_request("Elige si quieres ayudar como socio, como voluntario o ambas.")
    wish = payload.membership
    if wish:
        if wish.kind == Membership.Kind.SPONSORSHIP and not publicly_visible().filter(pk=wish.animal_id).exists():
            raise bad_request("Elige un animal de la fundación para apadrinar.")
        if wish.kind == Membership.Kind.DONATION and wish.animal_id:
            raise bad_request("Una cuota a la fundación no va asociada a un animal.")
    availability = []
    if payload.volunteer:
        availability = list(AvailabilityOption.objects.filter(pk__in=payload.volunteer.availability_ids))
        if len(availability) != len(set(payload.volunteer.availability_ids)):
            raise bad_request("Una de las opciones de disponibilidad no existe.")
    with transaction.atomic():
        person = services.find_or_create_person(person_data(payload))
        if wish:
            Membership.objects.create(person=person, kind=wish.kind, monthly_amount=wish.monthly_amount, animal_id=wish.animal_id)
        if payload.volunteer:
            if hasattr(person, "team_member"):
                raise conflict("Ya postulaste o eres parte del equipo de la fundación.")
            member = TeamMember.objects.create(person=person)
            member.availability.set(availability)
    return 201, {"detail": "Recibimos tu solicitud. La fundación te contactará."}


# ---------- Dashboard: applications (administration) ----------

class ApplicationOut(Schema):
    id: int
    type: str
    person: Named
    rut: str
    phone: str
    email: str | None
    detail: str
    status: str
    created_at: str


class DecisionIn(Schema):
    effective_date: date | None = None


def application_out(obj):
    person = obj.person
    if isinstance(obj, Membership):
        kind, detail = "membership", obj.get_kind_display() + (f" de {obj.animal.name}" if obj.animal_id else "") + f" · ${obj.monthly_amount:,}".replace(",", ".")
    else:
        kind, detail = "volunteer", ", ".join(o.label for o in obj.availability.all()) or "Sin disponibilidad indicada"
    return {
        "id": obj.id, "type": kind, "person": {"id": person.id, "name": person.full_name}, "rut": rut.display(person.document_number),
        "phone": person.phone, "email": person.email, "detail": detail, "status": obj.get_status_display(), "created_at": obj.created_at.isoformat(),
    }


@dashboard_router.get("/applications", response=list[ApplicationOut])
@admin_only
def list_applications(request, status: ReviewStatus = ReviewStatus.PENDING):
    memberships = Membership.objects.filter(status=status).select_related("person", "animal")
    members = TeamMember.objects.filter(status=status).select_related("person").prefetch_related("availability")
    return sorted([application_out(o) for o in [*memberships, *members]], key=lambda a: a["created_at"], reverse=True)


def _review(obj, request, status, start_field, start):
    if obj.status != ReviewStatus.PENDING:
        raise bad_request("Esta postulación ya fue revisada.")
    obj.status = status
    obj.reviewed_by, obj.reviewed_at = request.auth, timezone.now()
    if status == ReviewStatus.APPROVED:
        setattr(obj, start_field, start or date.today())
    obj.save()
    return application_out(obj)


@dashboard_router.post("/memberships/{membership_id}/approve", response=ApplicationOut)
@admin_only
def approve_membership(request, membership_id: int, payload: DecisionIn):
    return _review(get_object_or_404(Membership, pk=membership_id), request, ReviewStatus.APPROVED, "started_at", payload.effective_date)


@dashboard_router.post("/memberships/{membership_id}/reject", response=ApplicationOut)
@admin_only
def reject_membership(request, membership_id: int):
    return _review(get_object_or_404(Membership, pk=membership_id), request, ReviewStatus.REJECTED, None, None)


@dashboard_router.post("/team-members/{member_id}/approve", response=ApplicationOut)
@admin_only
def approve_team_member(request, member_id: int, payload: DecisionIn):
    return _review(get_object_or_404(TeamMember, pk=member_id), request, ReviewStatus.APPROVED, "joined_at", payload.effective_date)


@dashboard_router.post("/team-members/{member_id}/reject", response=ApplicationOut)
@admin_only
def reject_team_member(request, member_id: int):
    return _review(get_object_or_404(TeamMember, pk=member_id), request, ReviewStatus.REJECTED, None, None)


class EndIn(Schema):
    effective_date: date


@dashboard_router.post("/memberships/{membership_id}/end", response=ApplicationOut)
@admin_only
def end_membership(request, membership_id: int, payload: EndIn):
    """The member stops contributing."""
    membership = get_object_or_404(Membership, pk=membership_id)
    if membership.status != ReviewStatus.APPROVED or membership.ended_at:
        raise bad_request("Solo se puede terminar un aporte vigente.")
    if payload.effective_date < membership.started_at:
        raise bad_request("La fecha de término no puede ser anterior al inicio.")
    membership.ended_at = payload.effective_date
    membership.save(update_fields=["ended_at", "updated_at"])
    return application_out(membership)


def _fostered_names(member):
    from apps.animals.services import in_care

    return list(in_care().filter(foster_home=member).values_list("name", flat=True))


@dashboard_router.post("/team-members/{member_id}/leave", response=ApplicationOut)
@admin_only
def leave_team(request, member_id: int, payload: EndIn):
    """Leaving the team also removes the panel access. Not allowed while fostering animals."""
    member = get_object_or_404(TeamMember.objects.select_related("person"), pk=member_id)
    if member.status != ReviewStatus.APPROVED or member.left_at:
        raise bad_request("Esta persona no es parte activa del equipo.")
    if payload.effective_date < member.joined_at:
        raise bad_request("La fecha de salida no puede ser anterior a su ingreso.")
    animals = _fostered_names(member)
    if animals:
        raise bad_request(f"Primero devuelve al refugio o completa la adopción de: {', '.join(animals)}.")
    with transaction.atomic():
        member.left_at, member.is_foster_home = payload.effective_date, False
        member.save(update_fields=["left_at", "is_foster_home", "updated_at"])
        user = getattr(member.person, "user", None)
        if user:
            services.revoke_access(user, request.auth)
    return application_out(member)


@dashboard_router.get("/team-members/foster-homes", response=list[Named])
def foster_homes(request):
    """Active foster homes, for the dropdown that assigns one to an animal."""
    homes = TeamMember.objects.filter(status=ReviewStatus.APPROVED, left_at__isnull=True, is_foster_home=True).select_related("person")
    return [{"id": h.id, "name": h.person.full_name} for h in homes]


class FosterHomeIn(Schema):
    is_foster_home: bool


@dashboard_router.put("/team-members/{member_id}/foster-home", response=ApplicationOut)
@admin_only
def set_foster_home_flag(request, member_id: int, payload: FosterHomeIn):
    member = get_object_or_404(TeamMember.objects.select_related("person"), pk=member_id)
    if member.status != ReviewStatus.APPROVED or member.left_at:
        raise bad_request("Solo alguien activo del equipo puede ser casa de acogida.")
    if not payload.is_foster_home:
        animals = _fostered_names(member)
        if animals:
            raise bad_request(f"Primero devuelve al refugio o completa la adopción de: {', '.join(animals)}.")
    member.is_foster_home = payload.is_foster_home
    member.save(update_fields=["is_foster_home", "updated_at"])
    return application_out(member)


# ---------- Dashboard: people (administration) ----------

class PersonRow(Schema):
    id: int
    name: str
    rut: str
    phone: str
    email: str | None
    locality: str | None
    roles: list[str]
    panel_access: str | None


class PersonPatch(Schema):
    first_names: str | None = Field(None, min_length=1, max_length=120)
    paternal_surname: str | None = Field(None, min_length=1, max_length=80)
    maternal_surname: str | None = Field(None, max_length=80)
    phone: str | None = Field(None, max_length=20)
    email: Email | None = None
    locality_id: int | None = None


class PeopleFilters(Schema):
    group: str | None = Field(None, description="access, staff, volunteers, foster_homes o members")
    q: str = ""


def person_row(person):
    roles = []
    member = getattr(person, "team_member", None)
    if member and member.status == ReviewStatus.APPROVED and not member.left_at:
        roles.append(member.get_kind_display())
        if member.is_foster_home:
            roles.append("Casa de acogida")
    for m in person.memberships.all():
        if m.status == ReviewStatus.APPROVED and not m.ended_at:
            roles.append(m.get_kind_display() + (f" de {m.animal.name}" if m.animal_id else ""))
    user = getattr(person, "user", None)
    return {
        "id": person.id, "name": person.full_name, "rut": rut.display(person.document_number), "phone": person.phone,
        "email": person.email, "locality": person.locality.name if person.locality_id else None, "roles": roles,
        "panel_access": user.get_role_display() if user and user.is_active else None,
    }


@dashboard_router.get("/people", response=list[PersonRow])
@admin_only
@paginate(Page20)
def list_people(request, filters: Query[PeopleFilters]):
    qs = Person.objects.select_related("locality", "team_member", "user").prefetch_related("memberships__animal")
    active_member = {"team_member__status": ReviewStatus.APPROVED, "team_member__left_at__isnull": True}
    groups = {
        "access": {"user__is_active": True},
        "staff": {**active_member, "team_member__kind": TeamMember.Kind.STAFF},
        "volunteers": {**active_member, "team_member__kind": TeamMember.Kind.VOLUNTEER},
        "foster_homes": {**active_member, "team_member__is_foster_home": True},
        "members": {"memberships__status": ReviewStatus.APPROVED, "memberships__ended_at__isnull": True},
    }
    if filters.group:
        if filters.group not in groups:
            raise bad_request("Grupo no válido. Usa access, staff, volunteers, foster_homes o members.")
        qs = qs.filter(**groups[filters.group]).distinct()
    if filters.q.strip():
        from django.db.models import Q

        text = filters.q.strip()
        qs = qs.filter(Q(first_names__icontains=text) | Q(paternal_surname__icontains=text) | Q(document_number__icontains=text.replace(".", "")))
    return Mapped(qs, person_row)


@dashboard_router.get("/people/{person_id}", response=PersonRow)
@admin_only
def get_person(request, person_id: int):
    return person_row(get_object_or_404(Person, pk=person_id))


@dashboard_router.patch("/people/{person_id}", response=PersonRow)
@admin_only
def update_person(request, person_id: int, payload: PersonPatch):
    """Corrects contact data. The RUT is the person's identity and cannot be edited."""
    person = get_object_or_404(Person, pk=person_id)
    data = payload.dict(exclude_unset=True)
    if "locality_id" in data and data["locality_id"] and not Locality.objects.filter(pk=data["locality_id"]).exists():
        raise bad_request("La comuna elegida no existe.")
    if data.get("email") is None and "email" in data and hasattr(person, "user"):
        raise bad_request("Esta persona tiene cuenta en el panel y necesita un correo para iniciar sesión.")
    for key, value in data.items():
        setattr(person, key, value)
    try:
        with transaction.atomic():
            person.save()
    except IntegrityError:
        raise conflict("Ese correo ya pertenece a otra persona.") from None
    return person_row(person)


@dashboard_router.post("/people/{person_id}/revoke-access", response=PersonRow)
@admin_only
def revoke_access(request, person_id: int):
    person = get_object_or_404(Person, pk=person_id)
    user = getattr(person, "user", None)
    if not user or not user.is_active:
        raise bad_request("Esta persona no tiene acceso al panel.")
    if user == request.auth:
        raise bad_request("No puedes quitarte el acceso a ti mismo.")
    services.revoke_access(user, request.auth)
    return person_row(person)


# ---------- Dashboard: availability options (administration) ----------

class OptionIn(Schema):
    label: str = Field(min_length=1, max_length=60)
    position: int = Field(0, ge=0)


@dashboard_router.post("/settings/availability-options", response={201: Named})
@admin_only
def create_option(request, payload: OptionIn):
    try:
        option = AvailabilityOption.objects.create(**payload.dict())
    except IntegrityError:
        raise conflict("Esa opción ya existe.") from None
    return 201, {"id": option.id, "name": option.label}


@dashboard_router.patch("/settings/availability-options/{option_id}", response=Named)
@admin_only
def update_option(request, option_id: int, payload: OptionIn):
    option = get_object_or_404(AvailabilityOption, pk=option_id)
    option.label, option.position = payload.label, payload.position
    try:
        option.save()
    except IntegrityError:
        raise conflict("Esa opción ya existe.") from None
    return {"id": option.id, "name": option.label}


@dashboard_router.delete("/settings/availability-options/{option_id}", response={204: None})
@admin_only
def delete_option(request, option_id: int):
    from django.db.models import ProtectedError

    try:
        get_object_or_404(AvailabilityOption, pk=option_id).delete()
    except ProtectedError:
        raise conflict("Esta opción ya fue elegida por personas del equipo y no se puede borrar.") from None
    return 204, None
