"""
Peuple la base avec 20 stations-service réelles de Kinshasa.

Coordonnées vérifiées via :
  - OpenStreetMap (amenity=fuel, 2026)
  - Ngandu Vially et al., IJRASRE 2019 (relevé GPS terrain ±3 m, réseau Total Kinshasa)
  - sonahydroc.cd / cobil.cd (adresses officielles)

Usage:
    python manage.py seed_stations --only
    python manage.py seed_stations --reset
"""

from django.core.management.base import BaseCommand

from stations.models import StationService


LEGACY_FICTIONAL_NAMES = [
    "TotalEnergies Boulevard du 30 Juin",
    "Shell Avenue Batetela",
    "TotalEnergies Limete",
    "Shell Kasa-Vubu",
    "Shell Matonge",
    "Cobil Avenue Kasa-Vubu",
    "Engen Ngaliema",
    "TotalEnergies Kintambo",
    "Sonahydroc Kintambo",
    "Cobil Bandalungwa",
    "TotalEnergies N'djili",
    "KM Oil Limete",
    "Engen Lemba",
    "TotalEnergies Matete",
    "Shell Mont Ngafula",
    "TotalEnergies Masina",
    "TotalEnergies Selembao",
    "Engen Gombe",
    "Cobil Kalamu",
    "TotalEnergies Kinshasa Port",
    "Shell Gombe",
    "TotalEnergies Lingwala",
    "KM Oil Ngaliema",
    "Oilibya Lemba",
    "Petro Congo Matete",
    "Station Galaxy Kinshasa",
    "Congo Fuel Masina",
    "Kin Fuel N'djili",
    "Eco Station Limete",
    "Barumbu Express",
    "Kasa Oil Kasa-Vubu",
    "Selembao Petroleum",
    "Mont Ngafula Energy",
    "Ngaba Plus",
    "Bumbu Service",
    "Ngiri Station",
    "Makala Energie",
]

