from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q

from apps.core import rut
from apps.core.models import TimeStampedModel


class ReviewStatus(models.TextChoices):
    """Shared by applications that start as a request: membership and team membership."""

    PENDING = "pending", "Pendiente"
    APPROVED = "approved", "Aprobada"
    REJECTED = "rejected", "Rechazada"


class Person(TimeStampedModel):
    """Anyone the organization deals with, identified once by their RUT."""

    document_number = models.CharField("RUT", max_length=20, unique=True, validators=[rut.validate])
    first_names = models.CharField("nombres", max_length=120)
    paternal_surname = models.CharField("primer apellido", max_length=80)
    maternal_surname = models.CharField("segundo apellido", max_length=80, blank=True)
    phone = models.CharField("teléfono", max_length=20, blank=True)
    # Nullable so that several people without email don't collide on the unique index.
    email = models.EmailField("correo", unique=True, null=True, blank=True)
    locality = models.ForeignKey(
        "organization.Locality", on_delete=models.PROTECT, null=True, blank=True, verbose_name="comuna"
    )
    data_consent_at = models.DateTimeField("aceptó el tratamiento de datos", null=True, blank=True)

    class Meta:
        verbose_name = "persona"
        verbose_name_plural = "personas"
        ordering = ["paternal_surname", "first_names"]
        constraints = [
            models.CheckConstraint(
                condition=Q(document_number__regex=rut.STORED_PATTERN), name="person_document_number_stored_form"
            ),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return " ".join(p for p in [self.first_names, self.paternal_surname, self.maternal_surname] if p)

    def clean(self):
        self.document_number = rut.normalize(self.document_number)
        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        """Login is by the person's email; this is what Django's auth backend calls."""
        return self.get(person__email__iexact=email)

    def create_user(self, person, password=None, role="worker"):
        if not person.email:
            raise ValueError("La persona necesita un correo para tener cuenta.")
        user = self.model(person=person, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, person, password=None):
        return self.create_user(person, password, role=User.Role.ADMIN)


class User(AbstractBaseUser, TimeStampedModel):
    """Panel account. Has no email of its own: it signs in with its person's email."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administración"
        WORKER = "worker", "Trabajador"

    person = models.OneToOneField(Person, on_delete=models.PROTECT, related_name="user", verbose_name="persona")
    role = models.CharField("rol", max_length=16, choices=Role.choices, default=Role.WORKER)
    is_active = models.BooleanField("acceso activo", default=True)
    deactivated_at = models.DateTimeField("acceso revocado el", null=True, blank=True)
    deactivated_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="revocado por"
    )

    objects = UserManager()

    USERNAME_FIELD = "person"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "cuenta"
        verbose_name_plural = "cuentas"
        constraints = [
            models.CheckConstraint(
                condition=Q(is_active=True, deactivated_at__isnull=True) | Q(is_active=False, deactivated_at__isnull=False),
                name="user_deactivation_consistent",
            ),
        ]

    def __str__(self):
        return f"{self.person} ({self.get_role_display()})"

    def get_username(self):
        return self.person.email

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    # Django admin needs these three; access follows the role, there are no per-model permissions.
    @property
    def is_staff(self):
        return self.is_active

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_admin

    def has_module_perms(self, app_label):
        return self.is_active and self.is_admin


class AvailabilityOption(TimeStampedModel):
    label = models.CharField("opción", max_length=60, unique=True)
    position = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "opción de disponibilidad"
        verbose_name_plural = "opciones de disponibilidad"
        ordering = ["position"]

    def __str__(self):
        return self.label


class TeamMember(TimeStampedModel):
    """Someone who gives their time: volunteer or staff. Starts as an application (pending)."""

    class Kind(models.TextChoices):
        VOLUNTEER = "volunteer", "Voluntario"
        STAFF = "staff", "Equipo de planta"

    person = models.OneToOneField(Person, on_delete=models.PROTECT, related_name="team_member", verbose_name="persona")
    kind = models.CharField("tipo", max_length=16, choices=Kind.choices, default=Kind.VOLUNTEER)
    status = models.CharField("estado", max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    is_foster_home = models.BooleanField("casa de acogida", default=False)
    joined_at = models.DateField("se unió el", null=True, blank=True)
    left_at = models.DateField("se fue el", null=True, blank=True)
    availability = models.ManyToManyField(
        AvailabilityOption, through="TeamMemberAvailability", blank=True, verbose_name="disponibilidad"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="revisado por"
    )
    reviewed_at = models.DateTimeField("revisado el", null=True, blank=True)

    class Meta:
        verbose_name = "integrante del equipo"
        verbose_name_plural = "equipo"
        constraints = [
            models.CheckConstraint(
                condition=Q(status=ReviewStatus.APPROVED, joined_at__isnull=False)
                | (~Q(status=ReviewStatus.APPROVED) & Q(joined_at__isnull=True, left_at__isnull=True)),
                name="team_member_dates_follow_status",
            ),
            models.CheckConstraint(
                condition=Q(is_foster_home=False) | Q(status=ReviewStatus.APPROVED),
                name="team_member_foster_home_only_if_approved",
            ),
        ]

    def __str__(self):
        return f"{self.person} · {self.get_kind_display()}"

    @property
    def is_active_member(self):
        return self.status == ReviewStatus.APPROVED and self.left_at is None


class TeamMemberAvailability(TimeStampedModel):
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    availability_option = models.ForeignKey(AvailabilityOption, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "disponibilidad"
        verbose_name_plural = "disponibilidades"
        constraints = [
            models.UniqueConstraint(fields=["team_member", "availability_option"], name="team_member_availability_unique"),
        ]


class Membership(TimeStampedModel):
    """Someone who gives resources: a monthly donation or the sponsorship of one animal. Starts as an application."""

    class Kind(models.TextChoices):
        DONATION = "donation", "Cuota a la fundación"
        SPONSORSHIP = "sponsorship", "Padrinazgo"

    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="memberships", verbose_name="persona")
    kind = models.CharField("tipo", max_length=16, choices=Kind.choices)
    monthly_amount = models.PositiveIntegerField("monto mensual acordado (CLP)")
    animal = models.ForeignKey(
        "animals.Animal", on_delete=models.PROTECT, null=True, blank=True, related_name="sponsorships", verbose_name="animal"
    )
    status = models.CharField("estado", max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    started_at = models.DateField("desde", null=True, blank=True)
    ended_at = models.DateField("hasta", null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="revisado por"
    )
    reviewed_at = models.DateTimeField("revisado el", null=True, blank=True)

    class Meta:
        verbose_name = "socio"
        verbose_name_plural = "socios"
        constraints = [
            models.CheckConstraint(
                condition=Q(kind="sponsorship", animal__isnull=False) | Q(kind="donation", animal__isnull=True),
                name="membership_sponsorship_has_animal",
            ),
            models.CheckConstraint(
                condition=Q(status=ReviewStatus.APPROVED, started_at__isnull=False)
                | (~Q(status=ReviewStatus.APPROVED) & Q(started_at__isnull=True, ended_at__isnull=True)),
                name="membership_dates_follow_status",
            ),
        ]

    def __str__(self):
        return f"{self.person} · {self.get_kind_display()}"
