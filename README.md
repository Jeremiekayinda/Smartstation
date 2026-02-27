# Smartstation

Smartstation est une application web Django de cartographie interactive permettant de localiser les stations-service et d'afficher en temps réel :

- disponibilité de la station (ouverte / fermée)
- disponibilité du carburant
- niveau d'affluence (faible / moyenne / forte)
- nombre de véhicules présents (provenant de capteurs IoT)

## Stack technique

- Python 3.x
- Django
- SQLite
- Django REST Framework
- HTML / CSS / JavaScript
- Leaflet.js / OpenStreetMap

## Installation

```bash
cd SmartStation
python -m venv venv
venv\Scripts\activate  # Sous Windows
pip install -r requirements.txt
```

## Démarrage du projet

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Accéder ensuite à :

- Interface web : http://127.0.0.1:8000/
- Admin Django : http://127.0.0.1:8000/admin/

## API capteurs (exemple)

Endpoint protégé par token :

- `POST /api/capteurs/`
  - Authentification : `TokenAuthentication` (DRF)

Headers :

- `Authorization: Token VOTRE_CLE`
- `Content-Type: application/json`

Body :

```json
{
  "station_id": 1,
  "nombre_vehicules": 12,
  "statut": "ouverte",
  "carburant_disponible": true
}
```

Le champ `station_id` est accepté et mappé automatiquement vers `station` côté serveur.

## Récupération d'un token API

Pour obtenir un token (à partir d'un couple `username` / `password`) :

- `POST /api/token/`

Body (form-data ou JSON simple) :

```json
{
  "username": "votre_utilisateur",
  "password": "votre_mot_de_passe"
}
```

Réponse :

```json
{
  "token": "CLE_A_UTILISER_DANS_LE_HEADER_AUTHORIZATION"
}
```

