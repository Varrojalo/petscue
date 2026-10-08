from django.db import migrations

# Dogs and cats come preloaded with suggested age stages (start of each stage, in months).
# Each organization can rename them, change the ages, hide a species or add others.
DEFAULT_SPECIES = [
    ("Perro", "Perros", 0, [("Cachorro", 0), ("Joven", 12), ("Adulto", 24), ("Mayor", 96)]),
    ("Gato", "Gatos", 1, [("Gatito", 0), ("Joven", 12), ("Adulto", 24), ("Mayor", 132)]),
]


def load(apps, schema_editor):
    Species = apps.get_model("animals", "Species")
    LifeStage = apps.get_model("animals", "LifeStage")
    for name, plural, position, stages in DEFAULT_SPECIES:
        species, created = Species.objects.get_or_create(name=name, defaults={"plural_name": plural, "position": position})
        if created:
            LifeStage.objects.bulk_create(LifeStage(species=species, name=n, from_months=m) for n, m in stages)


def unload(apps, schema_editor):
    Species = apps.get_model("animals", "Species")
    Species.objects.filter(name__in=[s[0] for s in DEFAULT_SPECIES], animals__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("animals", "0003_lifestage")]

    operations = [migrations.RunPython(load, unload)]
