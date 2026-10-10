from datetime import date, datetime

from django.shortcuts import get_object_or_404
from ninja import Field, File, Router, Schema
from ninja.files import UploadedFile

from apps.adoptions.models import Adoption
from apps.animals.models import Animal, Species
from apps.animals.services import in_care, visits_last_30_days
from apps.core.api import Email, admin_only, bad_request, check_font, check_image, team_auth
from apps.people.models import Membership, ReviewStatus, TeamMember
from apps.reports.models import StreetReport

from .models import Locality, MembershipTier, OrganizationSettings, SocialLink

public_router = Router(tags=["web pública: fundación"])
dashboard_router = Router(tags=["panel: resumen"], auth=team_auth)
settings_router = Router(tags=["panel: configuración"], auth=team_auth)


# ---------- Public ----------

class StageOut(Schema):
    id: int
    name: str
    from_months: int


class SpeciesPublic(Schema):
    id: int
    name: str
    plural_name: str
    life_stages: list[StageOut]


class SocialOut(Schema):
    id: int
    network: str
    handle: str
    position: int


class TierOut(Schema):
    id: int
    monthly_amount: int
    position: int


class FeaturedOut(Schema):
    slug: str
    name: str


class OrganizationOut(Schema):
    name: str
    street_address: str
    locality: str | None
    region: str | None
    phone: str
    email: str
    logo_url: str | None
    title_font_url: str | None
    brand_color: str
    accent_color: str
    adoption_fee: int
    street_reports_enabled: bool
    social_links: list[SocialOut]
    membership_tiers: list[TierOut]
    species: list[SpeciesPublic]
    featured_animal: FeaturedOut | None


class StatsOut(Schema):
    adoptions_this_year: int
    active_members: int
    rescued_this_year: int
    animals_in_care: int


class LocalityOut(Schema):
    id: int
    name: str
    region: str


def organization_out(s):
    featured = s.featured_animal
    show_featured = featured and in_care().filter(pk=featured.pk, species__is_active=True).exists()
    return {
        "name": s.name, "street_address": s.street_address,
        "locality": s.locality.name if s.locality_id else None, "region": s.locality.region.name if s.locality_id else None,
        "phone": s.phone, "email": s.email,
        "logo_url": s.logo.url if s.logo else None, "title_font_url": s.title_font.url if s.title_font else None,
        "brand_color": s.brand_color, "accent_color": s.accent_color, "adoption_fee": s.adoption_fee,
        "street_reports_enabled": s.street_reports_enabled,
        "social_links": list(SocialLink.objects.values("id", "network", "handle", "position")),
        "membership_tiers": list(MembershipTier.objects.values("id", "monthly_amount", "position")),
        "species": [
            {"id": sp.id, "name": sp.name, "plural_name": sp.plural_name,
             "life_stages": [{"id": st.id, "name": st.name, "from_months": st.from_months} for st in sp.life_stages.all()]}
            for sp in Species.objects.filter(is_active=True).prefetch_related("life_stages")
        ],
        "featured_animal": {"slug": featured.slug, "name": featured.name} if show_featured else None,
    }


@public_router.get("/organization", response=OrganizationOut)
def organization(request):
    """The organization's identity. The website loads it once to paint itself with its colors."""
    return organization_out(OrganizationSettings.load())


def active_members_count():
    return (
        Membership.objects.filter(status=ReviewStatus.APPROVED, ended_at__isnull=True).values("person").distinct().count()
    )


@public_router.get("/stats", response=StatsOut)
def stats(request):
    year = date.today().year
    return {
        "adoptions_this_year": Adoption.objects.filter(
            status__in=[Adoption.Status.SIGNED, Adoption.Status.RETURNED], contract_signed_at__year=year
        ).count(),
        "active_members": active_members_count(),
        "rescued_this_year": Animal.objects.filter(intake_date__year=year).count(),
        "animals_in_care": in_care().count(),
    }


@public_router.get("/localities", response=list[LocalityOut])
def localities(request, region: str | None = None):
    """Communes for the forms' dropdown. `region` filters by official region code (13 = Metropolitana)."""
    # Regions were loaded north to south, so their id gives the order Chileans expect.
    qs = Locality.objects.select_related("region").order_by("region_id", "name")
    if region:
        qs = qs.filter(region__code=region)
    return [{"id": loc.id, "name": loc.name, "region": loc.region.name} for loc in qs]


# ---------- Dashboard: summary and counters ----------

class ChartRow(Schema):
    animal_id: int
    name: str
    visits_last_30_days: int
    days_in_organization: int


class RecentRequest(Schema):
    id: int
    animal: str
    person: str
    status: str
    created_at: datetime


class SummaryOut(Schema):
    animals_in_care: int
    in_foster_homes: int
    new_adoption_requests: int
    adoptions_this_year: int
    active_members: int
    visits_chart: list[ChartRow]
    recent_requests: list[RecentRequest]


class CountersOut(Schema):
    new_adoption_requests: int
    pending_applications: int
    new_street_reports: int


