from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from .views import (
    RootRedirectView,
    HomeView,
    StationMapView,
    StationListView,
    StationDetailView,
    RegisterView,
    UserLoginView,
    ProfileView,
    ProfileEditView,
    UserPasswordChangeView,
    UserLogoutView,
    SettingsView,
    StationServiceViewSet,
    CapteurDataView,
    DashboardView,
    StationCreateView,
    AdminLoginView,
    AdminLogoutView,
    AdminStationListView,
    AdminStationDetailView,
    AdminCapteursView,
)

router = DefaultRouter()
router.register(r"stations", StationServiceViewSet, basename="api-station")

urlpatterns = [
    # Point d'entrée et authentification
    path("", RootRedirectView.as_view(), name="root"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("inscription/", RegisterView.as_view(), name="register"),
    # Pages utilisateur (protégées) — noms distincts de l'API DRF
    path("home/", HomeView.as_view(), name="home"),
    path("map/", StationMapView.as_view(), name="map"),
    path("stations/", StationListView.as_view(), name="stations-list"),
    path("stations/<int:pk>/", StationDetailView.as_view(), name="station-page"),
    path("profil/", ProfileView.as_view(), name="profile"),
    path("profil/modifier/", ProfileEditView.as_view(), name="profile-edit"),
    path("profil/mot-de-passe/", UserPasswordChangeView.as_view(), name="password-change"),
    path("deconnexion/", UserLogoutView.as_view(), name="logout"),
    path("parametres/", SettingsView.as_view(), name="settings"),
    # Administration
    path("administration/connexion/", AdminLoginView.as_view(), name="admin-login"),
    path("administration/deconnexion/", AdminLogoutView.as_view(), name="admin-logout"),
    path("administration/", AdminStationListView.as_view(), name="admin-stations"),
    path("administration/tableau-de-bord/", DashboardView.as_view(), name="admin-dashboard"),
    path("administration/capteurs/", AdminCapteursView.as_view(), name="admin-capteurs"),
    path("administration/stations/nouvelle/", StationCreateView.as_view(), name="station-create"),
    path(
        "administration/stations/<int:pk>/",
        AdminStationDetailView.as_view(),
        name="admin-station-detail",
    ),
    # Rétrocompatibilité
    path("carte/", RedirectView.as_view(pattern_name="map", permanent=False)),
    path("connexion/", RedirectView.as_view(pattern_name="login", permanent=False)),
    # API
    path("api/capteurs/", CapteurDataView.as_view(), name="api-capteurs"),
    path("api/", include(router.urls)),
]
