from django.contrib import admin

from .models import Animal, AnimalDailyViews, AnimalExit, AnimalPhoto, AnimalTrait, Species, Trait


class AnimalPhotoInline(admin.TabularInline):
    model = AnimalPhoto
    extra = 0


class AnimalTraitInline(admin.TabularInline):
    model = AnimalTrait
    extra = 0


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ["name", "species", "status_label", "intake_date", "foster_home", "in_treatment"]
    list_filter = ["species", "in_treatment", "sex", "size"]
    search_fields = ["name", "microchip_number"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["foster_home"]
    inlines = [AnimalPhotoInline, AnimalTraitInline]

    @admin.display(description="estado")
    def status_label(self, obj):
        return obj.Status(obj.status).label


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ["name", "plural_name", "is_active", "position"]
    list_editable = ["is_active", "position"]


@admin.register(AnimalExit)
class AnimalExitAdmin(admin.ModelAdmin):
    list_display = ["animal", "kind", "exit_date", "recorded_by"]
    list_filter = ["kind"]
    autocomplete_fields = ["animal"]


@admin.register(AnimalDailyViews)
class AnimalDailyViewsAdmin(admin.ModelAdmin):
    list_display = ["animal", "day", "views"]
    list_filter = ["day"]


admin.site.register(Trait)
