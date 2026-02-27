from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StationMapView,
    StationServiceViewSet,
    CapteurDataView,
    DashboardView,
    StationCreateView,
    MyStationsView,
)

router = DefaultRouter()
router.register(r"stations", StationServiceViewSet, basename="station")

urlpatterns = [
    path("", StationMapView.as_view(), name="stations-map"),
    path("dashboard/", DashboardView.as_view(), name="stations-dashboard"),
    path("mes-stations/", MyStationsView.as_view(), name="my-stations"),
    path("stations/nouvelle/", StationCreateView.as_view(), name="station-create"),
    path("api/capteurs/", CapteurDataView.as_view(), name="api-capteurs"),
    path("api/", include(router.urls)),
]

