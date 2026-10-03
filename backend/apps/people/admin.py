from django.contrib import admin

from apps.core import rut

from .forms import EmailAdminAuthenticationForm
from .models import AvailabilityOption, Membership, Person, TeamMember, TeamMemberAvailability, User

admin.site.site_header = "Petscue"
admin.site.site_title = "Petscue"
admin.site.index_title = "Administración de datos"
admin.site.login_form = EmailAdminAuthenticationForm


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["full_name", "rut", "email", "phone", "locality"]
    search_fields = ["document_number", "first_names", "paternal_surname", "maternal_surname", "email"]
    list_select_related = ["locality"]

    @admin.display(description="RUT", ordering="document_number")
    def rut(self, obj):
        return rut.display(obj.document_number)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["person", "role", "is_active", "last_login"]
    list_filter = ["role", "is_active"]
    search_fields = ["person__first_names", "person__paternal_surname", "person__email"]
    readonly_fields = ["last_login", "deactivated_at", "deactivated_by"]
    exclude = ["password"]
    autocomplete_fields = ["person"]


class TeamMemberAvailabilityInline(admin.TabularInline):
    model = TeamMemberAvailability
    extra = 0


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["person", "kind", "status", "is_foster_home", "joined_at", "left_at"]
    list_filter = ["kind", "status", "is_foster_home"]
    search_fields = ["person__first_names", "person__paternal_surname", "person__document_number"]
    autocomplete_fields = ["person"]
    inlines = [TeamMemberAvailabilityInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["person", "kind", "monthly_amount", "animal", "status", "started_at", "ended_at"]
    list_filter = ["kind", "status"]
    search_fields = ["person__first_names", "person__paternal_surname", "person__document_number"]
    autocomplete_fields = ["person", "animal"]


admin.site.register(AvailabilityOption)
