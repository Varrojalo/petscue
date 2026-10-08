"""Read-only Excel copy of the organization's data: one sheet per kind of record."""

from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook

from apps.adoptions.models import Adoption
from apps.animals.models import Animal
from apps.core import rut
from apps.people.models import Membership, Person, TeamMember
from apps.reports.models import StreetReport
from apps.restrictions.models import Restriction


def _local(moment):
    """Excel has no time zones: write the organization's local time."""
    return timezone.localtime(moment).replace(tzinfo=None) if moment else None


def _sheets():
    yield "Animales", ["Nombre", "Especie", "Sexo", "Tamaño", "Nacimiento aprox.", "Llegada", "Estado", "Microchip", "Padrinazgo (CLP)"], (
        [a.name, a.species.name, a.get_sex_display(), a.get_size_display(), a.birth_date_approx, a.intake_date,
         a.Status(a.status).label, a.microchip_number, a.sponsorship_amount]
        for a in Animal.objects.select_related("species", "exit").prefetch_related("adoptions")
    )
    yield "Adopciones", ["Animal", "Adoptante", "RUT", "Origen", "Estado", "Contrato", "Aporte (CLP)", "Descuento (CLP)", "Devolución", "Motivo devolución"], (
        [a.animal.name, a.person.full_name, rut.display(a.person.document_number), a.get_source_display(), a.get_status_display(),
         a.contract_signed_at, a.fee_charged, a.discount, a.returned_at, a.return_reason]
        for a in Adoption.objects.select_related("animal", "person")
    )
    yield "Personas", ["RUT", "Nombres", "Primer apellido", "Segundo apellido", "Teléfono", "Correo", "Comuna"], (
        [rut.display(p.document_number), p.first_names, p.paternal_surname, p.maternal_surname, p.phone, p.email, p.locality.name if p.locality_id else ""]
        for p in Person.objects.select_related("locality")
    )
    yield "Socios", ["RUT", "Persona", "Tipo", "Animal", "Monto mensual (CLP)", "Estado", "Desde", "Hasta"], (
        [rut.display(m.person.document_number), m.person.full_name, m.get_kind_display(), m.animal.name if m.animal_id else "",
         m.monthly_amount, m.get_status_display(), m.started_at, m.ended_at]
        for m in Membership.objects.select_related("person", "animal")
    )
    yield "Equipo", ["RUT", "Persona", "Tipo", "Estado", "Casa de acogida", "Desde", "Hasta"], (
        [rut.display(t.person.document_number), t.person.full_name, t.get_kind_display(), t.get_status_display(),
         "Sí" if t.is_foster_home else "No", t.joined_at, t.left_at]
        for t in TeamMember.objects.select_related("person")
    )
    yield "Restricciones", ["RUT", "Persona", "Motivo", "Especie", "Notas", "Registrada", "Levantada"], (
        [rut.display(r.person.document_number), r.person.full_name, r.get_reason_display(),
         r.species.plural_name if r.species_id else "Todas", r.notes, _local(r.created_at), _local(r.lifted_at)]
        for r in Restriction.objects.select_related("person", "species")
    )
    yield "Avisos", ["Número", "Lugar", "Detalles", "Teléfono", "Estado", "Recibido"], (
        [s.code, s.address, s.notes, s.contact_phone, s.get_status_display(), _local(s.created_at)]
        for s in StreetReport.objects.all()
    )


def build():
    book = Workbook(write_only=True)
    for title, header, rows in _sheets():
        sheet = book.create_sheet(title)
        sheet.append(header)
        for row in rows:
            sheet.append(row)
    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()
