from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from ninja import File, Router, Schema
from ninja.files import UploadedFile
from ninja.pagination import paginate

from apps.core.api import Mapped, Page20, admin_only, check_size, team_auth

from . import excel, imports
from .models import BackupRun, ImportBatch

dashboard_router = Router(tags=["panel: respaldos"], auth=team_auth)

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class BackupOut(Schema):
    id: int
    kind: str
    format: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    file_name: str
    size_bytes: int | None
    requested_by: str | None


def out(b):
    return {
        "id": b.id, "kind": b.get_kind_display(), "format": b.get_format_display(), "status": b.get_status_display(),
        "started_at": b.started_at, "finished_at": b.finished_at, "file_name": b.file_name, "size_bytes": b.size_bytes,
        "requested_by": b.requested_by.person.full_name if b.requested_by_id else None,
    }


@dashboard_router.get("/backups", response=list[BackupOut])
@admin_only
@paginate(Page20)
def list_backups(request):
    return Mapped(BackupRun.objects.select_related("requested_by__person"), out)


@dashboard_router.get("/backups/excel")
@admin_only
def download_excel(request):
    """Read-only copy of all the data in one Excel file. Changes made to the file do not come back to the platform."""
    started = timezone.now()
    content = excel.build()
    name = f"petscue-respaldo-{started:%Y-%m-%d}.xlsx"
    BackupRun.objects.create(
        kind=BackupRun.Kind.MANUAL, format=BackupRun.Format.EXCEL, status=BackupRun.Status.OK, started_at=started,
        finished_at=timezone.now(), file_name=name, size_bytes=len(content), requested_by=request.auth,
    )
    response = HttpResponse(content, content_type=XLSX)
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


# ---------- Excel imports (administration) ----------

class PreviewRow(Schema):
    row: int
    values: list[str]
    errors: list[str]


class PreviewOut(Schema):
    valid: bool
    detail: str
    missing_columns: list[str]
    extra_columns: list[str]
    rows: list[PreviewRow]


class ImportOut(Schema):
    id: int
    kind: str
    file_name: str
    row_count: int
    created_by: str
    created_at: datetime


def import_out(batch):
    return {
        "id": batch.id, "kind": batch.get_kind_display(), "file_name": batch.file_name, "row_count": batch.row_count,
        "created_by": batch.created_by.person.full_name, "created_at": batch.created_at,
    }


@dashboard_router.get("/imports", response=list[ImportOut])
@admin_only
@paginate(Page20)
def list_imports(request):
    return Mapped(ImportBatch.objects.select_related("created_by__person"), import_out)


@dashboard_router.get("/imports/{kind}/template")
@admin_only
def download_template(request, kind: ImportBatch.Kind):
    """Excel template with the exact columns, plus a sheet explaining how to fill each one."""
    response = HttpResponse(imports.template(kind), content_type=XLSX)
    response["Content-Disposition"] = f'attachment; filename="plantilla-{kind}.xlsx"'
    return response


@dashboard_router.post("/imports/{kind}/preview", response=PreviewOut)
@admin_only
def preview_import(request, kind: ImportBatch.Kind, file: File[UploadedFile]):
    """Checks every row without saving anything."""
    check_size(file)
    result = imports.validate(kind, file)
    result.pop("_parsed", None)
    return result


@dashboard_router.post("/imports/{kind}/confirm", response={201: ImportOut, 400: PreviewOut})
@admin_only
def confirm_import(request, kind: ImportBatch.Kind, file: File[UploadedFile]):
    """Validates again and saves everything in one transaction, or nothing if any row has errors."""
    check_size(file)
    batch, result = imports.run(kind, file, request.auth)
    if batch is None:
        return 400, result
    return 201, import_out(batch)
