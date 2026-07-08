from typing import Any

from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StationService, HistoriqueCapteurs
from .serializers import (
    StationServiceSerializer,
    HistoriqueCapteursSerializer,
)
from .forms import StationServiceForm
from .permissions import IsAdminOrReadOnly


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("admin-login")

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user and (user.is_staff or user.is_superuser))


class StationMapView(TemplateView):
    template_name = "stations/index.html"


class AdminLoginView(LoginView):
    template_name = "stations/admin_login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        return str(reverse_lazy("admin-stations"))

    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_staff or user.is_superuser):
            form.add_error(
                None,
                "Accès réservé aux administrateurs.",
            )
            return self.form_invalid(form)
        return super().form_valid(form)


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy("admin-login")


class AdminStationListView(AdminRequiredMixin, TemplateView):
    template_name = "stations/admin_stations.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["stations"] = StationService.objects.all()
        return context


class AdminStationDetailView(AdminRequiredMixin, UpdateView):
    model = StationService
    form_class = StationServiceForm
    template_name = "stations/admin_station_detail.html"
    context_object_name = "station"

    def get_success_url(self):
        return reverse_lazy("admin-station-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["historiques"] = self.object.historiques.all()[:10]
        return context


class StationCreateView(AdminRequiredMixin, CreateView):
    model = StationService
    form_class = StationServiceForm
    template_name = "stations/station_form.html"
    success_url = reverse_lazy("admin-stations")


class StationServiceViewSet(viewsets.ModelViewSet):
    queryset = StationService.objects.all()
    serializer_class = StationServiceSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        niveau = self.request.query_params.get("niveau_affluence")
        if niveau:
            qs = qs.filter(niveau_affluence=niveau)
        return qs


class CapteurDataView(APIView):
    """
    Réception des données des capteurs IoT.
    Endpoint: POST /api/capteurs/
    Protégé par token (authentification DRF).
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        data = request.data.copy()

        station_id = data.get("station_id")
        if station_id is not None and data.get("station") is None:
            data["station"] = station_id

        serializer = HistoriqueCapteursSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        historique = serializer.save()
        station = historique.station
        station.nombre_vehicules = historique.nombre_vehicules

        statut = data.get("statut")
        if statut in dict(StationService.STATUT_CHOICES):
            station.statut = statut

        carburant_disponible = data.get("carburant_disponible")
        if carburant_disponible is not None:
            if isinstance(carburant_disponible, bool):
                station.carburant_disponible = carburant_disponible
            elif isinstance(carburant_disponible, (int, float)):
                station.carburant_disponible = carburant_disponible != 0
            elif isinstance(carburant_disponible, str):
                station.carburant_disponible = carburant_disponible.strip().lower() in {
                    "1",
                    "true",
                    "vrai",
                    "yes",
                    "oui",
                    "on",
                }

        station.save()

        station_data = StationServiceSerializer(station).data
        return Response(
            {"detail": "Données capteur enregistrées.", "station": station_data},
            status=status.HTTP_201_CREATED,
        )


class DashboardView(TemplateView):
    template_name = "stations/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from django.db.models import Count

        context = super().get_context_data(**kwargs)
        total_stations = StationService.objects.count()
        stations_ouvertes = StationService.objects.filter(
            statut=StationService.STATUT_OUVERTE
        ).count()
        stations_actives = StationService.objects.filter(
            niveau_affluence__in=[
                StationService.AFFLUENCE_FAIBLE,
                StationService.AFFLUENCE_MOYENNE,
                StationService.AFFLUENCE_FORTE,
            ]
        ).count()
        repartition_affluence = (
            StationService.objects.values("niveau_affluence")
            .annotate(total=Count("id"))
            .order_by("niveau_affluence")
        )

        context.update(
            {
                "total_stations": total_stations,
                "stations_ouvertes": stations_ouvertes,
                "stations_actives": stations_actives,
                "repartition_affluence": repartition_affluence,
            }
        )
        return context
