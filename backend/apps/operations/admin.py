from django.contrib import admin

from .models import BackupRun, ImportBatch


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ["kind", "file_name", "row_count", "created_by", "created_at"]
    list_filter = ["kind"]


@admin.register(BackupRun)
class BackupRunAdmin(admin.ModelAdmin):
    list_display = ["started_at", "kind", "format", "status", "size_bytes"]
    list_filter = ["kind", "format", "status"]
