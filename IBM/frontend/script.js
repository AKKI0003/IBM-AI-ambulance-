// script.js

let map;
let userMarker;
let hospitalMarkers = [];
let hospitalsGlobal = [];
let directionsRenderer;
let currentUserLocation = null;

// --- MAP STYLES ---
const lightMapStyles = []; // An empty array means Google's default map style
const darkMapStyles = [
    { elementType: "geometry", stylers: [{ color: "#242f3e" }] }, { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] }, { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] }, { featureType: "administrative.locality", elementType: "labels.text.fill", stylers: [{ color: "#d59563" }] }, { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#d59563" }] }, { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#263c3f" }] }, { featureType: "poi.park", elementType: "labels.text.fill", stylers: [{ color: "#6b9a76" }] }, { featureType: "road", elementType: "geometry", stylers: [{ color: "#38414e" }] }, { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#212a37" }] }, { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#9ca5b3" }] }, { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#746855" }] }, { featureType: "road.highway", elementType: "geometry.stroke", stylers: [{ color: "#1f2835" }] }, { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#f3d19c" }] }, { featureType: "transit", elementType: "geometry", stylers: [{ color: "#2f3948" }] }, { featureType: "transit.station", elementType: "labels.text.fill", stylers: [{ color: "#d59563" }] }, { featureType: "water", elementType: "geometry", stylers: [{ color: "#17263c" }] }, { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#515c6d" }] }, { featureType: "water", elementType: "labels.text.stroke", stylers: [{ color: "#17263c" }] }
];

// --- NEW THEME TOGGLE FUNCTION ---
function toggleTheme() {
    const themeStylesheet = document.getElementById('theme-stylesheet');
    const toggleButton = document.getElementById('theme-toggle-btn');
    const currentTheme = themeStylesheet.href.includes('style.css') ? 'dark' : 'light';

    if (currentTheme === 'dark') {
        // Switch to light mode
        themeStylesheet.href = 'style1.css';
        localStorage.setItem('theme', 'light');
        if (map) map.setOptions({ styles: lightMapStyles });
        toggleButton.innerHTML = '🌙'; // Moon icon for switching to dark mode
    } else {
        // Switch to dark mode
        themeStylesheet.href = 'style.css';
        localStorage.setItem('theme', 'dark');
        if (map) map.setOptions({ styles: darkMapStyles });
        toggleButton.innerHTML = '☀️'; // Sun icon for switching to light mode
    }
}


// 1️⃣ Get User Location (Entry Point)
function getUserLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        currentUserLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        initMap(currentUserLocation);
        fetchHospitals(currentUserLocation);
      },
      () => alert("Failed to fetch your location. Please enable location services.")
    );
  } else {
    alert("Geolocation is not supported by this browser.");
  }
}

// 2️⃣ Initialize Google Map
// script.js

// 2️⃣ Initialize Google Map
// script.js

// 2️⃣ Initialize Google Map
function initMap(center) {
    const isDarkMode = (localStorage.getItem('theme') || 'dark') === 'dark';
    
    map = new google.maps.Map(document.getElementById("map"), {
        center,
        zoom: 14,
        styles: isDarkMode ? darkMapStyles : lightMapStyles,
        disableDefaultUI: true,
        zoomControl: true,
    });

    userMarker = new google.maps.Marker({
        position: center,
        map,
        title: "Patient Location",
        // This 'icon' object makes the pin a distinct blue circle
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: "#4285F4", // A standard blue color
            fillOpacity: 1,
            strokeWeight: 2,
            strokeColor: "white"
        }
    });

    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: true,
        polylineOptions: {
            strokeColor: isDarkMode ? "#00c2d1" : "#0d6efd",
            strokeWeight: 6,
            strokeOpacity: 0.8,
        },
    });
    directionsRenderer.setMap(map);
    
    document.getElementById('theme-toggle-btn').innerHTML = isDarkMode ? '☀️' : '🌙';
}

// 3️⃣ Fetch Hospitals from Flask Backend
function fetchHospitals(userLocation) {
  fetch("http://127.0.0.1:5000/api/search_hospitals", {
    method: "POST", headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      if (!Array.isArray(data)) { alert("Error: Unexpected data format from server."); return; }
      hospitalsGlobal = data.map((hospital) => {
        const distance = getDistance(userLocation.lat, userLocation.lng, hospital.latitude, hospital.longitude);
        return { ...hospital, distance };
      });
      applyFilters();
    })
    .catch((err) => {
      console.error("Error fetching hospital data:", err);
      alert("Failed to load hospitals from the server.");
    });
}

