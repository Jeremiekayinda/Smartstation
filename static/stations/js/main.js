let map;
let markersLayer = L.layerGroup();
let lastUpdateSpan;
let liveDot;
let liveText;
let userMarker;

const userLocationIcon = L.icon({
  iconUrl: "/static/stations/img/user-location.svg",
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -14],
});

const stationIcons = {
  faible: L.icon({
    iconUrl: "/static/stations/img/station-green.svg",
    iconSize: [30, 36],
    iconAnchor: [15, 34],
    popupAnchor: [0, -30],
  }),
  moyenne: L.icon({
    iconUrl: "/static/stations/img/station-orange.svg",
    iconSize: [30, 36],
    iconAnchor: [15, 34],
    popupAnchor: [0, -30],
  }),
  forte: L.icon({
    iconUrl: "/static/stations/img/station-red.svg",
    iconSize: [30, 36],
    iconAnchor: [15, 34],
    popupAnchor: [0, -30],
  }),
};

function getAffluenceColor(niveau) {
  switch (niveau) {
    case "faible":
      return "green";
    case "moyenne":
      return "orange";
    case "forte":
      return "red";
    default:
      return "gray";
  }
}

function initMap() {
  const defaultCenter = [-4.4419, 15.2663]; // Kinshasa par défaut

  map = L.map("map").setView(defaultCenter, 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  markersLayer.addTo(map);
}

function locateUser() {
  if (!navigator.geolocation) {
    console.warn("Géolocalisation non supportée par ce navigateur.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const coords = [position.coords.latitude, position.coords.longitude];

      if (!userMarker) {
        userMarker = L.marker(coords, { icon: userLocationIcon }).addTo(map).bindPopup("Vous êtes ici");
      } else {
        userMarker.setLatLng(coords);
      }

      map.setView(coords, 13);
    },
    (error) => {
      console.warn("Impossible de récupérer la position de l'utilisateur :", error);
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
    }
  );
}

async function fetchStations() {
  const select = document.getElementById("filter-affluence");
  const niveau = select.value;
  const params = new URLSearchParams();
  if (niveau) {
    params.append("niveau_affluence", niveau);
  }

  const url = "/api/stations/" + (params.toString() ? "?" + params.toString() : "");

  try {
    const response = await fetch(url, {
      headers: {
        "Accept": "application/json",
      },
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error("Erreur serveur");
    }

    const data = await response.json();
    updateMarkers(data);
    updateLiveStatus(true);
  } catch (error) {
    console.error("Erreur de récupération des stations :", error);
    updateLiveStatus(false);
  }
}

function updateMarkers(stations) {
  markersLayer.clearLayers();

  if (!Array.isArray(stations)) {
    return;
  }

  stations.forEach((station) => {
    const icon =
      stationIcons[station.niveau_affluence] ||
      stationIcons.faible;

    const marker = L.marker([station.latitude, station.longitude], {
      icon,
    });

    const statutLabel = station.statut === "ouverte" ? "Ouverte" : "Fermée";
    const carburantLabel = station.carburant_disponible ? "Disponible" : "Rupture";

    const popupContent = `
      <strong>${station.nom}</strong><br />
      Statut : ${statutLabel}<br />
      Carburant : ${carburantLabel}<br />
      Véhicules : ${station.nombre_vehicules}<br />
      Affluence : ${station.niveau_affluence}<br />
      Dernière mise à jour : ${new Date(
        station.date_mise_a_jour
      ).toLocaleString("fr-FR")}
    `;

    marker.bindPopup(popupContent);
    markersLayer.addLayer(marker);
  });

  const now = new Date();
  lastUpdateSpan.textContent = now.toLocaleTimeString("fr-FR");
}

function updateLiveStatus(online) {
  if (!liveDot || !liveText) return;
  if (online) {
    liveDot.classList.add("live");
    liveText.textContent = "Données à jour";
  } else {
    liveDot.classList.remove("live");
    liveText.textContent = "Erreur de rafraîchissement";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  locateUser();

  lastUpdateSpan = document.getElementById("last-update");
  liveDot = document.getElementById("live-dot");
  liveText = document.getElementById("live-text");

  const select = document.getElementById("filter-affluence");
  select.addEventListener("change", () => {
    fetchStations();
  });

  fetchStations();
  setInterval(fetchStations, 10000);
});