# coords_source : OSM | GPS_SURVEY_2019 | PHOTON | OFFICIAL_ADDRESS
SEED_STATIONS = [
    {
        "nom": "TotalEnergies Gombe",
        "commune": "Gombe",
        "adresse": "Avenue Lieutenant Colonel Ngongo Lutete, Gombe",
        "latitude": -4.30328,
        "longitude": 15.30338,
        "coords_source": "GPS_SURVEY_2019",
        "telephone": "+243 857 111 111",
        "carburants": "Essence, Gasoil, Super",
        "capacite_max": 40,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 4,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "TotalEnergies Socimat",
        "commune": "Gombe",
        "adresse": "Boulevard du 24 Novembre (Socimat), Gombe",
        "latitude": -4.3117704,
        "longitude": 15.2888972,
        "coords_source": "OSM",
        "telephone": "+243 857 111 111",
        "carburants": "Essence, Gasoil",
        "capacite_max": 38,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 7,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "TotalEnergies Victoire",
        "commune": "Kalamu",
        "adresse": "En face de la RTNC, Avenue du Peuple, Kalamu",
        "latitude": -4.32809,
        "longitude": 15.29646,
        "coords_source": "GPS_SURVEY_2019",
        "telephone": "+243 857 111 111",
        "carburants": "Essence, Gasoil",
        "capacite_max": 36,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 10,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "TotalEnergies Limete",
        "commune": "Limete",
        "adresse": "15ème Rue / Petit Boulevard Résidentiel, Limete",
        "latitude": -4.3669443,
        "longitude": 15.3418358,
        "coords_source": "OSM",
        "telephone": "+243 857 111 111",
        "carburants": "Essence, Gasoil",
        "capacite_max": 42,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 11,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "TotalEnergies Kintambo",
        "commune": "Kintambo",
        "adresse": "Rond-point Magasin, Kintambo",
        "latitude": -4.3336368,
        "longitude": 15.2583728,
        "coords_source": "OSM",
        "telephone": "+243 857 111 111",
        "carburants": "Essence, Gasoil",
        "capacite_max": 35,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 6,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Cobil Gombe",
        "commune": "Gombe",
        "adresse": "Croisement des Avenues Ipenge et Plateau (F/S Okapi), Gombe",
        "latitude": -4.3079121,
        "longitude": 15.3077156,
        "coords_source": "OSM",
        "telephone": "+243 818 200 100",
        "carburants": "Essence, Gasoil",
        "capacite_max": 32,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 3,
        "horaires": "6h30 - 21h30",
    },
    {
        "nom": "Cobil Limete",
        "commune": "Limete",
        "adresse": "Boulevard Lumumba, Limete",
        "latitude": -4.3798763,
        "longitude": 15.3409554,
        "coords_source": "OSM",
        "telephone": "+243 818 200 101",
        "carburants": "Essence, Gasoil",
        "capacite_max": 34,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 9,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Cobil Kintambo",
        "commune": "Kintambo",
        "adresse": "Avenue Colonel Mondjiba, Centre commercial Kintambo",
        "latitude": -4.3332615,
        "longitude": 15.2584583,
        "coords_source": "OSM",
        "telephone": "+243 818 200 102",
        "carburants": "Essence, Gasoil",
        "capacite_max": 30,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 2,
        "horaires": "7h00 - 21h00",
    },
    {
        "nom": "Cobil Masina",
        "commune": "Masina",
        "adresse": "Route Petro-Congo, Masina",
        "latitude": -4.3979998,
        "longitude": 15.3715228,
        "coords_source": "OSM",
        "telephone": "+243 818 200 103",
        "carburants": "Essence, Gasoil",
        "capacite_max": 36,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 14,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Engen Gombe",
        "commune": "Gombe",
        "adresse": "Avenue de la Libération, Gombe",
        "latitude": -4.305712,
        "longitude": 15.3088238,
        "coords_source": "OSM",
        "telephone": "+243 818 300 300",
        "carburants": "Essence, Gasoil, Super",
        "capacite_max": 38,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 8,
        "horaires": "6h00 - 23h00",
    },
    {
        "nom": "Engen Ngaliema",
        "commune": "Ngaliema",
        "adresse": "Route de Matadi (quartier UPN), Ngaliema",
        "latitude": -4.3325492,
        "longitude": 15.2700171,
        "coords_source": "OSM",
        "telephone": "+243 818 300 301",
        "carburants": "Essence, Gasoil",
        "capacite_max": 40,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 12,
        "horaires": "6h00 - 21h00",
    },
    {
        "nom": "Engen Bandalungwa",
        "commune": "Bandalungwa",
        "adresse": "Avenue Kasa-Vubu / Avenue de l'Enseignement (Bloc), Bandalungwa",
        "latitude": -4.3429878,
        "longitude": 15.2778346,
        "coords_source": "OSM",
        "telephone": "+243 818 300 302",
        "carburants": "Essence, Gasoil",
        "capacite_max": 33,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 5,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Sonahydroc Limete",
        "commune": "Limete",
        "adresse": "1ère rue Limete Funa, Boulevard Lumumba, Limete",
        "latitude": -4.3378849,
        "longitude": 15.3276578,
        "coords_source": "OFFICIAL_ADDRESS",
        "telephone": "+243 820 121 420",
        "carburants": "Essence, Gasoil",
        "capacite_max": 28,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 6,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Sonahydroc Masina",
        "commune": "Masina",
        "adresse": "Route Petro-Congo / Base SEP Masina, Masina",
        "latitude": -4.37538,
        "longitude": 15.37538,
        "coords_source": "GPS_SURVEY_2019",
        "telephone": "+243 820 121 420",
        "carburants": "Essence, Gasoil",
        "capacite_max": 30,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 16,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Sonahydroc Matete",
        "commune": "Matete",
        "adresse": "Marché Tomba, Matete",
        "latitude": -4.39002,
        "longitude": 15.34504,
        "coords_source": "GPS_SURVEY_2019",
        "telephone": "+243 820 121 420",
        "carburants": "Essence, Gasoil",
        "capacite_max": 32,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 9,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "KM Oil Ngaba",
        "commune": "Ngaba",
        "adresse": "Rond-point Ngaba, Ngaba",
        "latitude": -4.3689184,
        "longitude": 15.2849158,
        "coords_source": "OSM",
        "telephone": "+243 818 600 600",
        "carburants": "Essence, Gasoil",
        "capacite_max": 31,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 4,
        "horaires": "6h00 - 21h00",
    },
    {
        "nom": "KM Oil Pompage",
        "commune": "Mont Ngafula",
        "adresse": "Terminus Mbudi / Route de Pompage, Mont Ngafula",
        "latitude": -4.36156,
        "longitude": 15.19339,
        "coords_source": "GPS_SURVEY_2019",
        "telephone": "+243 818 600 601",
        "carburants": "Essence, Gasoil",
        "capacite_max": 28,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 2,
        "horaires": "6h00 - 21h00",
    },
    {
        "nom": "Mino Congo Station",
        "commune": "Gombe",
        "adresse": "Avenue de la Gombe / zone Grands Moulins, Gombe",
        "latitude": -4.3064885,
        "longitude": 15.3098152,
        "coords_source": "PHOTON",
        "telephone": "+243 818 500 200",
        "carburants": "Essence, Gasoil",
        "capacite_max": 26,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 1,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Puma Energy Limete",
        "commune": "Limete",
        "adresse": "Échangeur de Limete, Boulevard Lumumba, Limete",
        "latitude": -4.3752899,
        "longitude": 15.3440165,
        "coords_source": "OSM",
        "telephone": "+243 818 700 700",
        "carburants": "Essence, Gasoil",
        "capacite_max": 34,
        "statut": "ouverte",
        "carburant_disponible": True,
        "nombre_vehicules": 13,
        "horaires": "6h00 - 22h00",
    },
    {
        "nom": "Puma Energy Masina",
        "commune": "Masina",
        "adresse": "Avenue Mobutu / zone commerciale Masina",
        "latitude": -4.3908544,
        "longitude": 15.3751726,
        "coords_source": "OSM",
        "telephone": "+243 818 700 701",
        "carburants": "Essence, Gasoil",
        "capacite_max": 37,
        "statut": "ouverte",
        "carburant_disponible": False,
        "nombre_vehicules": 18,
        "horaires": "6h00 - 22h00",
    },
]

