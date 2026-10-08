from datetime import date

from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Field, File, Query, Router, Schema
from ninja.files import UploadedFile
from ninja.pagination import paginate

from apps.core.api import Mapped, Page20, admin_only, bad_request, check_image, conflict, team_auth
from apps.organization.models import OrganizationSettings
from apps.people.models import ReviewStatus, TeamMember

from . import services
from .models import Animal, AnimalExit, AnimalPhoto, LifeStage, Species, Trait

public_router = Router(tags=["web pública: animales"])
dashboard_router = Router(tags=["panel: animales"], auth=team_auth)
catalog_router = Router(tags=["panel: especies y rasgos"], auth=team_auth)

VIEW_COOKIE = "petscue_views"


# ---------- Schemas ----------

class PhotoOut(Schema):
    id: int
    url: str
    thumbnail_url: str
    position: int


class Labeled(Schema):
    id: int
    name: str


class AnimalCard(Schema):
    id: int
    slug: str
    name: str
    species: Labeled
    sex: str
    size: str
    age_months: int
    life_stage: str | None
    in_foster_home: bool
    in_treatment: bool
    cover: PhotoOut | None


class AnimalPublic(AnimalCard):
    quote: str
    story: str
    traits: list[str]
    vaccinated: bool
    sterilized: bool
    has_microchip: bool
    sponsorship_amount: int
    photos: list[PhotoOut]


class AdoptionHistoryItem(Schema):
    id: int
    person: str
    status: str
    contract_signed_at: date | None
    returned_at: date | None
    return_reason: str


class ExitOut(Schema):
    kind: str
    exit_date: date
    notes: str


class AnimalDashboard(AnimalPublic):
    status: str
    birth_date_approx: date
    intake_date: date
    days_in_organization: int
    microchip_number: str
    foster_home: Labeled | None
    featured: bool
    visits_last_30_days: int
    trait_ids: list[int]
    adoptions: list[AdoptionHistoryItem]
    exit: ExitOut | None


class AnimalIn(Schema):
    name: str = Field(min_length=1, max_length=60)
    species_id: int
    sex: Animal.Sex = Animal.Sex.UNKNOWN
    size: Animal.Size = Animal.Size.MEDIUM
    birth_date_approx: date
    intake_date: date
    in_treatment: bool = False
    quote: str = Field("", max_length=160)
    story: str = ""
    vaccinated: bool = False
    sterilized: bool = False
    microchip_number: str = Field("", max_length=20)
    sponsorship_amount: int = Field(0, ge=0)
    trait_ids: list[int] = []


class AnimalPatch(Schema):
    name: str | None = Field(None, min_length=1, max_length=60)
    species_id: int | None = None
    sex: Animal.Sex | None = None
    size: Animal.Size | None = None
    birth_date_approx: date | None = None
    intake_date: date | None = None
    in_treatment: bool | None = None
    quote: str | None = Field(None, max_length=160)
    story: str | None = None
    vaccinated: bool | None = None
    sterilized: bool | None = None
    microchip_number: str | None = Field(None, max_length=20)
    sponsorship_amount: int | None = Field(None, ge=0)
    trait_ids: list[int] | None = None


class FosterIn(Schema):
    team_member_id: int | None


class ExitIn(Schema):
    kind: AnimalExit.Kind
    exit_date: date
    notes: str = ""


class PhotoOrderIn(Schema):
    photo_ids: list[int]


class TraitIn(Schema):
    label: str = Field(min_length=1, max_length=60)


class TraitOut(Schema):
    id: int
    label: str


class LifeStageIn(Schema):
    name: str = Field(min_length=1, max_length=40)
    from_months: int = Field(ge=0)


class SpeciesIn(Schema):
    name: str = Field(min_length=1, max_length=60)
    plural_name: str = Field(min_length=1, max_length=60)
    is_active: bool = True
    position: int = Field(0, ge=0)


class SpeciesPatch(Schema):
    name: str | None = Field(None, min_length=1, max_length=60)
    plural_name: str | None = Field(None, min_length=1, max_length=60)
    is_active: bool | None = None
    position: int | None = Field(None, ge=0)


class LifeStageOut(Schema):
    id: int
    name: str
    from_months: int


class SpeciesOut(Schema):
    id: int
    name: str
    plural_name: str
    is_active: bool
    position: int
    life_stages: list[LifeStageOut]


# ---------- Serialization ----------

def photo_out(photo):
    return {
        "id": photo.id,
        "url": photo.image.url,
        "thumbnail_url": default_storage.url(services.thumbnail_name(photo.image.name)),
        "position": photo.position,
    }


