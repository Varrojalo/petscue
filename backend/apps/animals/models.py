from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Species(TimeStampedModel):
    """Species each organization rescues. Created by the admin; hidden instead of deleted once used."""

    name = models.CharField("nombre", max_length=60, unique=True)
    plural_name = models.CharField("nombre en plural", max_length=60)
    is_active = models.BooleanField("visible en la web", default=True)
    position = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "especie"
        verbose_name_plural = "especies"
        ordering = ["position", "name"]

    def __str__(self):
        return self.name


class LifeStage(TimeStampedModel):
    """Age stages defined by the organization for each species (a cat is old later than a rabbit)."""

    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="life_stages", verbose_name="especie")
    name = models.CharField("nombre", max_length=40)
    from_months = models.PositiveSmallIntegerField("desde (meses)", help_text="La primera etapa de cada especie empieza en 0.")

    class Meta:
        verbose_name = "etapa de edad"
        verbose_name_plural = "etapas de edad"
        ordering = ["species", "from_months"]
        constraints = [
            models.UniqueConstraint(fields=["species", "from_months"], name="life_stage_unique_start"),
            models.UniqueConstraint(fields=["species", "name"], name="life_stage_unique_name"),
        ]

    def __str__(self):
        return f"{self.species} · {self.name}"


class Trait(TimeStampedModel):
    label = models.CharField("rasgo", max_length=60, unique=True)

    class Meta:
        verbose_name = "rasgo"
        verbose_name_plural = "rasgos"
        ordering = ["label"]

    def __str__(self):
        return self.label


class Animal(TimeStampedModel):
    """An animal's record. Its status is never stored: see `status`."""

    class Sex(models.TextChoices):
        FEMALE = "female", "Hembra"
        MALE = "male", "Macho"
        UNKNOWN = "unknown", "Desconocido"

    class Size(models.TextChoices):
        SMALL = "small", "Pequeño"
        MEDIUM = "medium", "Mediano"
        LARGE = "large", "Grande"

    class Status(models.TextChoices):
        DECEASED = "deceased", "Falleció"
        TRANSFERRED = "transferred", "Trasladado"
        ADOPTED = "adopted", "Adoptado"
        FOSTER = "foster", "En casa de acogida"
        TREATMENT = "treatment", "En tratamiento"
        AVAILABLE = "available", "Disponible"

    slug = models.SlugField("dirección", max_length=80, unique=True, help_text="Se guarda para que los enlaces compartidos no cambien.")
    name = models.CharField("nombre", max_length=60)
    species = models.ForeignKey(Species, on_delete=models.PROTECT, related_name="animals", verbose_name="especie")
    sex = models.CharField("sexo", max_length=10, choices=Sex.choices, default=Sex.UNKNOWN)
    size = models.CharField("tamaño", max_length=10, choices=Size.choices, default=Size.MEDIUM)
    birth_date_approx = models.DateField("fecha de nacimiento aproximada")
    in_treatment = models.BooleanField("en tratamiento", default=False)
    foster_home = models.ForeignKey(
        "people.TeamMember", on_delete=models.PROTECT, null=True, blank=True, related_name="fostered_animals",
        verbose_name="casa de acogida",
    )
    quote = models.CharField("frase destacada", max_length=160, blank=True)
    story = models.TextField("historia", blank=True)
    vaccinated = models.BooleanField("vacunas al día", default=False)
    sterilized = models.BooleanField("esterilizado", default=False)
    microchip_number = models.CharField("número de microchip", max_length=20, blank=True)
    intake_date = models.DateField("llegó a la fundación el")
    sponsorship_amount = models.PositiveIntegerField("padrinazgo mensual (CLP)", default=0)
    traits = models.ManyToManyField(Trait, through="AnimalTrait", blank=True, verbose_name="rasgos")

    class Meta:
        verbose_name = "animal"
        verbose_name_plural = "animales"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["microchip_number"], condition=~Q(microchip_number=""), name="animal_microchip_unique"
            ),
            models.CheckConstraint(condition=Q(intake_date__gte=models.F("birth_date_approx")), name="animal_intake_after_birth"),
        ]

    def __str__(self):
        return self.name

    @property
    def age_months(self):
        from datetime import date

        today = date.today()
        months = (today.year - self.birth_date_approx.year) * 12 + today.month - self.birth_date_approx.month
        return max(0, months - (today.day < self.birth_date_approx.day))

    @property
    def life_stage(self):
        """The species' stage whose start is the latest one not after the animal's age."""
        stages = [s for s in self.species.life_stages.all() if s.from_months <= self.age_months]
        return max(stages, key=lambda s: s.from_months, default=None)

    @property
    def status(self):
        """Derived in priority order: an exit, a signed adoption, a foster home, treatment, otherwise available."""
        if hasattr(self, "exit"):
            return self.Status.DECEASED if self.exit.kind == AnimalExit.Kind.DECEASED else self.Status.TRANSFERRED
        if self.adoptions.filter(status="signed").exists():
            return self.Status.ADOPTED
        if self.foster_home_id:
            return self.Status.FOSTER
        if self.in_treatment:
            return self.Status.TREATMENT
        return self.Status.AVAILABLE


class AnimalTrait(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    trait = models.ForeignKey(Trait, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "rasgo del animal"
        verbose_name_plural = "rasgos del animal"
        constraints = [models.UniqueConstraint(fields=["animal", "trait"], name="animal_trait_unique")]


class AnimalPhoto(TimeStampedModel):
    """The database stores only the relative path; the file lives on the organization's server."""

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="photos", verbose_name="animal")
    image = models.ImageField("foto", upload_to="animals/%Y/%m/")
    position = models.PositiveSmallIntegerField("orden", default=0, help_text="La de menor orden es la foto principal.")

    class Meta:
        verbose_name = "foto"
        verbose_name_plural = "fotos"
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["animal", "position"], name="animal_photo_position_unique")]

    def __str__(self):
        return f"{self.animal} #{self.position}"


class AnimalDailyViews(TimeStampedModel):
    """Visits to an animal's page per day. Stores no data about who visited."""

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="daily_views")
    day = models.DateField("día")
    views = models.PositiveIntegerField("visitas", default=0)

    class Meta:
        verbose_name = "visitas del día"
        verbose_name_plural = "visitas por día"
        constraints = [models.UniqueConstraint(fields=["animal", "day"], name="animal_daily_views_unique")]


class AnimalExit(TimeStampedModel):
    """An exit that is not an adoption. At most one per animal."""

    class Kind(models.TextChoices):
        DECEASED = "deceased", "Falleció"
        TRANSFERRED = "transferred", "Trasladado a otra organización"

    animal = models.OneToOneField(Animal, on_delete=models.PROTECT, related_name="exit", verbose_name="animal")
    kind = models.CharField("motivo", max_length=16, choices=Kind.choices)
    exit_date = models.DateField("fecha")
    notes = models.TextField("nota", blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", verbose_name="registrado por"
    )

    class Meta:
        verbose_name = "salida"
        verbose_name_plural = "salidas"

    def __str__(self):
        return f"{self.animal} · {self.get_kind_display()}"
