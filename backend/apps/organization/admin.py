from django.contrib import admin

from .models import Locality, MembershipTier, OrganizationSettings, Region, SocialLink


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not OrganizationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ["name", "region", "code"]
    list_filter = ["region"]
    search_fields = ["name"]


admin.site.register(Region)
admin.site.register(SocialLink)
admin.site.register(MembershipTier)
