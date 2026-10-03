from ninja import NinjaAPI

api = NinjaAPI(title="Petscue API", version="0.1.0")


@api.get("/health", tags=["sistema"])
def health(request):
    """Lets Docker and monitoring tools check that the backend is up."""
    return {"status": "ok"}