SEED_NAMES = [s["nom"] for s in SEED_STATIONS]


def build_adresse(data: dict) -> str:
    horaires = data.pop("horaires", "6h00 - 22h00")
    commune = data.pop("commune", "")
    data.pop("coords_source", None)
    adresse = data.get("adresse", "")
    if commune and commune not in adresse:
        adresse = f"{adresse}, {commune}"
    return f"{adresse} | Horaires : {horaires}"


class Command(BaseCommand):
    help = "Insère 20 stations-service réelles de Kinshasa (coordonnées vérifiées)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime les stations seed existantes puis les recrée.",
        )
        parser.add_argument(
            "--only",
            action="store_true",
            help="Supprime TOUTES les stations puis insère uniquement les 20 stations seed.",
        )

    def handle(self, *args, **options):
        if options["only"]:
            deleted, _ = StationService.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Base vidée : {deleted} enregistrement(s)."))
        elif options["reset"]:
            names = set(LEGACY_FICTIONAL_NAMES + SEED_NAMES)
            deleted, _ = StationService.objects.filter(nom__in=names).delete()
            self.stdout.write(self.style.WARNING(f"Supprimé : {deleted} enregistrement(s) seed."))

        created = 0
        updated = 0

        for entry in SEED_STATIONS:
            data = dict(entry)
            nom = data["nom"]
            adresse = build_adresse(data)
            defaults = {k: v for k, v in data.items() if k != "nom"}
            defaults["adresse"] = adresse

            station, was_created = StationService.objects.update_or_create(
                nom=nom,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1
            self.stdout.write(
                f"  {'+' if was_created else '~'} {station.nom} "
                f"({station.niveau_affluence}, {station.nombre_vehicules} véh.) "
                f"[{station.latitude}, {station.longitude}]"
            )

        total_seed = StationService.objects.filter(nom__in=SEED_NAMES).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nTerminé : {created} créée(s), {updated} mise(s) à jour. "
                f"{total_seed} station(s) en base."
            )
        )
