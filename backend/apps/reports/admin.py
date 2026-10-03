from django.contrib import admin

from .models import StreetReport


@admin.register(StreetReport)
class StreetReportAdmin(admin.ModelAdmin):
    list_display = ["code", "address", "status", "created_at"]
    list_filter = ["status"]
