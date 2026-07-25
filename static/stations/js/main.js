let map;
let markersLayer = L.layerGroup();
let userCoords = null;
let userMarker = null;
let userAccuracyCircle = null;
let allStations = [];
let activeFilter = "";
let markerRegistry = new Map();
let stationSignatures = new Map();
let initialFitDone = false;
let nearbyStationsInfo = [];
let recommendedStationId = null;
let isLocating = false;
let refreshTimer = null;
let geoWatchId = null;
let userPositionReady = false;
let searchActiveIndex = -1;
let userPopupTimer = null;

const USER_ZOOM = 16;
const USER_LOCATE_ZOOM = 16;
const USER_POPUP_AUTO_CLOSE_MS = 5000;
const NEARBY_RADIUS_KM = 5;
const REFRESH_MS = 5000;
const SEARCH_MIN_CHARS = 2;
const SEARCH_MAX_SUGGESTIONS = 8;
const GEO_OPTIONS = {
  enableHighAccuracy: true,
  timeout: 20000,
  maximumAge: 5000,
};
const GEO_WATCH_OPTIONS = {
  enableHighAccuracy: true,
  maximumAge: 5000,
  timeout: 30000,
};

const panel = document.getElementById("station-panel");
const panelContent = document.getElementById("panel-content");
const geoToast = document.getElementById("geo-toast");
const searchInput = document.getElementById("search-stations");
const searchSuggestions = document.getElementById("search-suggestions");

const AFFLUENCE_LABELS = { faible: "Faible", moyenne: "Moyenne", forte: "Forte" };
const AFFLUENCE_BADGE = { faible: "green", moyenne: "orange", forte: "red" };
const AFFLUENCE_COLORS = { faible: "#22c55e", moyenne: "#f97316", forte: "#ef4444" };

function escapeHtml(text) {
  const el = document.createElement("div");
  el.textContent = text ?? "";
  return el.innerHTML;
}

