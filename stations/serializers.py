from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import StationService, HistoriqueCapteurs

User = get_user_model()


class StationServiceSerializer(serializers.ModelSerializer):
    gestionnaire = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    gestionnaire_username = serializers.ReadOnlyField(source="gestionnaire.username")

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
            "gestionnaire",
            "gestionnaire_username",
        ]
        read_only_fields = ["niveau_affluence", "date_mise_a_jour"]

    def update(self, instance, validated_data):
        """
        Un gestionnaire peut changer uniquement l'état opérationnel
        (statut, carburant_disponible, nombre_vehicules).
        L'admin peut tout modifier.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_staff:
            # On empêche les gestionnaires de modifier ces champs structurels
            for field in ["nom", "latitude", "longitude", "gestionnaire"]:
                validated_data.pop(field, None)

        return super().update(instance, validated_data)


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

