from django.contrib import admin

from .models import StationService, HistoriqueCapteurs


@admin.register(StationService)
class StationServiceAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "statut",
        "carburant_disponible",
        "nombre_vehicules",
        "niveau_affluence",
        "date_mise_a_jour",
    )
    list_filter = ("statut", "carburant_disponible", "niveau_affluence")
    search_fields = ("nom",)
    readonly_fields = ("niveau_affluence", "date_mise_a_jour")


@admin.register(HistoriqueCapteurs)
class HistoriqueCapteursAdmin(admin.ModelAdmin):
    list_display = ("station", "nombre_vehicules", "timestamp")
    list_filter = ("station", "timestamp")
    search_fields = ("station__nom",)
