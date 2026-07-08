from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0003_gestionnaire_required"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="stationservice",
            name="gestionnaire",
        ),
    ]
