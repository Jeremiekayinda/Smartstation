from typing import Any

from django.db import transaction
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import redirect

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StationService, HistoriqueCapteurs
from .serializers import StationServiceSerializer, HistoriqueCapteursSerializer
from .forms import StationServiceForm, RegisterForm, ProfileForm
from .permissions import IsAdminOrReadOnly


class AuthRequiredMixin(LoginRequiredMixin):
    """Pages utilisateur : redirection vers /login/ si non authentifié."""

    login_url = reverse_lazy("login")


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("admin-login")

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user and (user.is_staff or user.is_superuser))


class RootRedirectView(View):
    """Point d'entrée : / → /login/ ou /home/ si déjà connecté."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return redirect("login")


# --- Pages utilisateur (authentification requise) ---

class HomeView(AuthRequiredMixin, TemplateView):
    template_name = "stations/home.html"


class StationMapView(AuthRequiredMixin, TemplateView):
    template_name = "stations/map.html"


class StationListView(AuthRequiredMixin, TemplateView):
    template_name = "stations/station_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["stations"] = StationService.objects.all()
        return context


class StationDetailView(AuthRequiredMixin, DetailView):
    model = StationService
    template_name = "stations/station_detail.html"
    context_object_name = "station"


class ProfileView(AuthRequiredMixin, TemplateView):
    template_name = "stations/profile.html"


class ProfileEditView(AuthRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "stations/profile_edit.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profil mis à jour avec succès.")
        return super().form_valid(form)


class UserPasswordChangeView(AuthRequiredMixin, PasswordChangeView):
    template_name = "stations/password_change.html"
    success_url = reverse_lazy("profile")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "form-control ss-input")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Mot de passe mis à jour avec succès.")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Vous avez été déconnecté.")
        return super().dispatch(request, *args, **kwargs)


class SettingsView(AuthRequiredMixin, TemplateView):
    template_name = "stations/settings.html"


# --- Authentification ---

class UserLoginView(LoginView):
    template_name = "stations/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        return str(reverse_lazy("home"))

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Bienvenue, {self.request.user.username} !")
        return response


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "stations/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f"Bienvenue, {self.object.username} !")
        return response


# --- Administration ---

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
            form.add_error(None, "Accès réservé aux administrateurs.")
            return self.form_invalid(form)
        messages.success(self.request, f"Bienvenue, {user.username} !")
        return super().form_valid(form)


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy("admin-login")

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Vous avez été déconnecté.")
        return super().dispatch(request, *args, **kwargs)


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
        messages.success(self.request, "Station mise à jour avec succès.")
        return reverse_lazy("admin-station-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["historiques"] = self.object.historiques.all()[:10]
        return context


class AdminCapteursView(AdminRequiredMixin, TemplateView):
    template_name = "stations/admin_capteurs.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["historiques"] = (
            HistoriqueCapteurs.objects.select_related("station").all()[:50]
        )
        return context


class StationCreateView(AdminRequiredMixin, CreateView):
    model = StationService
    form_class = StationServiceForm
    template_name = "stations/station_form.html"
    success_url = reverse_lazy("admin-stations")

    def form_valid(self, form):
        messages.success(self.request, "Station créée avec succès.")
        return super().form_valid(form)


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = "stations/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from django.db.models import Count

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "total_stations": StationService.objects.count(),
                "stations_ouvertes": StationService.objects.filter(
                    statut=StationService.STATUT_OUVERTE
                ).count(),
                "stations_actives": StationService.objects.exclude(
                    statut=StationService.STATUT_FERMEE
                ).count(),
                "repartition_affluence": (
                    StationService.objects.values("niveau_affluence")
                    .annotate(total=Count("id"))
                    .order_by("niveau_affluence")
                ),
                "derniers_capteurs": HistoriqueCapteurs.objects.select_related(
                    "station"
                ).all()[:8],
            }
        )
        return context


# --- API ---

class StationServiceViewSet(viewsets.ModelViewSet):
    queryset = StationService.objects.all()
    serializer_class = StationServiceSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        niveau = self.request.query_params.get("niveau_affluence")
        search = self.request.query_params.get("search")
        if niveau:
            qs = qs.filter(niveau_affluence=niveau)
        if search:
            qs = qs.filter(nom__icontains=search)
        return qs


class CapteurDataView(APIView):
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
                    "1", "true", "vrai", "yes", "oui", "on",
                }

        station.save()
        return Response(
            {
                "detail": "Données capteur enregistrées.",
                "station": StationServiceSerializer(station).data,
            },
            status=status.HTTP_201_CREATED,
        )
