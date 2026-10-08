"""Pieces shared by every app's API: access rules, Spanish error messages, pagination and upload checks."""

from functools import wraps
from pathlib import Path
from typing import Annotated

from django.core.exceptions import ValidationError as DjangoValidationError
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination
from ninja.security import SessionAuth
from PIL import Image
from pydantic import AfterValidator


class TeamAuth(SessionAuth):
    """Any active panel account: volunteers, staff and administration."""

    def authenticate(self, request, key):
        user = request.user
        return user if user.is_authenticated and user.is_active else None


team_auth = TeamAuth()


def admin_only(view):
    """Endpoints that only the administration role may use."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.auth.is_admin:
            raise HttpError(403, "Solo la administración puede hacer esto.")
        return view(request, *args, **kwargs)

    return wrapper


def _email(value):
    from django.core.validators import validate_email

    value = value.strip().lower()
    try:
        validate_email(value)
    except DjangoValidationError:
        raise ValueError("Escribe un correo válido, por ejemplo nombre@correo.cl.") from None
    return value


# Email checked with Django's own validator (no extra dependency), stored in lowercase.
Email = Annotated[str, AfterValidator(_email)]


class Page20(PageNumberPagination):
    page_size = 20


class Mapped:
    """Lets pagination slice the queryset first and serialize only the page it returns."""

    def __init__(self, queryset, serialize):
        self.queryset, self.serialize = queryset, serialize

    def __len__(self):
        return self.queryset.count()

    def __getitem__(self, page):
        return [self.serialize(obj) for obj in self.queryset[page]]


def bad_request(message):
    return HttpError(400, message)


def conflict(message):
    return HttpError(409, message)


# ---------- Spanish messages for request validation ----------

_MESSAGES = {
    "missing": "Este dato es obligatorio.",
    "string_type": "Debe ser un texto.",
    "int_parsing": "Debe ser un número entero.",
    "int_type": "Debe ser un número entero.",
    "int_from_float": "Debe ser un número entero.",
    "bool_parsing": "Debe ser sí o no.",
    "bool_type": "Debe ser sí o no.",
    "date_parsing": "Fecha no válida. Usa el formato AAAA-MM-DD.",
    "date_from_datetime_parsing": "Fecha no válida. Usa el formato AAAA-MM-DD.",
    "date_type": "Fecha no válida. Usa el formato AAAA-MM-DD.",
    "list_type": "Debe ser una lista.",
    "value_error": None,
}


def translate_validation_error(error):
    kind, ctx = error.get("type", ""), error.get("ctx", {})
    if kind == "string_too_long":
        return f"Puede tener como máximo {ctx.get('max_length')} caracteres."
    if kind == "string_too_short":
        return "Este dato es obligatorio." if ctx.get("min_length") == 1 else f"Debe tener al menos {ctx.get('min_length')} caracteres."
    if kind in {"greater_than_equal", "greater_than"}:
        return f"Debe ser mayor{' o igual' if kind == 'greater_than_equal' else ''} a {ctx.get('ge', ctx.get('gt'))}."
    if kind in {"less_than_equal", "less_than"}:
        return f"Debe ser menor{' o igual' if kind == 'less_than_equal' else ''} a {ctx.get('le', ctx.get('lt'))}."
    if kind in {"literal_error", "enum"}:
        return f"Valor no permitido. Opciones: {ctx.get('expected', '')}."
    if kind == "value_error":
        return str(error.get("msg", "")).removeprefix("Value error, ")
    return _MESSAGES.get(kind) or "Dato no válido."


def validation_errors_payload(errors):
    out = []
    for error in errors:
        loc = [str(part) for part in error.get("loc", []) if part not in {"body", "query", "path", "form", "file", "payload", "data"}]
        out.append({"field": ".".join(loc), "message": translate_validation_error(error)})
    return {"detail": "Revisa los datos enviados.", "errors": out}


def django_validation_payload(exc: DjangoValidationError):
    if hasattr(exc, "message_dict"):
        errors = [{"field": f if f != "__all__" else "", "message": m} for f, msgs in exc.message_dict.items() for m in msgs]
    else:
        errors = [{"field": "", "message": m} for m in exc.messages]
    return {"detail": errors[0]["message"] if len(errors) == 1 else "Revisa los datos enviados.", "errors": errors}


# ---------- Uploads ----------

IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
FONT_EXTENSIONS = {".woff2", ".woff", ".ttf", ".otf"}


def check_size(upload):
    from apps.organization.models import OrganizationSettings

    limit = OrganizationSettings.load().max_upload_mb
    if upload.size > limit * 1024 * 1024:
        raise bad_request(f"El archivo pesa más de {limit} MB, el máximo que permite la fundación.")


def check_image(upload):
    check_size(upload)
    try:
        with Image.open(upload) as img:
            fmt = img.format
            img.verify()
    except Exception:
        raise bad_request("El archivo no es una imagen válida.") from None
    finally:
        upload.seek(0)
    if fmt not in IMAGE_FORMATS:
        raise bad_request("Solo se aceptan imágenes JPG, PNG o WEBP.")


def check_font(upload):
    check_size(upload)
    if Path(upload.name).suffix.lower() not in FONT_EXTENSIONS:
        raise bad_request("Solo se aceptan tipografías .woff2, .woff, .ttf u .otf.")
