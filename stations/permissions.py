from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrStationManagerOrReadOnly(BasePermission):
    """
    - Lecture : tout le monde
    - Création : uniquement admin/staff
    - Mise à jour / suppression : admin/staff ou gestionnaire de la station
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Création de station uniquement pour l'admin (via API)
        if getattr(view, "action", None) == "create":
            return user.is_staff or user.is_superuser

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        # Gestionnaire rattaché à la station
        return getattr(obj, "gestionnaire_id", None) == user.id

