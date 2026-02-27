from __future__ import annotations

from django.db import models
from django.conf import settings


class StationService(models.Model):
    STATUT_OUVERTE = "ouverte"
    STATUT_FERMEE = "fermee"
    STATUT_CHOICES = [
        (STATUT_OUVERTE, "Ouverte"),
        (STATUT_FERMEE, "Fermée"),
    ]

    AFFLUENCE_FAIBLE = "faible"
    AFFLUENCE_MOYENNE = "moyenne"
    AFFLUENCE_FORTE = "forte"
    AFFLUENCE_CHOICES = [
        (AFFLUENCE_FAIBLE, "Faible"),
        (AFFLUENCE_MOYENNE, "Moyenne"),
        (AFFLUENCE_FORTE, "Forte"),
    ]

    nom = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    gestionnaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stations_geres",
        help_text="Utilisateur responsable de la mise à jour de cette station.",
    )
    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default=STATUT_OUVERTE,
    )
    carburant_disponible = models.BooleanField(default=True)
    nombre_vehicules = models.PositiveIntegerField(default=0)
    niveau_affluence = models.CharField(
        max_length=10,
        choices=AFFLUENCE_CHOICES,
        default=AFFLUENCE_FAIBLE,
    )
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]


    def __str__(self) -> str:
        return self.nom

    def _calculer_affluence(self) -> str:
        if self.nombre_vehicules <= 5:
            return self.AFFLUENCE_FAIBLE
        if 6 <= self.nombre_vehicules <= 15:
            return self.AFFLUENCE_MOYENNE
        return self.AFFLUENCE_FORTE

    def save(self, *args, **kwargs) -> None:
        self.niveau_affluence = self._calculer_affluence()
        super().save(*args, **kwargs)


class HistoriqueCapteurs(models.Model):
    station = models.ForeignKey(
        StationService,
        on_delete=models.CASCADE,
        related_name="historiques",
    )
    nombre_vehicules = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.station.nom} - {self.nombre_vehicules} véhicules"

