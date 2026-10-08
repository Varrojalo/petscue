from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from ninja import NinjaAPI, Router
from ninja.errors import AuthenticationError, ValidationError

from apps.adoptions import api as adoptions
from apps.animals import api as animals
from apps.core.api import django_validation_payload, validation_errors_payload
from apps.operations import api as operations
from apps.organization import api as organization
from apps.people import api as people
from apps.reports import api as reports
from apps.restrictions import api as restrictions

api = NinjaAPI(title="Petscue API", version="0.1.0", description="API de la web pública y del panel interno de Petscue.")


@api.exception_handler(ValidationError)
def on_validation_error(request, exc):
    return api.create_response(request, validation_errors_payload(exc.errors), status=422)


@api.exception_handler(DjangoValidationError)
def on_django_validation_error(request, exc):
    return api.create_response(request, django_validation_payload(exc), status=400)


@api.exception_handler(AuthenticationError)
def on_authentication_error(request, exc):
    return api.create_response(request, {"detail": "Inicia sesión para continuar."}, status=401)


@api.exception_handler(Http404)
def on_not_found(request, exc):
    return api.create_response(request, {"detail": "No encontramos lo que buscas."}, status=404)


@api.get("/health", tags=["sistema"])
def health(request):
    """Lets Docker and monitoring tools check that the backend is up."""
    return {"status": "ok"}


# Website: anyone can use these, without signing in.
public = Router()
for router in (organization.public_router, animals.public_router, adoptions.public_router, people.public_router, reports.public_router):
    public.add_router("", router)

# Panel: every endpoint requires a signed-in team account; some also require the administration role.
dashboard = Router()
for router in (
    organization.dashboard_router, animals.dashboard_router, animals.catalog_router, adoptions.dashboard_router,
    people.dashboard_router, restrictions.dashboard_router, reports.dashboard_router, organization.settings_router,
    operations.dashboard_router,
):
    dashboard.add_router("", router)

api.add_router("/public", public)
api.add_router("/auth", people.auth_router)
api.add_router("/dashboard", dashboard)
