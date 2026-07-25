from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import StationService

User = get_user_model()
BOOTSTRAP = "form-control ss-input"


class StationServiceForm(forms.ModelForm):
    class Meta:
        model = StationService
        fields = [
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
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": BOOTSTRAP, "placeholder": "Nom de la station"}),
            "adresse": forms.TextInput(attrs={"class": BOOTSTRAP, "placeholder": "Adresse complète"}),
            "latitude": forms.NumberInput(attrs={"class": BOOTSTRAP, "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"class": BOOTSTRAP, "step": "0.000001"}),
            "telephone": forms.TextInput(attrs={"class": BOOTSTRAP, "placeholder": "+243..."}),
            "carburants": forms.TextInput(attrs={"class": BOOTSTRAP, "placeholder": "Essence, Gasoil"}),
            "capacite_max": forms.NumberInput(attrs={"class": BOOTSTRAP, "min": "1"}),
            "nombre_vehicules": forms.NumberInput(attrs={"class": BOOTSTRAP, "min": "0"}),
            "statut": forms.Select(attrs={"class": "form-select ss-input"}),
            "carburant_disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": BOOTSTRAP}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", BOOTSTRAP)
            if field.widget.__class__.__name__ == "PasswordInput":
                field.widget.attrs.setdefault("placeholder", "••••••••")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": BOOTSTRAP, "placeholder": "Prénom"}),
            "last_name": forms.TextInput(attrs={"class": BOOTSTRAP, "placeholder": "Nom"}),
            "email": forms.EmailInput(attrs={"class": BOOTSTRAP, "placeholder": "email@exemple.com"}),
        }
