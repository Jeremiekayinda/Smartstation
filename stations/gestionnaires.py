from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def is_gestionnaire_eligible(user) -> bool:
    return bool(user and user.is_authenticated and not user.is_staff and not user.is_superuser)


def validate_gestionnaire_user(user) -> None:
    if user is None:
        raise ValidationError("Chaque station doit avoir un gestionnaire.")
    if user.is_staff or user.is_superuser:
        raise ValidationError(
            "Un administrateur ne peut pas être gestionnaire de station."
        )


def create_gestionnaire(username: str, password: str) -> User:
    username = username.strip()
    if not username:
        raise ValidationError("Le nom d'utilisateur du gestionnaire est obligatoire.")
    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError("Ce nom d'utilisateur est déjà utilisé.")
    if len(password) < 8:
        raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")

    user = User.objects.create_user(username=username, password=password)
    user.is_staff = False
    user.is_superuser = False
    user.save(update_fields=["is_staff", "is_superuser"])
    return user


def username_from_station_name(nom: str, station_id: int | None = None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", nom.lower()).strip("_")[:24] or "station"
    suffix = f"_{station_id}" if station_id else ""
    base = f"gest_{slug}{suffix}"[:30]
    candidate = base
    index = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base[:26]}_{index}"
        index += 1
    return candidate
