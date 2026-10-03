from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class StreetReport(TimeStampedModel):
    """A stray animal reported from the website (feature under evaluation)."""

    class Status(models.TextChoices):
        NEW = "new", "Nuevo"
        HANDLED = "handled", "Atendido"

    photo = models.ImageField("foto", upload_to="reports/%Y/%m/", blank=True)
    address = models.CharField("lugar", max_length=200)
    notes = models.TextField("detalles", blank=True)
    contact_phone = models.CharField("teléfono de contacto", max_length=20, blank=True)
    status = models.CharField("estado", max_length=8, choices=Status.choices, default=Status.NEW)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="atendido por"
    )

    class Meta:
        verbose_name = "aviso de la calle"
        verbose_name_plural = "avisos de la calle"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    @property
    def code(self):
        """Reference number shown to the person who reported, derived from the id: 31 -> AV-0031."""
        return f"AV-{self.pk:04d}" if self.pk else "AV-nuevo"