// 4️⃣ Filter and Sort Logic
function applyFilters() {
    if (!currentUserLocation) { alert("Please click the 'Use My Current Location' button first."); return; }
    const threatLevel = document.getElementById("threatLevel").value;
    const sortBy = document.getElementById("sortBy").value;
    let finalList = [...hospitalsGlobal];

    if (threatLevel === "high") {
        finalList = finalList.filter((h) => h.bed_availability.critical_vent > 0 || h.bed_availability.critical_no_vent > 0);
    } else if (threatLevel === "medium") {
        finalList = finalList.filter((h) => h.bed_availability.non_critical > 0);
    }

    if (sortBy === "distance") {
        finalList.sort((a, b) => a.distance - b.distance);
    } else if (sortBy === "beds") {
        finalList.sort((a, b) => b.bed_availability.total - a.bed_availability.total);
    } else if (sortBy === "wait") {
        finalList.sort((a, b) => a.estimated_wait_time - a.estimated_wait_time);
    }

    if (finalList.length === 0) {
        document.getElementById("hospitals").innerHTML = `<p class="text-center p-3">No hospitals found matching the selected criteria.</p>`;
        hospitalMarkers.forEach((marker) => marker.setMap(null));
        hospitalMarkers = [];
        return;
    }
    renderHospitals(finalList);
    drawRoute(finalList[0], currentUserLocation);
}

// 5️⃣ Render Hospital Cards
function renderHospitals(hospitals) {
  const container = document.getElementById("hospitals");
  container.innerHTML = "";
  hospitalMarkers.forEach((marker) => marker.setMap(null));
  hospitalMarkers = [];

  hospitals.forEach((h) => {
    const div = document.createElement("div");
    div.className = "hospital-card";
    div.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <h5 style="cursor: pointer; color: #0d6efd; margin-bottom: 0;" onclick="updateRoute(${h.latitude}, ${h.longitude})">
          ${h.name}
        </h5>
        <button class="btn btn-primary btn-sm" onclick="startNavigation(${h.latitude}, ${h.longitude})">
          Navigate
        </button>
      </div>
      <hr class="my-2">
      <p>
         <strong>Beds Available:</strong> ${h.bed_availability.total} |
         <strong>Wait Time:</strong> ${h.estimated_wait_time} mins |
         <strong>Distance:</strong> ${h.distance.toFixed(2)} km
      </p>
      <p><strong>Address:</strong> ${h.address}</p>
    `;
    container.appendChild(div);

    const marker = new google.maps.Marker({
      position: { lat: h.latitude, lng: h.longitude },
      map,
      title: h.name,
    });
    hospitalMarkers.push(marker);
  });
}

// 6️⃣ Draw Route to a Selected Hospital
function drawRoute(hospital, origin) {
  const directionsService = new google.maps.DirectionsService();
  directionsService.route({
      origin: origin,
      destination: { lat: hospital.latitude, lng: hospital.longitude },
      travelMode: google.maps.TravelMode.DRIVING,
    }, (response, status) => {
      if (status === "OK") {
        directionsRenderer.setDirections(response);
        document.getElementById("map").scrollIntoView({ behavior: "smooth" });
      } else {
        console.warn("Route failed:", status);
      }
    }
  );
}

// 7️⃣ Update route when a hospital name is clicked
function updateRoute(lat, lng) {
  if (!currentUserLocation) return; 
  const selectedHospital = { latitude: lat, longitude: lng };
  drawRoute(selectedHospital, currentUserLocation);
}

// 8️⃣ Open Google Maps for navigation
function startNavigation(lat, lng) {
    if (!currentUserLocation) {
        alert("Please set your location first before starting navigation.");
        return;
    }
    const destination = `${lat},${lng}`;
    const origin = `${currentUserLocation.lat},${currentUserLocation.lng}`;
    const navUrl = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving`;
    window.open(navUrl, '_blank');
}

// 9️⃣ Distance Calculation
function getDistance(lat1, lon1, lat2, lon2) {
  const toRad = (x) => (x * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
