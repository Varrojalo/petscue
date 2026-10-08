from datetime import date
from io import BytesIO
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Exists, OuterRef, Q, Sum
from django.utils.text import slugify
from PIL import Image

from apps.adoptions.models import Adoption

from .models import Animal, AnimalDailyViews

THUMBNAIL_WIDTH = 800


def _signed_adoption():
    return Adoption.objects.filter(animal=OuterRef("pk"), status=Adoption.Status.SIGNED)


def in_care():
    """Animals the organization is responsible for: no exit and no signed adoption."""
    return Animal.objects.filter(exit__isnull=True).exclude(Exists(_signed_adoption()))


def publicly_visible():
    return in_care().filter(species__is_active=True)


def filter_by_status(queryset, status):
    signed = Exists(_signed_adoption())
    if status in {Animal.Status.DECEASED, Animal.Status.TRANSFERRED}:
        return queryset.filter(exit__kind=status)
    if status == Animal.Status.ADOPTED:
        return queryset.filter(exit__isnull=True).filter(signed)
    base = queryset.filter(exit__isnull=True).exclude(signed)
    if status == Animal.Status.FOSTER:
        return base.filter(foster_home__isnull=False)
    if status == Animal.Status.TREATMENT:
        return base.filter(foster_home__isnull=True, in_treatment=True)
    if status == Animal.Status.AVAILABLE:
        return base.filter(foster_home__isnull=True, in_treatment=False)
    return queryset


def unique_slug(name, exclude_pk=None):
    base = slugify(name)[:70] or "animal"
    slug, n = base, 2
    while Animal.objects.filter(slug=slug).exclude(pk=exclude_pk).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def visits_last_30_days(animal_ids):
    since = date.today().toordinal() - 29
    rows = (
        AnimalDailyViews.objects.filter(animal_id__in=animal_ids, day__gte=date.fromordinal(since))
        .values("animal_id")
        .annotate(total=Sum("views"))
    )
    return {r["animal_id"]: r["total"] for r in rows}


def count_visit(animal):
    """Adds one visit for today. Callers make sure each device counts once a day."""
    with transaction.atomic():
        row, _ = AnimalDailyViews.objects.select_for_update().get_or_create(animal=animal, day=date.today())
        row.views += 1
        row.save(update_fields=["views", "updated_at"])


# ---------- Photos ----------

def thumbnail_name(image_name):
    """Derived from the original's path, so it needs no column of its own."""
    path = PurePosixPath(image_name)
    return str(path.with_name(f"{path.stem}.thumb.webp"))


def make_thumbnail(photo):
    with default_storage.open(photo.image.name, "rb") as source, Image.open(source) as img:
        img = img.convert("RGB")
        if img.width > THUMBNAIL_WIDTH:
            img = img.resize((THUMBNAIL_WIDTH, round(img.height * THUMBNAIL_WIDTH / img.width)))
        buffer = BytesIO()
        img.save(buffer, "WEBP", quality=80)
    default_storage.save(thumbnail_name(photo.image.name), ContentFile(buffer.getvalue()))


def delete_photo_files(photo):
    for name in (photo.image.name, thumbnail_name(photo.image.name)):
        if name and default_storage.exists(name):
            default_storage.delete(name)


def is_in_care(animal):
    return in_care().filter(pk=animal.pk).exists()


def searchable(queryset, text):
    return queryset.filter(Q(name__icontains=text) | Q(microchip_number__icontains=text)) if text else queryset
