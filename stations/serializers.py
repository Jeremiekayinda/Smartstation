from rest_framework import serializers

from .models import StationService, HistoriqueCapteurs


class StationServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationService
        fields = [
            "id",
            "nom",
            "latitude",
            "longitude",
            "statut",
            "carburant_disponible",
            "nombre_vehicules",
            "niveau_affluence",
            "date_mise_a_jour",
        ]
        read_only_fields = ["niveau_affluence", "date_mise_a_jour"]


class HistoriqueCapteursSerializer(serializers.ModelSerializer):
    station = serializers.PrimaryKeyRelatedField(
        queryset=StationService.objects.all()
    )

    class Meta:
        model = HistoriqueCapteurs
        fields = ["id", "station", "nombre_vehicules", "timestamp"]
        read_only_fields = ["timestamp"]

    def validate_nombre_vehicules(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError(
                "Le nombre de véhicules doit être positif."
            )
        return value
