from django.db import migrations

# Official region codes of Chile. Communes will be loaded from the official SUBDERE list in a later migration.
REGIONS = [
    ("15", "Arica y Parinacota"),
    ("01", "Tarapacá"),
    ("02", "Antofagasta"),
    ("03", "Atacama"),
    ("04", "Coquimbo"),
    ("05", "Valparaíso"),
    ("13", "Metropolitana de Santiago"),
    ("06", "Libertador General Bernardo O'Higgins"),
    ("07", "Maule"),
    ("16", "Ñuble"),
    ("08", "Biobío"),
    ("09", "La Araucanía"),
    ("14", "Los Ríos"),
    ("10", "Los Lagos"),
    ("11", "Aysén del General Carlos Ibáñez del Campo"),
    ("12", "Magallanes y de la Antártica Chilena"),
]


def load(apps, schema_editor):
    Region = apps.get_model("organization", "Region")
    for code, name in REGIONS:
        Region.objects.update_or_create(code=code, defaults={"name": name})


def unload(apps, schema_editor):
    apps.get_model("organization", "Region").objects.filter(code__in=[c for c, _ in REGIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [("organization", "0002_initial")]

    operations = [migrations.RunPython(load, unload)]