@dashboard_router.get("/summary", response=SummaryOut)
def summary(request):
    animals = list(in_care().only("id", "name", "intake_date", "foster_home_id"))
    visits = visits_last_30_days([a.id for a in animals])
    today = date.today()
    recent = Adoption.objects.select_related("animal", "person").order_by("-created_at")[:5]
    return {
        "animals_in_care": len(animals),
        "in_foster_homes": sum(1 for a in animals if a.foster_home_id),
        "new_adoption_requests": Adoption.objects.filter(status=Adoption.Status.NEW).count(),
        "adoptions_this_year": stats(request)["adoptions_this_year"],
        "active_members": active_members_count(),
        "visits_chart": [
            {"animal_id": a.id, "name": a.name, "visits_last_30_days": visits.get(a.id, 0), "days_in_organization": (today - a.intake_date).days}
            for a in animals
        ],
        "recent_requests": [
            {"id": r.id, "animal": r.animal.name, "person": r.person.full_name, "status": r.get_status_display(), "created_at": r.created_at}
            for r in recent
        ],
    }


@dashboard_router.get("/counters", response=CountersOut)
def counters(request):
    """Numbers shown next to the panel's menu items. Cheap enough to refresh every minute."""
    return {
        "new_adoption_requests": Adoption.objects.filter(status=Adoption.Status.NEW).count(),
        "pending_applications": Membership.objects.filter(status=ReviewStatus.PENDING).count()
        + TeamMember.objects.filter(status=ReviewStatus.PENDING).count(),
        "new_street_reports": StreetReport.objects.filter(status=StreetReport.Status.NEW).count(),
    }


# ---------- Dashboard: settings (administration) ----------

class SettingsOut(OrganizationOut):
    locality_id: int | None
    backup_retention_days: int
    max_upload_mb: int


class SettingsPatch(Schema):
    name: str | None = Field(None, min_length=1, max_length=120)
    street_address: str | None = Field(None, max_length=160)
    locality_id: int | None = None
    phone: str | None = Field(None, max_length=20)
    email: Email | None = None
    brand_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    adoption_fee: int | None = Field(None, ge=0)
    backup_retention_days: int | None = Field(None, ge=1, le=365)
    street_reports_enabled: bool | None = None
    max_upload_mb: int | None = Field(None, ge=1)


class SocialIn(Schema):
    network: SocialLink.Network
    handle: str = Field(min_length=1, max_length=200)
    position: int = Field(0, ge=0)


class TierIn(Schema):
    monthly_amount: int = Field(gt=0)
    position: int = Field(0, ge=0)


def settings_out(s):
    return {
        **organization_out(s),
        "locality_id": s.locality_id, "backup_retention_days": s.backup_retention_days, "max_upload_mb": s.max_upload_mb,
    }


@settings_router.get("/settings", response=SettingsOut)
@admin_only
def get_settings(request):
    return settings_out(OrganizationSettings.load())


@settings_router.patch("/settings", response=SettingsOut)
@admin_only
def update_settings(request, payload: SettingsPatch):
    s = OrganizationSettings.load()
    data = payload.dict(exclude_unset=True)
    if data.get("locality_id") and not Locality.objects.filter(pk=data["locality_id"]).exists():
        raise bad_request("La comuna elegida no existe.")
    if "email" in data:
        data["email"] = data["email"] or ""
    for key, value in data.items():
        setattr(s, key, value)
    s.updated_by = request.auth
    s.save()
    return settings_out(s)


def _replace_file(field_name, upload, request):
    s = OrganizationSettings.load()
    old = getattr(s, field_name)
    if old:
        old.delete(save=False)
    if upload:
        getattr(s, field_name).save(upload.name, upload, save=False)
    s.updated_by = request.auth
    s.save()
    return settings_out(s)


@settings_router.post("/settings/logo", response=SettingsOut)
@admin_only
def upload_logo(request, file: File[UploadedFile]):
    check_image(file)
    return _replace_file("logo", file, request)


@settings_router.delete("/settings/logo", response=SettingsOut)
@admin_only
def delete_logo(request):
    return _replace_file("logo", None, request)


@settings_router.post("/settings/title-font", response=SettingsOut)
@admin_only
def upload_font(request, file: File[UploadedFile]):
    """The organization's own typeface. Only for titles; long texts keep Atkinson Hyperlegible."""
    check_font(file)
    return _replace_file("title_font", file, request)


@settings_router.delete("/settings/title-font", response=SettingsOut)
@admin_only
def delete_font(request):
    return _replace_file("title_font", None, request)


def _crud(model, schema_in, schema_out, path):
    @settings_router.post(path, response={201: schema_out}, operation_id=f"create_{model.__name__.lower()}")
    @admin_only
    def create(request, payload: schema_in):
        obj = model.objects.create(**payload.dict())
        return 201, model.objects.filter(pk=obj.pk).values(*schema_out.model_fields).get()

    @settings_router.patch(f"{path}/{{item_id}}", response=schema_out, operation_id=f"update_{model.__name__.lower()}")
    @admin_only
    def update(request, item_id: int, payload: schema_in):
        obj = get_object_or_404(model, pk=item_id)
        for key, value in payload.dict().items():
            setattr(obj, key, value)
        obj.save()
        return model.objects.filter(pk=obj.pk).values(*schema_out.model_fields).get()

    @settings_router.delete(f"{path}/{{item_id}}", response={204: None}, operation_id=f"delete_{model.__name__.lower()}")
    @admin_only
    def delete(request, item_id: int):
        get_object_or_404(model, pk=item_id).delete()
        return 204, None


_crud(SocialLink, SocialIn, SocialOut, "/settings/social-links")
_crud(MembershipTier, TierIn, TierOut, "/settings/membership-tiers")

