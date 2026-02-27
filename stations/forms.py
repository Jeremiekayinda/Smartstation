from django import forms

from .models import StationService


class StationServiceForm(forms.ModelForm):
    class Meta:
        model = StationService
        fields = [
            "nom",
            "latitude",
            "longitude",
            "statut",
            "carburant_disponible",
            "nombre_vehicules",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "select-control", "placeholder": "Nom de la station"}),
            "latitude": forms.NumberInput(attrs={"class": "select-control", "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"class": "select-control", "step": "0.000001"}),
            "nombre_vehicules": forms.NumberInput(attrs={"class": "select-control", "min": "0"}),
            "statut": forms.Select(attrs={"class": "select-control"}),
            "carburant_disponible": forms.CheckboxInput(),
        }

