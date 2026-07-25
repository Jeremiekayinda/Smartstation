from rest_framework import serializers

from .models import StationService, HistoriqueCapteurs


class StationServiceSerializer(serializers.ModelSerializer):
    taux_occupation = serializers.FloatField(read_only=True)
    temps_attente_estime = serializers.CharField(read_only=True)
    affluence_label = serializers.CharField(read_only=True)

    class Meta:
        model = StationService
        fields = [
            "id",
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
            "niveau_affluence",
            "affluence_label",
            "taux_occupation",
            "temps_attente_estime",
            "date_mise_a_jour",
        ]
        read_only_fields = ["niveau_affluence", "date_mise_a_jour"]


class HistoriqueCapteursSerializer(serializers.ModelSerializer):
    station = serializers.PrimaryKeyRelatedField(
        queryset=StationService.objects.all()
    )
    station_nom = serializers.CharField(source="station.nom", read_only=True)

    class Meta:
        model = HistoriqueCapteurs
        fields = ["id", "station", "station_nom", "nombre_vehicules", "timestamp"]
        read_only_fields = ["timestamp"]

    def validate_nombre_vehicules(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError(
                "Le nombre de véhicules doit être positif."
            )
        return value
