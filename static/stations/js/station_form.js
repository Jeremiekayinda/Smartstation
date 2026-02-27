let stationFormMap;
let stationMarker;

const stationFormIcon = L.icon({
  iconUrl: "/static/stations/img/station-green.svg",
  iconSize: [30, 36],
  iconAnchor: [15, 34],
  popupAnchor: [0, -30],
});

function initStationFormMap() {
  const defaultCenter = [-4.4419, 15.2663]; // Kinshasa

  stationFormMap = L.map("map").setView(defaultCenter, 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(stationFormMap);

  const latInput = document.getElementById("id_latitude");
  const lngInput = document.getElementById("id_longitude");

  // Si des coordonnées existent déjà (édition éventuelle)
  if (latInput.value && lngInput.value) {
    const coords = [parseFloat(latInput.value), parseFloat(lngInput.value)];
    stationMarker = L.marker(coords, { icon: stationFormIcon }).addTo(stationFormMap);
    stationFormMap.setView(coords, 14);
  }

  stationFormMap.on("click", (e) => {
    const { lat, lng } = e.latlng;

    if (stationMarker) {
      stationMarker.setLatLng(e.latlng);
    } else {
      stationMarker = L.marker(e.latlng, { icon: stationFormIcon }).addTo(stationFormMap);
    }

    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("map")) {
    initStationFormMap();
  }
});

