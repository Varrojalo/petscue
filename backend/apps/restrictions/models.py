from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Restriction(TimeStampedModel):
    """People who may not adopt, kept by each organization. Never deleted: lifted, so the history remains."""

    class Reason(models.TextChoices):
        ABUSE = "abuse", "Maltrato"
        ABANDONMENT = "abandonment", "Abandono"
        REPEATED_RETURNS = "repeated_returns", "Devolución reiterada"
        FALSE_INFORMATION = "false_information", "Datos falsos en la solicitud"
        OTHER = "other", "Otro"

    person = models.ForeignKey("people.Person", on_delete=models.PROTECT, related_name="restrictions", verbose_name="persona")
    species = models.ForeignKey(
        "animals.Species", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name="especie", help_text="Vacío = aplica a todas las especies.",
    )
    reason = models.CharField("motivo", max_length=20, choices=Reason.choices)
    notes = models.TextField("notas")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", verbose_name="registrada por")
    lifted_at = models.DateTimeField("levantada el", null=True, blank=True)
    lifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+", verbose_name="levantada por"
    )

    class Meta:
        verbose_name = "restricción"
        verbose_name_plural = "restricciones"
        constraints = [
            # A person has at most one active restriction per species, and at most one general one (species NULL).
            models.UniqueConstraint(
                fields=["person", "species"], condition=Q(lifted_at__isnull=True), nulls_distinct=False,
                name="restriction_one_active_per_species",
            ),
            models.CheckConstraint(
                condition=Q(lifted_at__isnull=True, lifted_by__isnull=True) | Q(lifted_at__isnull=False, lifted_by__isnull=False),
                name="restriction_lifted_consistent",
            ),
        ]

    def __str__(self):
        return f"{self.person} · {self.get_reason_display()}"

    def applies_to(self, species):
        return self.lifted_at is None and (self.species_id is None or self.species_id == species.id)