function normalizeStations(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

function stationCoords(station) {
  const lat = Number(station.latitude);
  const lng = Number(station.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return [lat, lng];
}

function affluenceLevel(station) {
  return station.niveau_affluence || "faible";
}

function affluenceBadge(niveau) {
  const label = AFFLUENCE_LABELS[niveau] || niveau;
  const cls = AFFLUENCE_BADGE[niveau] || "gray";
  return `<span class="ss-badge ss-badge--${cls}">${label}</span>`;
}

function parseStationMeta(station) {
  const raw = station.adresse || "";
  const match = raw.match(/^(.+?)\s*\|\s*Horaires\s*:\s*(.+)$/i);
  const adresse = match ? match[1].trim() : raw.trim() || "Kinshasa, RDC";
  return {
    adresse,
    horaires: match
      ? match[2].trim()
      : station.statut === "fermee"
        ? "Fermée"
        : "6h00 - 22h00",
    commune: extractCommune(adresse),
  };
}

function extractCommune(adresse) {
  const parts = adresse
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  return parts.length > 1 ? parts[parts.length - 1] : "";
}

function stationSubtitle(station) {
  const meta = parseStationMeta(station);
  if (meta.commune) return meta.commune;
  const parts = meta.adresse.split(",").map((p) => p.trim()).filter(Boolean);
  return parts[0] || meta.adresse;
}

function normalizeSearchText(value) {
  return (value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function getSearchMatches(query, limit = SEARCH_MAX_SUGGESTIONS) {
  const q = normalizeSearchText(query.trim());
  if (!q || q.length < SEARCH_MIN_CHARS) return [];

  const scored = [];

  for (const station of allStations) {
    const meta = parseStationMeta(station);
    const nom = normalizeSearchText(station.nom);
    const commune = normalizeSearchText(meta.commune);
    const adresse = normalizeSearchText(meta.adresse);
    const quartier = adresse
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean)
      .slice(0, -1)
      .join(" ");

    let score = 0;
    if (nom.startsWith(q)) score += 120;
    else if (nom.includes(q)) score += 90;
    if (commune === q) score += 110;
    else if (commune.startsWith(q)) score += 85;
    else if (commune.includes(q)) score += 65;
    if (quartier.includes(q)) score += 55;
    if (adresse.includes(q)) score += 45;

    if (score > 0) scored.push({ station, score });
  }

  return scored
    .sort((a, b) => b.score - a.score || a.station.nom.localeCompare(b.station.nom, "fr"))
    .slice(0, limit)
    .map((entry) => entry.station);
}

function hideSearchSuggestions() {
  if (!searchSuggestions) return;
  searchSuggestions.hidden = true;
  searchSuggestions.innerHTML = "";
  searchActiveIndex = -1;
  searchInput?.setAttribute("aria-expanded", "false");
}

function renderSearchSuggestions(matches) {
  if (!searchSuggestions || !searchInput) return;

  if (!matches.length) {
    searchSuggestions.innerHTML = `
      <div class="ss-search-suggestions__empty" role="option" aria-disabled="true">
        <i class="bi bi-search" aria-hidden="true"></i>
        <span>Aucune station trouvée</span>
      </div>
    `;
    searchSuggestions.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
    return;
  }

  searchSuggestions.innerHTML = matches
    .map((station, index) => {
      const level = affluenceLevel(station);
      return `
        <button
          type="button"
          class="ss-search-suggestion"
          role="option"
          data-station-id="${station.id}"
          data-index="${index}"
          id="search-suggestion-${index}"
        >
          <span class="ss-search-suggestion__dot ss-search-suggestion__dot--${level}" aria-hidden="true"></span>
          <span class="ss-search-suggestion__text">
            <span class="ss-search-suggestion__title">${escapeHtml(station.nom)}</span>
            <span class="ss-search-suggestion__subtitle">${escapeHtml(stationSubtitle(station))}</span>
          </span>
          <i class="bi bi-chevron-right ss-search-suggestion__arrow" aria-hidden="true"></i>
        </button>
      `;
    })
    .join("");

  searchSuggestions.hidden = false;
  searchInput.setAttribute("aria-expanded", "true");
  searchActiveIndex = -1;
}

function highlightSearchSuggestion(index) {
  if (!searchSuggestions) return;
  const items = [...searchSuggestions.querySelectorAll(".ss-search-suggestion")];
  items.forEach((item, i) => item.classList.toggle("is-active", i === index));
  if (index >= 0 && items[index]) {
    items[index].scrollIntoView({ block: "nearest" });
    searchInput?.setAttribute("aria-activedescendant", items[index].id);
  } else {
    searchInput?.removeAttribute("aria-activedescendant");
  }
}

function selectSearchStation(station) {
  if (!station) return;
  hideSearchSuggestions();
  if (searchInput) searchInput.value = station.nom;
  focusOnStation(station, { openPopup: true });
}

function handleSearchInput() {
  const query = searchInput?.value.trim() ?? "";
  if (query.length < SEARCH_MIN_CHARS) {
    hideSearchSuggestions();
    return;
  }
  renderSearchSuggestions(getSearchMatches(query));
}

function handleSearchSuggestionClick(event) {
  const item = event.target.closest(".ss-search-suggestion");
  if (!item) return;
  const stationId = Number(item.dataset.stationId);
  const station = allStations.find((s) => s.id === stationId);
  selectSearchStation(station);
}

function handleSearchKeydown(event) {
  if (!searchSuggestions || searchSuggestions.hidden) {
    if (event.key === "Escape") hideSearchSuggestions();
    return;
  }

  const items = [...searchSuggestions.querySelectorAll(".ss-search-suggestion")];
  if (!items.length) return;

  if (event.key === "ArrowDown") {
    event.preventDefault();
    searchActiveIndex = Math.min(searchActiveIndex + 1, items.length - 1);
    highlightSearchSuggestion(searchActiveIndex);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    searchActiveIndex = Math.max(searchActiveIndex - 1, 0);
    highlightSearchSuggestion(searchActiveIndex);
  } else if (event.key === "Enter") {
    event.preventDefault();
    const target =
      searchActiveIndex >= 0
        ? allStations.find((s) => s.id === Number(items[searchActiveIndex].dataset.stationId))
        : getSearchMatches(searchInput?.value ?? "", 1)[0];
    selectSearchStation(target);
  } else if (event.key === "Escape") {
    hideSearchSuggestions();
  }
}

function formatUpdatedAt(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function formatDistance(lat1, lon1, lat2, lon2) {
  const km = haversineKm(lat1, lon1, lat2, lon2);
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

function googleMapsItineraryUrl(destLat, destLng, originLat, originLng) {
  let url = `https://www.google.com/maps/dir/?api=1&destination=${destLat},${destLng}`;
  if (
    originLat != null &&
    originLng != null &&
    Number.isFinite(Number(originLat)) &&
    Number.isFinite(Number(originLng))
  ) {
    url += `&origin=${originLat},${originLng}`;
  }
  return url;
}

function itineraryUrlForStation(coords) {
  if (!coords) return "#";
  const [lat, lng] = coords;
  if (userCoords) {
    return googleMapsItineraryUrl(lat, lng, userCoords[0], userCoords[1]);
  }
  return googleMapsItineraryUrl(lat, lng);
}

function isStationNearby(stationId) {
  return nearbyStationsInfo.some((n) => n.station.id === stationId);
}

function isStationRecommended(stationId) {
  return recommendedStationId === stationId;
}

function stationSignature(station) {
  return [
    station.niveau_affluence,
    station.nombre_vehicules,
    station.statut,
    station.carburant_disponible,
    station.taux_occupation,
    station.nom,
    isStationNearby(station.id),
    isStationRecommended(station.id),
  ].join("|");
}

function isGeolocationSupported() {
  return Boolean(navigator.geolocation);
}

function isSecureContextForGeo() {
  return window.isSecureContext === true;
}

function hideGeoToast() {
  if (!geoToast) return;
  geoToast.hidden = true;
  geoToast.innerHTML = "";
  geoToast.className = "ss-geo-toast";
}

function showGeoToast(message, { retry = false, variant = "error" } = {}) {
  if (!geoToast) {
    alert(message);
    return;
  }

  const icon =
    variant === "success" ? "bi-check-circle-fill" : "bi-exclamation-triangle-fill";

  geoToast.className = `ss-geo-toast ss-geo-toast--${variant}`;
  geoToast.innerHTML = `
    <div class="ss-geo-toast__content">
      <i class="bi ${icon}" aria-hidden="true"></i>
      <p>${escapeHtml(message)}</p>
    </div>
    ${
      retry
        ? `<button type="button" class="ss-btn ss-btn--primary ss-btn--sm" id="geo-toast-retry">Réessayer</button>`
        : ""
    }
    <button type="button" class="ss-geo-toast__close" id="geo-toast-close" aria-label="Fermer">&times;</button>
  `;
  geoToast.hidden = false;

  document.getElementById("geo-toast-close")?.addEventListener("click", hideGeoToast);
  document.getElementById("geo-toast-retry")?.addEventListener("click", () => {
    hideGeoToast();
    startUserGeolocation({ recenterOnReady: true });
  });
}

function geoErrorMessage(error) {
  if (!error) return "Impossible d'obtenir votre position. Veuillez réessayer.";
  switch (error.code) {
    case 1:
      return "Accès à la géolocalisation refusé. Autorisez la localisation dans les paramètres de votre navigateur, puis réessayez.";
    case 2:
      return "Votre position n'a pas pu être déterminée. Vérifiez que le GPS est activé et réessayez.";
    case 3:
      return "La demande de géolocalisation a expiré. Vérifiez votre connexion et réessayez.";
    default:
      return "Une erreur est survenue lors de la géolocalisation. Veuillez réessayer.";
  }
}

function setLocateButtonLoading(loading) {
  const btn = document.getElementById("btn-locate");
  if (!btn) return;
  isLocating = loading;
  btn.disabled = loading;
  btn.classList.toggle("ss-btn--loading", loading);
  const label = btn.querySelector(".ss-btn-locate-label");
  if (label) label.textContent = loading ? "Localisation…" : "Me localiser";
}

function createUserLocationIcon() {
  return L.divIcon({
    className: "ss-user-location-wrap",
    html: `
      <div class="ss-user-location" aria-hidden="true">
        <span class="ss-user-location__pulse"></span>
        <span class="ss-user-location__dot"></span>
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

function onUserPositionUpdate(position, { recenter = false } = {}) {
  userPositionReady = true;
  hideGeoToast();
  updateUserMarker(position);
  computeNearbyStations();
  syncMarkers();

  if (recenter) {
    recenterOnUser();
  }
}

function onUserPositionError(error, { showToast = false } = {}) {
  if (showToast) {
    setLocateButtonLoading(false);
    showGeoToast(geoErrorMessage(error), { retry: true });
  }
}

function stopUserGeolocation() {
  if (geoWatchId != null) {
    navigator.geolocation.clearWatch(geoWatchId);
    geoWatchId = null;
  }
}

function startUserGeolocation({ recenterOnReady = false, showErrors = false } = {}) {
  if (!isGeolocationSupported()) {
    if (showErrors || recenterOnReady) {
      showGeoToast("Votre navigateur ne prend pas en charge la géolocalisation.", { retry: false });
    }
    return;
  }

  if (!isSecureContextForGeo()) {
    if (showErrors || recenterOnReady) {
      showGeoToast(
        "La géolocalisation nécessite HTTPS ou l'accès via localhost / 127.0.0.1.",
        { retry: false }
      );
    }
    return;
  }

  stopUserGeolocation();

  geoWatchId = navigator.geolocation.watchPosition(
    (position) => onUserPositionUpdate(position, { recenter: recenterOnReady && !userPositionReady }),
    (error) => onUserPositionError(error, { showToast: showErrors || recenterOnReady }),
    GEO_WATCH_OPTIONS
  );
}

function flyToUserPosition() {
  if (!userCoords || !map) return;

  map.flyTo(userCoords, USER_LOCATE_ZOOM, {
    duration: 0.85,
    easeLinearity: 0.22,
    animate: true,
  });
}

function clearUserPopupTimer() {
  if (userPopupTimer != null) {
    clearTimeout(userPopupTimer);
    userPopupTimer = null;
  }
}

function openUserHerePopup() {
  if (!userMarker) return;

  clearUserPopupTimer();
  userMarker.openPopup();

  userPopupTimer = setTimeout(() => {
    if (userMarker?.isPopupOpen()) {
      userMarker.closePopup();
    }
    userPopupTimer = null;
  }, USER_POPUP_AUTO_CLOSE_MS);
}

function bindUserMarkerEvents(marker) {
  marker.on("popupclose", clearUserPopupTimer);
}

function recenterOnUser() {
  if (!userCoords) return;

  computeNearbyStations();
  syncMarkers();
  flyToUserPosition();

  map.once("moveend", () => {
    openUserHerePopup();
    openNearbyPanel();

    const hiddenNearby = nearbyStationsInfo.filter(
      (n) => !filteredStations().some((s) => s.id === n.station.id)
    );
    if (hiddenNearby.length && nearbyStationsInfo.length) {
      showGeoToast(
        `${hiddenNearby.length} station${hiddenNearby.length > 1 ? "s" : ""} proche${hiddenNearby.length > 1 ? "s" : ""} masquée${hiddenNearby.length > 1 ? "s" : ""} par le filtre. Sélectionnez « Tous » pour les afficher sur la carte.`,
        { retry: false, variant: "success" }
      );
    }
  });
}

function computeNearbyStations() {
  nearbyStationsInfo = [];
  recommendedStationId = null;

  if (!userCoords || !allStations.length) return [];

  const results = [];

  for (const station of allStations) {
    const coords = stationCoords(station);
    if (!coords) continue;
    const km = haversineKm(userCoords[0], userCoords[1], coords[0], coords[1]);
    if (km <= NEARBY_RADIUS_KM) {
      results.push({
        station,
        distanceKm: km,
        distanceLabel: formatDistance(userCoords[0], userCoords[1], coords[0], coords[1]),
        isRecommended: false,
      });
    }
  }

  results.sort((a, b) => a.distanceKm - b.distanceKm);

  if (results.length) {
    results[0].isRecommended = true;
    recommendedStationId = results[0].station.id;
  }

  nearbyStationsInfo = results;
  return results;
}

function centerMapOnUserContext() {
  if (!userCoords) return;

  if (nearbyStationsInfo.length) {
    const bounds = L.latLngBounds([userCoords]);
    nearbyStationsInfo.forEach(({ station }) => {
      const coords = stationCoords(station);
      if (coords) bounds.extend(coords);
    });
    map.flyToBounds(bounds.pad(0.18), {
      duration: 0.9,
      easeLinearity: 0.25,
      maxZoom: 15,
      padding: [48, 48],
    });
    return;
  }

  map.flyTo(userCoords, USER_ZOOM, { duration: 0.9, easeLinearity: 0.25 });
}

function stationStatusBadges(station) {
  const statutBadge =
    station.statut === "ouverte"
      ? '<span class="ss-badge ss-badge--green">Ouverte</span>'
      : '<span class="ss-badge ss-badge--gray">Fermée</span>';
  const carburantBadge = station.carburant_disponible
    ? '<span class="ss-badge ss-badge--green">Disponible</span>'
    : '<span class="ss-badge ss-badge--red">Indisponible</span>';
  return { statutBadge, carburantBadge };
}

function buildNearbyStationCard(entry) {
  const { station, distanceLabel, isRecommended } = entry;
  const level = affluenceLevel(station);
  const coords = stationCoords(station);
  const { statutBadge, carburantBadge } = stationStatusBadges(station);
  const hiddenByFilter = !filteredStations().some((s) => s.id === station.id);
  const itineraryUrl = coords ? itineraryUrlForStation(coords) : "#";

  return `
    <article class="ss-nearby-card${isRecommended ? " ss-nearby-card--recommended" : ""}" data-station-id="${station.id}">
      <header class="ss-nearby-card__header">
        <span class="ss-map-popup__dot ss-map-popup__dot--${level}" aria-hidden="true"></span>
        <div class="ss-nearby-card__title-wrap">
          <h3 class="ss-nearby-card__title">${escapeHtml(station.nom)}</h3>
          <span class="ss-nearby-card__distance">
            <i class="bi bi-geo-alt" aria-hidden="true"></i> ${escapeHtml(distanceLabel)}
          </span>
        </div>
        ${
          isRecommended
            ? `<span class="ss-badge ss-badge--yellow ss-nearby-card__badge">
                <i class="bi bi-star-fill" aria-hidden="true"></i> Recommandée
              </span>`
            : ""
        }
      </header>
      <div class="ss-nearby-card__meta">
        ${affluenceBadge(level)}
        ${statutBadge}
        ${carburantBadge}
      </div>
      ${
        hiddenByFilter
          ? `<p class="ss-nearby-card__hint">
              <i class="bi bi-funnel" aria-hidden="true"></i> Masquée par le filtre actif
            </p>`
          : ""
      }
      <footer class="ss-nearby-card__actions">
        <a href="/stations/${station.id}/" class="ss-btn ss-btn--primary ss-btn--sm">
          <i class="bi bi-info-circle"></i> Voir les détails
        </a>
        <a href="${itineraryUrl}" target="_blank" rel="noopener" class="ss-btn ss-btn--dark ss-btn--sm">
          <i class="bi bi-signpost-split"></i> Itinéraire
        </a>
      </footer>
    </article>
  `;
}

function openNearbyPanel() {
  if (!panel || !panelContent) return;

  const label = document.querySelector(".ss-side-panel__label");
  const count = nearbyStationsInfo.length;

  if (label) {
    label.textContent = count
      ? `${count} station${count > 1 ? "s" : ""} à proximité`
      : "Stations à proximité";
  }

  if (!count) {
    panelContent.innerHTML = `
      <div class="ss-nearby-panel ss-nearby-panel--empty">
        <div class="ss-nearby-panel__hero">
          <i class="bi bi-geo-alt-fill" aria-hidden="true"></i>
          <h2>Position enregistrée</h2>
          <p>Aucune station trouvée dans un rayon de ${NEARBY_RADIUS_KM} km.</p>
          <p class="ss-nearby-panel__hint">Explorez la carte ou modifiez les filtres pour découvrir d'autres stations.</p>
        </div>
      </div>
    `;
  } else {
    panelContent.innerHTML = `
      <div class="ss-nearby-panel">
        <p class="ss-nearby-panel__summary">
          <strong>${count} station${count > 1 ? "s" : ""} trouvée${count > 1 ? "s" : ""}</strong>
          dans un rayon de ${NEARBY_RADIUS_KM} km · triées par distance
        </p>
        <div class="ss-nearby-panel__list">
          ${nearbyStationsInfo.map(buildNearbyStationCard).join("")}
        </div>
      </div>
    `;
  }

  panel.classList.add("open");
  panel.setAttribute("aria-hidden", "false");
}

function handleNearbyPanelClick(event) {
  const card = event.target.closest(".ss-nearby-card");
  if (!card || event.target.closest("a")) return;

  const stationId = Number(card.dataset.stationId);
  const entry = nearbyStationsInfo.find((n) => n.station.id === stationId);
  if (entry) focusOnStation(entry.station, { openPopup: true });
}

function popupRow(iconClass, label, valueHtml, { iconVariant = "" } = {}) {
  const variantClass = iconVariant ? ` ss-map-popup__row-icon-wrap--${iconVariant}` : "";
  return `
    <div class="ss-map-popup__row">
      <span class="ss-map-popup__row-icon-wrap${variantClass}" aria-hidden="true">
        <i class="bi ${iconClass}"></i>
      </span>
      <div class="ss-map-popup__row-body">
        <span class="ss-map-popup__row-label">${label}</span>
        <span class="ss-map-popup__row-value">${valueHtml}</span>
      </div>
    </div>
  `;
}

function buildPopup(station, { isRecommended = false, distanceLabel = null } = {}) {
  const level = affluenceLevel(station);
  const coords = stationCoords(station);
  if (!coords) return "<p>Coordonnées invalides</p>";

  const meta = parseStationMeta(station);
  const { carburantBadge } = stationStatusBadges(station);

  const recommendedBlock =
    isRecommended && distanceLabel
      ? `<div class="ss-map-popup__nearest">
          <span class="ss-badge ss-badge--yellow">
            <i class="bi bi-star-fill"></i> Recommandée · ${escapeHtml(distanceLabel)}
          </span>
        </div>`
      : distanceLabel
        ? `<div class="ss-map-popup__nearest">
            <span class="ss-badge ss-badge--gray">
              <i class="bi bi-geo-alt"></i> ${escapeHtml(distanceLabel)}
            </span>
          </div>`
        : "";

  const statutValue =
    station.statut === "ouverte"
      ? '<span class="ss-popup-status"><i class="bi bi-circle-fill ss-icon--green"></i> Ouverte</span>'
      : '<span class="ss-popup-status"><i class="bi bi-circle-fill ss-icon--red"></i> Fermée</span>';

  return `
    <article class="ss-map-popup ss-map-popup--rich">
      <header class="ss-map-popup__header">
        <span class="ss-map-popup__dot ss-map-popup__dot--${level}" aria-hidden="true"></span>
        <h3 class="ss-map-popup__title">${escapeHtml(station.nom)}</h3>
      </header>
      <div class="ss-map-popup__body">
        ${recommendedBlock}
        ${popupRow("bi-geo-alt", "Adresse", escapeHtml(meta.adresse))}
        ${popupRow("bi-circle-fill", "Statut", statutValue, {
          iconVariant: station.statut === "ouverte" ? "green" : "red",
        })}
        ${popupRow("bi-fuel-pump", "Carburant", carburantBadge)}
        ${popupRow("bi-car-front-fill", "Véhicules", `<strong>${station.nombre_vehicules}</strong>`)}
        ${popupRow("bi-bar-chart-fill", "Occupation", `<strong>${station.taux_occupation ?? 0}%</strong>`)}
        ${popupRow("bi-speedometer2", "Affluence", affluenceBadge(level))}
        ${popupRow("bi-p-square-fill", "Capacité max", `<strong>${station.capacite_max}</strong> places`)}
        ${popupRow("bi-clock", "Horaires", escapeHtml(meta.horaires))}
        <p class="ss-map-popup__updated">
          <i class="bi bi-arrow-repeat"></i> MAJ : ${escapeHtml(formatUpdatedAt(station.date_mise_a_jour))}
        </p>
      </div>
      <footer class="ss-map-popup__actions">
        <a href="/stations/${station.id}/" class="ss-btn ss-btn--primary ss-btn--sm ss-btn--block">
          <i class="bi bi-info-circle"></i> Voir les détails
        </a>
        <a href="${itineraryUrlForStation(coords)}" target="_blank" rel="noopener" class="ss-btn ss-btn--dark ss-btn--sm ss-btn--block">
          <i class="bi bi-signpost-split"></i> Itinéraire
        </a>
      </footer>
    </article>
  `;
}

function initMap() {
  map = L.map("map", { zoomControl: true }).setView([-4.325, 15.322], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);
  markersLayer.addTo(map);
}

function markerStyleFor(station) {
  const level = affluenceLevel(station);
  const isNearby = isStationNearby(station.id);
  const isRecommended = isStationRecommended(station.id);
  const classNames = [
    "ss-station-marker",
    `ss-station-marker--${level}`,
    "ss-station-marker--live",
  ];
  if (isNearby) classNames.push("ss-station-marker--nearby");
  if (isRecommended) classNames.push("ss-station-marker--recommended");

  return {
    radius: isRecommended ? 15 : isNearby ? 13 : 11,
    fillColor: AFFLUENCE_COLORS[level] || AFFLUENCE_COLORS.faible,
    color: isRecommended ? "#f5b800" : isNearby ? "#1e40af" : "#ffffff",
    weight: isRecommended ? 5 : isNearby ? 4 : 3,
    fillOpacity: 0.95,
    className: classNames.join(" "),
  };
}

function popupMetaForStation(station) {
  const entry = nearbyStationsInfo.find((n) => n.station.id === station.id);
  return {
    isRecommended: Boolean(entry?.isRecommended),
    distanceLabel: entry?.distanceLabel ?? null,
  };
}

function bindMarkerPopup(marker, station) {
  const { isRecommended, distanceLabel } = popupMetaForStation(station);
  marker.bindPopup(buildPopup(station, { isRecommended, distanceLabel }), {
    className: "ss-popup ss-popup--animated",
    maxWidth: 340,
    minWidth: 280,
    closeButton: true,
    autoPanPadding: [24, 24],
  });
}

function createStationMarker(station, animate = false) {
  const coords = stationCoords(station);
  if (!coords) return null;

  const marker = L.circleMarker(coords, markerStyleFor(station));
  bindMarkerPopup(marker, station);
  marker.stationId = station.id;

  if (animate) {
    marker.setStyle({ fillOpacity: 0, opacity: 0 });
    requestAnimationFrame(() => {
      marker.setStyle({ fillOpacity: 0.95, opacity: 1 });
    });
  }

  return marker;
}

function refreshMarker(marker, station) {
  marker.setStyle(markerStyleFor(station));
  const { isRecommended, distanceLabel } = popupMetaForStation(station);
  marker.setPopupContent(buildPopup(station, { isRecommended, distanceLabel }));
}

function updateUserMarker(position) {
  const { latitude, longitude, accuracy } = position.coords;
  userCoords = [latitude, longitude];

  const userPopup = `
    <div class="ss-user-popup">
      <strong>Vous êtes ici</strong>
      ${accuracy ? `<span class="ss-user-popup__meta">Précision ~${Math.round(accuracy)} m</span>` : ""}
    </div>
  `;

  if (!userMarker) {
    userMarker = L.marker(userCoords, {
      icon: createUserLocationIcon(),
      zIndexOffset: 1000,
      interactive: true,
    })
      .addTo(map)
      .bindPopup(userPopup, {
        className: "ss-popup ss-popup--user ss-popup--animated",
        closeButton: true,
        offset: [0, -6],
        autoPan: true,
        autoPanPadding: [24, 24],
      });
    bindUserMarkerEvents(userMarker);
  } else {
    userMarker.setLatLng(userCoords);
    userMarker.setPopupContent(userPopup);
  }

  if (userAccuracyCircle) {
    map.removeLayer(userAccuracyCircle);
    userAccuracyCircle = null;
  }

  if (accuracy && Number.isFinite(accuracy) && accuracy > 0) {
    userAccuracyCircle = L.circle(userCoords, {
      radius: accuracy,
      color: "#3b82f6",
      weight: 1,
      fillColor: "#3b82f6",
      fillOpacity: 0.12,
      interactive: false,
    }).addTo(map);
  }
}

function locateUser() {
  if (isLocating) return;

  if (!isGeolocationSupported()) {
    showGeoToast("Votre navigateur ne prend pas en charge la géolocalisation.", { retry: false });
    return;
  }

  if (!isSecureContextForGeo()) {
    showGeoToast(
      "La géolocalisation nécessite HTTPS ou l'accès via localhost / 127.0.0.1.",
      { retry: false }
    );
    return;
  }

  if (userCoords && userPositionReady) {
    recenterOnUser();
    return;
  }

  setLocateButtonLoading(true);

  navigator.geolocation.getCurrentPosition(
    (position) => {
      setLocateButtonLoading(false);
      onUserPositionUpdate(position, { recenter: true });
    },
    (error) => {
      setLocateButtonLoading(false);
      showGeoToast(geoErrorMessage(error), { retry: true });
    },
    GEO_OPTIONS
  );
}

function filteredStations() {
  return allStations.filter((s) => !activeFilter || s.niveau_affluence === activeFilter);
}

function fitMapToVisibleStations({ maxZoom = 13, force = false } = {}) {
  const stations = filteredStations();
  const coords = stations.map(stationCoords).filter(Boolean);
  if (!coords.length) return;
  map.fitBounds(L.latLngBounds(coords).pad(0.12), { maxZoom, animate: force });
}

function focusOnStation(station, { openPopup = true } = {}) {
  const coords = stationCoords(station);
  if (!coords) return;
  hideSearchSuggestions();
  map.flyTo(coords, 15, { duration: 0.7 });
  if (!openPopup) return;
  const marker = markerRegistry.get(station.id);
  if (marker) {
    setTimeout(() => marker.openPopup(), 450);
  } else {
    showGeoToast(
      `Station « ${station.nom} » masquée par le filtre actif. Sélectionnez « Tous » pour l'afficher.`,
      { retry: false, variant: "success" }
    );
  }
}

function syncMarkers() {
  const stations = filteredStations();
  const visibleIds = new Set(stations.map((s) => s.id));

  for (const [id, marker] of [...markerRegistry.entries()]) {
    if (!visibleIds.has(id)) {
      markersLayer.removeLayer(marker);
      markerRegistry.delete(id);
      stationSignatures.delete(id);
    }
  }

  stations.forEach((station, index) => {
    const sig = stationSignature(station);
    const existing = markerRegistry.get(station.id);

    if (existing) {
      if (stationSignatures.get(station.id) !== sig) {
        refreshMarker(existing, station);
        stationSignatures.set(station.id, sig);
        existing.getElement()?.classList.add("ss-marker-updated");
        setTimeout(() => existing.getElement()?.classList.remove("ss-marker-updated"), 600);
      }
    } else {
      const marker = createStationMarker(station, true);
      if (!marker) return;
      markersLayer.addLayer(marker);
      markerRegistry.set(station.id, marker);
      stationSignatures.set(station.id, sig);
    }
  });
}

async function fetchStations() {
  try {
    const res = await fetch("/api/stations/", {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
    if (!res.ok) throw new Error(`API error ${res.status}`);

    allStations = normalizeStations(await res.json());

    if (userCoords) computeNearbyStations();

    syncMarkers();

    if (panel?.classList.contains("open") && userCoords) {
      openNearbyPanel();
    }

    if (!initialFitDone && allStations.length && !userCoords) {
      fitMapToVisibleStations();
      initialFitDone = true;
    }
  } catch (e) {
    console.error("Impossible de charger les stations:", e);
  }
}

function refreshMapLayout() {
  map?.invalidateSize();
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(fetchStations, REFRESH_MS);
}

document.addEventListener("DOMContentLoaded", () => {
  initMap();

  map.whenReady(() => {
    refreshMapLayout();
    fetchStations();
    startAutoRefresh();
    startUserGeolocation();
    setTimeout(refreshMapLayout, 100);
  });

  document.getElementById("btn-locate")?.addEventListener("click", locateUser);
  document.getElementById("panel-close")?.addEventListener("click", () => {
    panel?.classList.remove("open");
    panel?.setAttribute("aria-hidden", "true");
  });

  panelContent?.addEventListener("click", handleNearbyPanelClick);

  document.getElementById("filter-affluence-group")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-niveau]");
    if (!btn) return;

    document
      .querySelectorAll("#filter-affluence-group .ss-filter-pill")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeFilter = btn.dataset.niveau || "";
    syncMarkers();
    fitMapToVisibleStations({ maxZoom: 14, force: true });
  });

  let searchTimer;
  searchInput?.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(handleSearchInput, 180);
  });

  searchInput?.addEventListener("keydown", handleSearchKeydown);

  searchInput?.addEventListener("focus", () => {
    if ((searchInput.value.trim().length ?? 0) >= SEARCH_MIN_CHARS) {
      handleSearchInput();
    }
  });

  searchSuggestions?.addEventListener("mousedown", (e) => e.preventDefault());
  searchSuggestions?.addEventListener("click", handleSearchSuggestionClick);

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".ss-search-wrap")) hideSearchSuggestions();
  });

  window.addEventListener("resize", refreshMapLayout);
  window.addEventListener("beforeunload", stopUserGeolocation);
});
