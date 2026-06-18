import re

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_gestionnaires(apps, schema_editor):
    StationService = apps.get_model("stations", "StationService")
    User = apps.get_model("auth", "User")

    def make_username(nom: str, station_id: int) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", nom.lower()).strip("_")[:24] or "station"
        base = f"gest_{slug}_{station_id}"[:30]
        candidate = base
        index = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base[:26]}_{index}"
            index += 1
        return candidate

    for station in StationService.objects.all():
        gestionnaire_id = station.gestionnaire_id
        needs_new = gestionnaire_id is None

        if gestionnaire_id:
            user = User.objects.filter(pk=gestionnaire_id).first()
            if user is None or user.is_staff or user.is_superuser:
                needs_new = True

        if not needs_new:
            continue

        username = make_username(station.nom, station.id)
        user = User.objects.create_user(username=username, password="changeme123")
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=["is_staff", "is_superuser"])
        station.gestionnaire_id = user.id
        station.save(update_fields=["gestionnaire_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0002_stationservice_gestionnaire"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(assign_gestionnaires, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="stationservice",
            name="gestionnaire",
            field=models.ForeignKey(
                help_text="Gestionnaire dédié à cette station (compte non administrateur).",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="stations_geres",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
