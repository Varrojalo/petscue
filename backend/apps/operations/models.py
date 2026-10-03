from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ImportBatch(TimeStampedModel):
    """An Excel import. Only recorded when the whole file passed validation: all rows go in, or none do."""

    class Kind(models.TextChoices):
        ANIMALS = "animals", "Animales en la fundación"
        ADOPTIONS = "adoptions", "Adopciones anteriores"
        PEOPLE = "people", "Socios y equipo"
        RESTRICTIONS = "restrictions", "Lista de restricciones"

    kind = models.CharField("tipo", max_length=16, choices=Kind.choices)
    file_name = models.CharField("archivo", max_length=200)
    row_count = models.PositiveIntegerField("filas importadas")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", verbose_name="importado por")

    class Meta:
        verbose_name = "importación"
        verbose_name_plural = "importaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.file_name}"


class BackupRun(TimeStampedModel):
    class Kind(models.TextChoices):
        AUTO = "auto", "Automático"
        MANUAL = "manual", "Manual"

    class Format(models.TextChoices):
        DATABASE = "database", "Base de datos (restaurable)"
        EXCEL = "excel", "Excel (solo lectura)"

    class Status(models.TextChoices):
        OK = "ok", "Correcto"
        FAILED = "failed", "Falló"

    kind = models.CharField("tipo", max_length=8, choices=Kind.choices)
    format = models.CharField("formato", max_length=8, choices=Format.choices)
    status = models.CharField("estado", max_length=8, choices=Status.choices)
    started_at = models.DateTimeField("inicio")
    finished_at = models.DateTimeField("término", null=True, blank=True)
    file_name = models.CharField("archivo", max_length=200)
    size_bytes = models.PositiveBigIntegerField("tamaño (bytes)", null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
        verbose_name="solicitado por", help_text="Vacío en los respaldos automáticos.",
    )

    class Meta:
        verbose_name = "respaldo"
        verbose_name_plural = "respaldos"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.started_at:%Y-%m-%d %H:%M}"