def card(animal):
    photos = list(animal.photos.all())
    stage = animal.life_stage
    return {
        "id": animal.id,
        "slug": animal.slug,
        "name": animal.name,
        "species": {"id": animal.species_id, "name": animal.species.name},
        "sex": animal.get_sex_display(),
        "size": animal.get_size_display(),
        "age_months": animal.age_months,
        "life_stage": stage.name if stage else None,
        "in_foster_home": animal.foster_home_id is not None,
        "in_treatment": animal.in_treatment,
        "cover": photo_out(photos[0]) if photos else None,
    }


def public_detail(animal):
    return {
        **card(animal),
        "quote": animal.quote,
        "story": animal.story,
        "traits": [t.label for t in animal.traits.all()],
        "vaccinated": animal.vaccinated,
        "sterilized": animal.sterilized,
        "has_microchip": bool(animal.microchip_number),
        "sponsorship_amount": animal.sponsorship_amount,
        "photos": [photo_out(p) for p in animal.photos.all()],
    }


def dashboard_detail(animal):
    exit_ = getattr(animal, "exit", None)
    featured_id = OrganizationSettings.load().featured_animal_id
    return {
        **public_detail(animal),
        "status": animal.Status(animal.status).label,
        "birth_date_approx": animal.birth_date_approx,
        "intake_date": animal.intake_date,
        "days_in_organization": (date.today() - animal.intake_date).days,
        "microchip_number": animal.microchip_number,
        "foster_home": {"id": animal.foster_home_id, "name": animal.foster_home.person.full_name} if animal.foster_home_id else None,
        "featured": featured_id == animal.id,
        "visits_last_30_days": services.visits_last_30_days([animal.id]).get(animal.id, 0),
        "trait_ids": [t.id for t in animal.traits.all()],
        "adoptions": [
            {
                "id": a.id, "person": a.person.full_name, "status": a.get_status_display(),
                "contract_signed_at": a.contract_signed_at, "returned_at": a.returned_at, "return_reason": a.return_reason,
            }
            for a in animal.adoptions.select_related("person").order_by("-created_at")
        ],
        "exit": {"kind": exit_.get_kind_display(), "exit_date": exit_.exit_date, "notes": exit_.notes} if exit_ else None,
    }


def with_relations(queryset):
    return queryset.select_related("species", "foster_home__person").prefetch_related("photos", "traits", "species__life_stages")


def shift_months(day, months):
    """date `months` months before `day` (day clamped to the month's length)."""
    import calendar

    total = day.year * 12 + day.month - 1 - months
    year, month = divmod(total, 12)
    return day.replace(year=year, month=month + 1, day=min(day.day, calendar.monthrange(year, month + 1)[1]))


def filter_life_stage(queryset, stage):
    nxt = stage.species.life_stages.filter(from_months__gt=stage.from_months).order_by("from_months").first()
    today = date.today()
    queryset = queryset.filter(species=stage.species, birth_date_approx__lte=shift_months(today, stage.from_months))
    if nxt:
        queryset = queryset.filter(birth_date_approx__gt=shift_months(today, nxt.from_months))
    return queryset


# ---------- Public ----------

class PublicFilters(Schema):
    species: int | None = None
    size: Animal.Size | None = None
    life_stage: int | None = None


@public_router.get("/animals", response=list[AnimalCard])
@paginate(Page20)
def public_list(request, filters: Query[PublicFilters]):
    """Animals looking for a family, with optional filters."""
    qs = with_relations(services.publicly_visible())
    if filters.species:
        qs = qs.filter(species_id=filters.species)
    if filters.size:
        qs = qs.filter(size=filters.size)
    if filters.life_stage:
        qs = filter_life_stage(qs, get_object_or_404(LifeStage, pk=filters.life_stage))
    return Mapped(qs, card)


@public_router.get("/animals/{slug}", response={200: AnimalPublic, 410: dict})
def public_detail_view(request, slug: str, response: HttpResponse):
    """An animal's page. Counts one visit per device per day."""
    animal = get_object_or_404(with_relations(Animal.objects.all()), slug=slug)
    if not services.publicly_visible().filter(pk=animal.pk).exists():
        return 410, {"detail": "Esta ficha ya no está disponible."}
    today = date.today().isoformat()
    stamp, _, seen = request.COOKIES.get(VIEW_COOKIE, "").partition(":")
    seen_ids = set(seen.split(",")) if stamp == today and seen else set()
    if str(animal.id) not in seen_ids:
        services.count_visit(animal)
        seen_ids.add(str(animal.id))
        response.set_cookie(VIEW_COOKIE, f"{today}:{','.join(sorted(seen_ids))}", max_age=86400, samesite="Lax")
    return 200, public_detail(animal)


# ---------- Dashboard: animals ----------

