from __future__ import annotations

from django.db import models


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
    adresse = models.CharField(max_length=500, blank=True, default="")
    latitude = models.FloatField()
    longitude = models.FloatField()
    telephone = models.CharField(max_length=30, blank=True, default="")
    carburants = models.CharField(
        max_length=255,
        default="Essence, Gasoil",
        help_text="Carburants proposés, séparés par des virgules.",
    )
    capacite_max = models.PositiveIntegerField(default=30)
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

    @property
    def taux_occupation(self) -> float:
        if not self.capacite_max:
            return 0.0
        return round((self.nombre_vehicules / self.capacite_max) * 100, 1)

    @property
    def temps_attente_estime(self) -> str:
        if self.statut == self.STATUT_FERMEE:
            return "Fermée"
        if not self.carburant_disponible:
            return "Indisponible"
        mapping = {
            self.AFFLUENCE_FAIBLE: "~5 min",
            self.AFFLUENCE_MOYENNE: "~15 min",
            self.AFFLUENCE_FORTE: "~30 min",
        }
        return mapping.get(self.niveau_affluence, "~10 min")

    @property
    def affluence_label(self) -> str:
        return dict(self.AFFLUENCE_CHOICES).get(self.niveau_affluence, self.niveau_affluence)

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
