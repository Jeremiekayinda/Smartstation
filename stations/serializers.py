from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import StationService, HistoriqueCapteurs

User = get_user_model()


from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import StationService, HistoriqueCapteurs
from .gestionnaires import create_gestionnaire, validate_gestionnaire_user

User = get_user_model()


class StationServiceSerializer(serializers.ModelSerializer):
    gestionnaire = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=False, is_superuser=False),
        required=False,
        allow_null=True,
        write_only=True,
    )
    gestionnaire_username = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    gestionnaire_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=8
    )
    gestionnaire_username_display = serializers.ReadOnlyField(
        source="gestionnaire.username"
    )

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
            "gestionnaire_password",
            "gestionnaire_username_display",
        ]
        read_only_fields = ["niveau_affluence", "date_mise_a_jour"]

    def validate_gestionnaire(self, value):
        if value is not None:
            validate_gestionnaire_user(value)
        return value

    def create(self, validated_data):
        gestionnaire = validated_data.pop("gestionnaire", None)
        username = validated_data.pop("gestionnaire_username", "").strip()
        password = validated_data.pop("gestionnaire_password", "")

        if gestionnaire is None:
            if not username or not password:
                raise serializers.ValidationError(
                    {
                        "gestionnaire_username": (
                            "Indiquez gestionnaire_username et gestionnaire_password "
                            "pour créer le compte gestionnaire."
                        )
                    }
                )
            gestionnaire = create_gestionnaire(username, password)
        else:
            validate_gestionnaire_user(gestionnaire)

        validated_data["gestionnaire"] = gestionnaire
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("gestionnaire_username", None)
        validated_data.pop("gestionnaire_password", None)
        gestionnaire = validated_data.pop("gestionnaire", None)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_staff:
            for field in ["nom", "latitude", "longitude", "gestionnaire"]:
                validated_data.pop(field, None)
        elif gestionnaire is not None:
            validate_gestionnaire_user(gestionnaire)
            validated_data["gestionnaire"] = gestionnaire

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

