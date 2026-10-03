from django.contrib import admin

from .models import Restriction


@admin.register(Restriction)
class RestrictionAdmin(admin.ModelAdmin):
    list_display = ["person", "reason", "species", "created_at", "lifted_at"]
    list_filter = ["reason", "species"]
    search_fields = ["person__document_number", "person__first_names", "person__paternal_surname"]
    autocomplete_fields = ["person"]