class DashboardFilters(Schema):
    status: Animal.Status | None = None
    species: int | None = None
    q: str = ""


def _get(animal_id):
    return get_object_or_404(with_relations(Animal.objects.all()), pk=animal_id)


def _require_in_care(animal, action):
    if not services.is_in_care(animal):
        raise bad_request(f"No se puede {action}: el animal ya fue adoptado o salió de la fundación.")


def _apply(animal, data):
    traits = data.pop("trait_ids", None)
    if "species_id" in data:
        get_object_or_404(Species, pk=data["species_id"])
    for key, value in data.items():
        setattr(animal, key, value)
    try:
        with transaction.atomic():
            animal.save()
            if traits is not None:
                found = list(Trait.objects.filter(pk__in=traits))
                if len(found) != len(set(traits)):
                    raise bad_request("Uno de los rasgos no existe.")
                animal.traits.set(found)
    except IntegrityError as exc:
        if "microchip" in str(exc):
            raise conflict("Ya hay un animal con ese número de microchip.") from None
        if "intake_after_birth" in str(exc):
            raise bad_request("La fecha de llegada no puede ser anterior a la de nacimiento.") from None
        raise


@dashboard_router.get("/animals", response=list[AnimalCard])
@paginate(Page20)
def dashboard_list(request, filters: Query[DashboardFilters]):
    """Every animal, including adopted ones and exits, which the website does not show."""
    qs = services.searchable(with_relations(Animal.objects.all()), filters.q.strip())
    if filters.species:
        qs = qs.filter(species_id=filters.species)
    if filters.status:
        qs = services.filter_by_status(qs, filters.status)
    return Mapped(qs, card)


@dashboard_router.post("/animals", response={201: AnimalDashboard})
def create_animal(request, payload: AnimalIn):
    data = payload.dict()
    animal = Animal(slug=services.unique_slug(data["name"]))
    _apply(animal, data)
    return 201, dashboard_detail(_get(animal.pk))


@dashboard_router.get("/animals/{animal_id}", response=AnimalDashboard)
def get_animal(request, animal_id: int):
    return dashboard_detail(_get(animal_id))


@dashboard_router.patch("/animals/{animal_id}", response=AnimalDashboard)
def update_animal(request, animal_id: int, payload: AnimalPatch):
    animal = _get(animal_id)
    _apply(animal, payload.dict(exclude_unset=True))
    return dashboard_detail(_get(animal_id))


@dashboard_router.post("/animals/{animal_id}/photos", response={201: PhotoOut})
def upload_photo(request, animal_id: int, image: File[UploadedFile]):
    animal = _get(animal_id)
    check_image(image)
    last = AnimalPhoto.objects.filter(animal=animal).order_by("-position").values_list("position", flat=True).first()
    position = 0 if last is None else last + 1
    photo = AnimalPhoto.objects.create(animal=animal, image=image, position=position)
    services.make_thumbnail(photo)
    return 201, photo_out(photo)


@dashboard_router.put("/animals/{animal_id}/photos/order", response=list[PhotoOut])
def reorder_photos(request, animal_id: int, payload: PhotoOrderIn):
    """The first photo in the list becomes the main one."""
    animal = _get(animal_id)
    photos = {p.id: p for p in animal.photos.all()}
    if sorted(payload.photo_ids) != sorted(photos):
        raise bad_request("La lista debe incluir todas las fotos del animal, una vez cada una.")
    with transaction.atomic():
        for offset, photo in enumerate(photos.values()):  # move out of the way first: (animal, position) is unique
            AnimalPhoto.objects.filter(pk=photo.pk).update(position=10_000 + offset)
        for position, photo_id in enumerate(payload.photo_ids):
            AnimalPhoto.objects.filter(pk=photo_id).update(position=position)
    return [photo_out(p) for p in AnimalPhoto.objects.filter(animal=animal).order_by("position")]


@dashboard_router.delete("/animals/{animal_id}/photos/{photo_id}", response={204: None})
def delete_photo(request, animal_id: int, photo_id: int):
    photo = get_object_or_404(AnimalPhoto, pk=photo_id, animal_id=animal_id)
    services.delete_photo_files(photo)
    photo.delete()
    return 204, None


@dashboard_router.put("/animals/{animal_id}/foster-home", response=AnimalDashboard)
def set_foster_home(request, animal_id: int, payload: FosterIn):
    """Assigns a foster home, or returns the animal to the shelter with `null`."""
    animal = _get(animal_id)
    _require_in_care(animal, "cambiar la casa de acogida")
    if payload.team_member_id is not None:
        home = get_object_or_404(TeamMember, pk=payload.team_member_id)
        if not (home.status == ReviewStatus.APPROVED and home.left_at is None and home.is_foster_home):
            raise bad_request("Esa persona no es una casa de acogida activa del equipo.")
    animal.foster_home_id = payload.team_member_id
    animal.save(update_fields=["foster_home", "updated_at"])
    return dashboard_detail(_get(animal_id))


