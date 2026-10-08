from datetime import datetime

from django.shortcuts import get_object_or_404
from ninja import Field, File, Form, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.pagination import paginate

from apps.core.api import Mapped, Page20, bad_request, check_image, team_auth
from apps.organization.models import OrganizationSettings

from .models import StreetReport

public_router = Router(tags=["web pública: avisos de la calle"])
dashboard_router = Router(tags=["panel: avisos de la calle"], auth=team_auth)


class ReportIn(Schema):
    address: str = Field(min_length=1, max_length=200)
    notes: str = Field("", max_length=2000)
    contact_phone: str = Field("", max_length=20)


class ReportOut(Schema):
    id: int
    code: str
    address: str
    notes: str
    contact_phone: str
    photo_url: str | None
    status: str
    handled_by: str | None
    created_at: datetime


def out(r):
    return {
        "id": r.id, "code": r.code, "address": r.address, "notes": r.notes, "contact_phone": r.contact_phone,
        "photo_url": r.photo.url if r.photo else None, "status": r.get_status_display(),
        "handled_by": r.handled_by.person.full_name if r.handled_by_id else None, "created_at": r.created_at,
    }


@public_router.post("/street-reports", response={201: dict})
def create_report(request, data: Form[ReportIn], photo: File[UploadedFile] = None):
    """A stray animal reported from the website, only while the organization has the feature on."""
    if not OrganizationSettings.load().street_reports_enabled:
        raise HttpError(404, "La fundación no recibe avisos por la web.")
    if photo:
        check_image(photo)
    report = StreetReport.objects.create(photo=photo, **data.dict())
    return 201, {"detail": f"Recibimos tu aviso. Tu número de aviso es {report.code}.", "code": report.code}


@dashboard_router.get("/street-reports", response=list[ReportOut])
@paginate(Page20)
def list_reports(request, status: StreetReport.Status | None = None):
    qs = StreetReport.objects.select_related("handled_by__person")
    if status:
        qs = qs.filter(status=status)
    return Mapped(qs, out)


@dashboard_router.post("/street-reports/{report_id}/handle", response=ReportOut)
def handle(request, report_id: int):
    report = get_object_or_404(StreetReport, pk=report_id)
    if report.status == StreetReport.Status.HANDLED:
        raise bad_request("Este aviso ya fue atendido.")
    report.status, report.handled_by = StreetReport.Status.HANDLED, request.auth
    report.save(update_fields=["status", "handled_by", "updated_at"])
    return out(report)
