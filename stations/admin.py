from django.contrib import admin

from .models import StationService, HistoriqueCapteurs
from .forms import StationServiceAdminForm


@admin.register(StationService)
class StationServiceAdmin(admin.ModelAdmin):
    form = StationServiceAdminForm
    list_display = (
        "nom",
        "gestionnaire",
        "statut",
        "carburant_disponible",
        "nombre_vehicules",
        "niveau_affluence",
        "date_mise_a_jour",
    )
    list_filter = ("statut", "carburant_disponible", "niveau_affluence", "gestionnaire")
    search_fields = ("nom", "gestionnaire__username")
    readonly_fields = ("niveau_affluence", "date_mise_a_jour")

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj:
            fields.append("gestionnaire")
        return fields


@admin.register(HistoriqueCapteurs)
class HistoriqueCapteursAdmin(admin.ModelAdmin):
    list_display = ("station", "nombre_vehicules", "timestamp")
    list_filter = ("station", "timestamp")
    search_fields = ("station__nom",)
