"""
Réindexe les stations pour obtenir des IDs consécutifs 1, 2, 3…
et réinitialise la séquence SQLite d'auto-incrémentation.

Préserve l'ordre actuel (tri par id croissant) afin que station_id=1
corresponde à la première station de la liste.

Usage:
    python manage.py reset_station_ids
    python manage.py reset_station_ids --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from stations.models import HistoriqueCapteurs, StationService

STATION_FIELDS = (
    "nom",
    "adresse",
    "latitude",
    "longitude",
    "telephone",
    "carburants",
    "capacite_max",
    "statut",
    "carburant_disponible",
    "nombre_vehicules",
)


def snapshot_stations():
    """Capture les données des stations dans l'ordre actuel des IDs."""
    snapshots = []
    for station in StationService.objects.all().order_by("id"):
        snapshots.append(
            {
                "old_id": station.id,
                "data": {field: getattr(station, field) for field in STATION_FIELDS},
            }
        )
    return snapshots


def reset_sqlite_sequence():
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM sqlite_sequence WHERE name='stations_stationservice'"
        )


class Command(BaseCommand):
    help = "Réindexe les IDs des stations (1…N) et réinitialise la séquence SQLite."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche le plan sans modifier la base.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        snapshots = snapshot_stations()
        count = len(snapshots)

        if count == 0:
            self.stdout.write(self.style.WARNING("Aucune station en base."))
            reset_sqlite_sequence()
            self.stdout.write(self.style.SUCCESS("Séquence SQLite réinitialisée."))
            return

        self.stdout.write(f"{count} station(s) à réindexer.\n")

        for index, entry in enumerate(snapshots, start=1):
            nom = entry["data"]["nom"]
            self.stdout.write(
                f"  {entry['old_id']} -> {index}  {nom}"
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("\nMode dry-run : aucune modification."))
            return

        historique_count = HistoriqueCapteurs.objects.count()
        if historique_count:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{historique_count} entrée(s) d'historique capteur seront supprimées "
                    "(clés étrangères vers les anciens IDs)."
                )
            )

        with transaction.atomic():
            HistoriqueCapteurs.objects.all().delete()
            StationService.objects.all().delete()
            reset_sqlite_sequence()

            for entry in snapshots:
                StationService.objects.create(**entry["data"])

        final = list(
            StationService.objects.all().order_by("id").values_list("id", "nom")
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT seq FROM sqlite_sequence WHERE name='stations_stationservice'"
            )
            seq_row = cursor.fetchone()

        self.stdout.write(self.style.SUCCESS(f"\n{len(final)} station(s) réindexée(s)."))
        self.stdout.write(f"Séquence SQLite : {seq_row[0] if seq_row else 'réinitialisée'}")
        self.stdout.write("\nVérification :")
        for station_id, nom in final:
            self.stdout.write(f"  id={station_id}  {nom}")
