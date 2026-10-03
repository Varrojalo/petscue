from django.contrib import admin

from .models import Adoption


@admin.register(Adoption)
class AdoptionAdmin(admin.ModelAdmin):
    list_display = ["animal", "person", "status", "source", "contract_signed_at", "returned_at", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["animal__name", "person__first_names", "person__paternal_surname", "person__document_number"]
    autocomplete_fields = ["animal", "person"]
