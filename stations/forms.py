from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import StationService
from .gestionnaires import create_gestionnaire, validate_gestionnaire_user

User = get_user_model()


class StationServiceForm(forms.ModelForm):
    gestionnaire_username = forms.CharField(
        label="Nom d'utilisateur du gestionnaire",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "select-control",
                "placeholder": "ex. gest_engen_kahuka",
                "autocomplete": "off",
            }
        ),
    )
    gestionnaire_password = forms.CharField(
        label="Mot de passe du gestionnaire",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={"class": "select-control", "autocomplete": "new-password"}
        ),
    )
    gestionnaire_password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "select-control", "autocomplete": "new-password"}
        ),
    )

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
            "nom": forms.TextInput(
                attrs={"class": "select-control", "placeholder": "Nom de la station"}
            ),
            "latitude": forms.NumberInput(
                attrs={"class": "select-control", "step": "0.000001"}
            ),
            "longitude": forms.NumberInput(
                attrs={"class": "select-control", "step": "0.000001"}
            ),
            "nombre_vehicules": forms.NumberInput(
                attrs={"class": "select-control", "min": "0"}
            ),
            "statut": forms.Select(attrs={"class": "select-control"}),
            "carburant_disponible": forms.CheckboxInput(),
        }

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("gestionnaire_password")
        confirm = cleaned.get("gestionnaire_password_confirm")
        if password != confirm:
            raise ValidationError(
                {"gestionnaire_password_confirm": "Les mots de passe ne correspondent pas."}
            )
        return cleaned

    def save(self, commit=True):
        if not commit:
            raise ValidationError(
                "La création de station doit inclure le gestionnaire."
            )
        gestionnaire = create_gestionnaire(
            self.cleaned_data["gestionnaire_username"],
            self.cleaned_data["gestionnaire_password"],
        )
        station = super().save(commit=False)
        station.gestionnaire = gestionnaire
        station.save()
        return station


class StationServiceAdminForm(forms.ModelForm):
    gestionnaire_username = forms.CharField(
        label="Nom d'utilisateur du gestionnaire",
        max_length=150,
        required=False,
        help_text="Obligatoire à la création. Compte dédié, sans droits admin.",
    )
    gestionnaire_password = forms.CharField(
        label="Mot de passe du gestionnaire",
        required=False,
        widget=forms.PasswordInput,
        help_text="Minimum 8 caractères.",
    )

    class Meta:
        model = StationService
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["gestionnaire"].disabled = True
            self.fields["gestionnaire_username"].disabled = True
            self.fields["gestionnaire_password"].help_text = (
                "Laisser vide pour conserver le mot de passe actuel."
            )
        else:
            self.fields.pop("gestionnaire")

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk:
            username = cleaned.get("gestionnaire_username", "").strip()
            password = cleaned.get("gestionnaire_password", "")
            if not username:
                raise ValidationError(
                    {"gestionnaire_username": "Ce champ est obligatoire."}
                )
            if len(password) < 8:
                raise ValidationError(
                    {"gestionnaire_password": "Minimum 8 caractères."}
                )
        return cleaned

    def save(self, commit=True):
        if self.instance.pk:
            station = super().save(commit=commit)
            password = self.cleaned_data.get("gestionnaire_password")
            if password:
                station.gestionnaire.set_password(password)
                station.gestionnaire.save(update_fields=["password"])
            return station

        gestionnaire = create_gestionnaire(
            self.cleaned_data["gestionnaire_username"],
            self.cleaned_data["gestionnaire_password"],
        )
        station = super().save(commit=False)
        station.gestionnaire = gestionnaire
        if commit:
            station.save()
        return station
