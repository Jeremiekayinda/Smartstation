from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0004_remove_gestionnaire"),
    ]

    operations = [
        migrations.AddField(
            model_name="stationservice",
            name="adresse",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="stationservice",
            name="capacite_max",
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name="stationservice",
            name="carburants",
            field=models.CharField(
                default="Essence, Gasoil",
                help_text="Carburants proposés, séparés par des virgules.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="stationservice",
            name="telephone",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
    ]