@dashboard_router.post("/animals/{animal_id}/feature", response=AnimalDashboard)
def feature_animal(request, animal_id: int):
    """Makes the animal the protagonist of the website's home page."""
    animal = _get(animal_id)
    _require_in_care(animal, "destacar al animal")
    if not animal.species.is_active:
        raise bad_request("No se puede destacar: su especie está oculta en la web.")
    settings = OrganizationSettings.load()
    settings.featured_animal = animal
    settings.updated_by = request.auth
    settings.save()
    return dashboard_detail(animal)


@dashboard_router.delete("/animals/{animal_id}/feature", response=AnimalDashboard)
def unfeature_animal(request, animal_id: int):
    settings = OrganizationSettings.load()
    if settings.featured_animal_id == animal_id:
        settings.featured_animal = None
        settings.updated_by = request.auth
        settings.save()
    return dashboard_detail(_get(animal_id))


@dashboard_router.post("/animals/{animal_id}/exit", response=AnimalDashboard)
def register_exit(request, animal_id: int, payload: ExitIn):
    """Death or transfer: takes the animal off the website, its foster home and the home page."""
    animal = _get(animal_id)
    _require_in_care(animal, "registrar la salida")
    if payload.exit_date < animal.intake_date or payload.exit_date > date.today():
        raise bad_request("La fecha de salida debe estar entre la llegada del animal y hoy.")
    with transaction.atomic():
        AnimalExit.objects.create(animal=animal, recorded_by=request.auth, **payload.dict())
        animal.foster_home = None
        animal.save(update_fields=["foster_home", "updated_at"])
        OrganizationSettings.objects.filter(featured_animal=animal).update(featured_animal=None)
    return dashboard_detail(_get(animal_id))


# ---------- Dashboard: traits and species ----------

@catalog_router.get("/traits", response=list[TraitOut])
def list_traits(request):
    return [{"label": t.label, "id": t.id} for t in Trait.objects.all()]


@catalog_router.post("/traits", response={201: TraitOut})
def create_trait(request, payload: TraitIn):
    label = " ".join(payload.label.split())
    label = label[0].upper() + label[1:]
    if Trait.objects.filter(label__iexact=label).exists():
        raise conflict("Ese rasgo ya existe.")
    trait = Trait.objects.create(label=label)
    return 201, {"id": trait.id, "label": trait.label}


def species_out(species):
    return {
        "id": species.id, "name": species.name, "plural_name": species.plural_name, "is_active": species.is_active,
        "position": species.position, "life_stages": [{"id": s.id, "name": s.name, "from_months": s.from_months} for s in species.life_stages.all()],
    }


@catalog_router.get("/species", response=list[SpeciesOut])
def list_species(request):
    return [species_out(s) for s in Species.objects.prefetch_related("life_stages")]


@catalog_router.post("/species", response={201: SpeciesOut})
@admin_only
def create_species(request, payload: SpeciesIn):
    if Species.objects.filter(name__iexact=payload.name.strip()).exists():
        raise conflict("Esa especie ya existe.")
    return 201, species_out(Species.objects.create(**payload.dict()))


@catalog_router.patch("/species/{species_id}", response=SpeciesOut)
@admin_only
def update_species(request, species_id: int, payload: SpeciesPatch):
    species = get_object_or_404(Species, pk=species_id)
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(species, key, value)
    try:
        species.save()
    except IntegrityError:
        raise conflict("Esa especie ya existe.") from None
    return species_out(species)


@catalog_router.put("/species/{species_id}/life-stages", response=SpeciesOut)
@admin_only
def replace_life_stages(request, species_id: int, payload: list[LifeStageIn]):
    """Replaces the species' age stages. The first one starts at 0 months."""
    species = get_object_or_404(Species, pk=species_id)
    starts = [s.from_months for s in payload]
    names = [s.name.strip().lower() for s in payload]
    if not payload or min(starts) != 0:
        raise bad_request("La primera etapa debe empezar en 0 meses.")
    if len(set(starts)) != len(starts) or len(set(names)) != len(names):
        raise bad_request("Cada etapa debe tener un nombre y una edad de inicio distintos.")
    with transaction.atomic():
        species.life_stages.all().delete()
        LifeStage.objects.bulk_create(
            [LifeStage(species=species, name=s.name.strip(), from_months=s.from_months) for s in sorted(payload, key=lambda s: s.from_months)]
        )
    return species_out(Species.objects.prefetch_related("life_stages").get(pk=species_id))

