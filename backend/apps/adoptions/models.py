from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Adoption(TimeStampedModel):
    """The whole adoption cycle in one row: request, interview, contract and a possible return."""

    class Source(models.TextChoices):
        WEB = "web", "Formulario web"
        IMPORT = "import", "Importación desde Excel"

    class Status(models.TextChoices):
        NEW = "new", "Nueva"
        INTERVIEW = "interview", "Entrevista"
        SIGNED = "signed", "Contrato firmado"
        RETURNED = "returned", "Devuelto"
        REJECTED = "rejected", "Rechazada"

    class Housing(models.TextChoices):
        APARTMENT = "apartment", "Departamento"
        HOUSE = "house", "Casa"
        HOUSE_WITH_YARD = "house_with_yard", "Casa con patio"

    animal = models.ForeignKey("animals.Animal", on_delete=models.PROTECT, related_name="adoptions", verbose_name="animal")
    person = models.ForeignKey("people.Person", on_delete=models.PROTECT, related_name="adoptions", verbose_name="adoptante")
    source = models.CharField("origen", max_length=8, choices=Source.choices, default=Source.WEB)
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.NEW)
    housing = models.CharField("vivienda", max_length=16, choices=Housing.choices, blank=True)
    has_other_pets = models.BooleanField("tiene otros animales", null=True, blank=True)
    message = models.TextField("mensaje", blank=True)
    foster_notified_at = models.DateTimeField("casa de acogida avisada el", null=True, blank=True)
    contract_signed_at = models.DateField("contrato firmado el", null=True, blank=True)
    fee_charged = models.PositiveIntegerField("aporte cobrado (CLP)", null=True, blank=True)
    discount = models.PositiveIntegerField("descuento (CLP)", null=True, blank=True)
    returned_at = models.DateField("devuelto el", null=True, blank=True)
    return_reason = models.TextField("motivo de la devolución", blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="revisado por"
    )
    reviewed_at = models.DateTimeField("revisado el", null=True, blank=True)

    class Meta:
        verbose_name = "adopción"
        verbose_name_plural = "adopciones"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["animal"], condition=Q(status="signed"), name="adoption_one_active_per_animal"),
            models.CheckConstraint(
                condition=~Q(status__in=["signed", "returned"])
                | Q(contract_signed_at__isnull=False, fee_charged__isnull=False),
                name="adoption_contract_data_when_signed",
            ),
            models.CheckConstraint(
                condition=Q(status="returned", returned_at__isnull=False) | (~Q(status="returned") & Q(returned_at__isnull=True)),
                name="adoption_returned_at_iff_returned",
            ),
            models.CheckConstraint(
                condition=Q(source="import") | (~Q(housing="") & Q(has_other_pets__isnull=False)),
                name="adoption_web_has_housing_data",
            ),
            models.CheckConstraint(
                condition=Q(returned_at__isnull=True) | Q(returned_at__gte=models.F("contract_signed_at")),
                name="adoption_return_after_contract",
            ),
        ]

    def __str__(self):
        return f"{self.person} → {self.animal} ({self.get_status_display()})"
