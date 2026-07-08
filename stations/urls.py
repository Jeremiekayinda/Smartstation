from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StationMapView,
    StationServiceViewSet,
    CapteurDataView,
    DashboardView,
    StationCreateView,
    AdminLoginView,
    AdminLogoutView,
    AdminStationListView,
    AdminStationDetailView,
)

router = DefaultRouter()
router.register(r"stations", StationServiceViewSet, basename="station")

urlpatterns = [
    path("", StationMapView.as_view(), name="stations-map"),
    path("dashboard/", DashboardView.as_view(), name="stations-dashboard"),
    path("administration/connexion/", AdminLoginView.as_view(), name="admin-login"),
    path(
        "administration/deconnexion/",
        AdminLogoutView.as_view(),
        name="admin-logout",
    ),
    path("administration/", AdminStationListView.as_view(), name="admin-stations"),
    path(
        "administration/stations/nouvelle/",
        StationCreateView.as_view(),
        name="station-create",
    ),
    path(
        "administration/stations/<int:pk>/",
        AdminStationDetailView.as_view(),
        name="admin-station-detail",
    ),
    path("api/capteurs/", CapteurDataView.as_view(), name="api-capteurs"),
    path("api/", include(router.urls)),
]
