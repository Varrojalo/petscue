from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from apps.core.models import TimeStampedModel

hex_color = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Usa un color hexadecimal, por ejemplo #2F7D5A.")


class Region(TimeStampedModel):
    code = models.CharField("código", max_length=4, unique=True)
    name = models.CharField("nombre", max_length=80)

    class Meta:
        verbose_name = "región"
        verbose_name_plural = "regiones"
        ordering = ["code"]

    def __str__(self):
        return self.name


class Locality(TimeStampedModel):
    """Comuna in Chile. Neutral name so other countries' local divisions can be added later."""

    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="localities", verbose_name="región")
    code = models.CharField("código", max_length=8, unique=True)
    name = models.CharField("nombre", max_length=80)

    class Meta:
        verbose_name = "comuna"
        verbose_name_plural = "comunas"
        ordering = ["name"]

    def __str__(self):
        return self.name


class OrganizationSettings(TimeStampedModel):
    """The organization's identity. There is always exactly one row (id = 1)."""

    name = models.CharField("nombre", max_length=120)
    street_address = models.CharField("calle y número", max_length=160, blank=True)
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT, null=True, blank=True, verbose_name="comuna")
    phone = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo", blank=True)
    logo = models.ImageField("logo", upload_to="organization/", blank=True)
    brand_color = models.CharField("color principal", max_length=7, default="#2F7D5A", validators=[hex_color])
    accent_color = models.CharField("color de acento", max_length=7, default="#F2C94C", validators=[hex_color])
    title_font = models.FileField("tipografía de títulos", upload_to="organization/fonts/", blank=True)
    adoption_fee = models.PositiveIntegerField("aporte de adopción (CLP)", default=0)
    featured_animal = models.ForeignKey(
        "animals.Animal", on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="animal destacado"
    )
    backup_retention_days = models.PositiveSmallIntegerField(
        "días que se guardan los respaldos", default=30, validators=[MinValueValidator(1), MaxValueValidator(365)]
    )
    street_reports_enabled = models.BooleanField("avisos de la calle activos", default=False)
    max_upload_mb = models.PositiveSmallIntegerField(
        "tamaño máximo por archivo (MB)", default=10, validators=[MinValueValidator(1)],
        help_text="Archivos más grandes ocupan más espacio en el servidor y hacen más pesados los respaldos.",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="actualizado por"
    )

    class Meta:
        verbose_name = "configuración de la fundación"
        verbose_name_plural = "configuración de la fundación"
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="organization_settings_single_row"),
            models.CheckConstraint(
                condition=models.Q(backup_retention_days__gte=1, backup_retention_days__lte=365),
                name="organization_settings_retention_range",
            ),
            models.CheckConstraint(condition=models.Q(max_upload_mb__gte=1), name="organization_settings_max_upload_positive"),
            models.CheckConstraint(
                condition=models.Q(brand_color__regex=r"^#[0-9A-Fa-f]{6}$", accent_color__regex=r"^#[0-9A-Fa-f]{6}$"),
                name="organization_settings_hex_colors",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        if self._state.adding:
            # Saving a fresh instance over the existing row must keep that row's creation date.
            existing = type(self).objects.filter(pk=1).values_list("created_at", flat=True).first()
            if existing:
                self.created_at = existing
                self._state.adding = False
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"name": "Mi fundación"})
        return obj


class SocialLink(TimeStampedModel):
    class Network(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        TIKTOK = "tiktok", "TikTok"
        YOUTUBE = "youtube", "YouTube"
        X = "x", "X"
        OTHER = "other", "Otra"

    network = models.CharField("red", max_length=16, choices=Network.choices)
    handle = models.CharField("usuario o dirección", max_length=200)
    position = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "red social"
        verbose_name_plural = "redes sociales"
        ordering = ["position"]

    def __str__(self):
        return f"{self.get_network_display()}: {self.handle}"


class MembershipTier(TimeStampedModel):
    """Suggested monthly amounts shown on the membership form."""

    monthly_amount = models.PositiveIntegerField("cuota mensual (CLP)")
    position = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "cuota sugerida"
        verbose_name_plural = "cuotas sugeridas"
        ordering = ["position"]

    def __str__(self):
        from apps.core.formatting import money

        return money(self.monthly_amount)
