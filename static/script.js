/**
 * GreenRoute - Client-side Interactive Logic
 * 
 * Frontend Engineer: This file is linked across the admin dashboard and login templates.
 * Place custom interactive components, dashboard graph refreshers, and client-side
 * validation logic here.
 */

// Test variable to verify script is loading
window.greenRouteLoaded = true;

// Global search function to make location search work
window.searchLocation = async function(query, suggestionsElement) {
    if (query.length < 2) {
        suggestionsElement.innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/search-location/?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.status === 'success' && data.results.length > 0) {
            suggestionsElement.innerHTML = data.results
                .map((result, index) => `
                    <div class="suggestion-item" data-index="${index}" data-lat="${result.lat}" data-lng="${result.lng}" data-name="${result.name}">
                        <i class="fa-solid fa-map-pin"></i> ${result.name}
                    </div>
                `)
                .join('');
        } else if (data.status === 'error') {
            suggestionsElement.innerHTML = `<div class="suggestion-item disabled">${data.message}</div>`;
        } else {
            suggestionsElement.innerHTML = '<div class="suggestion-item disabled">No results found</div>';
        }
    } catch (error) {
        console.error('Location search error:', error);
        suggestionsElement.innerHTML = '<div class="suggestion-item disabled">Search error</div>';
    }
};

console.log('GreenRoute script initialized. searchLocation:', typeof window.searchLocation);

document.addEventListener('DOMContentLoaded', () => {
    // Initialization logic
    console.log("GreenRoute Client-side scripts loaded successfully.");
});


// GreenRoute - Public Dashboard Map Logic
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize map if we are on the dashboard (where #eco-map exists)
    const mapElement = document.getElementById('eco-map');
    if (!mapElement) return;

    // Initialize Leaflet map centered on Nairobi
    const map = L.map('eco-map').setView([-1.2921, 36.8219], 13);

    // Add Dark Mode CartoDB Map Tiles for that sleek "Eco-Routing" aesthetic
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    let currentRouteLine = null;
    let startMarker = null;
    let endMarker = null;
    let selectedStart = null;
    let selectedEnd = null;

    // Debounce function to prevent rate-limiting from Nominatim API
    function debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }

    const debouncedSearchLocation = debounce((query, element) => {
        searchLocation(query, element);
    }, 500);

    // Start location search with autocomplete
    const startInput = document.getElementById('start-location-input');
    const startSuggestions = document.getElementById('start-suggestions');
    
    if (startInput) {
        startInput.addEventListener('input', (e) => {
            debouncedSearchLocation(e.target.value, startSuggestions);
        });
    }

    startSuggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.suggestion-item');
        if (item && !item.classList.contains('disabled')) {
            const lat = parseFloat(item.dataset.lat);
            const lng = parseFloat(item.dataset.lng);
            const name = item.dataset.name;

            selectedStart = { lat, lng, name };
            startInput.value = name;
            startSuggestions.innerHTML = '';

            // Place marker on map
            if (startMarker) map.removeLayer(startMarker);
            startMarker = L.marker([lat, lng], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            })
            .bindPopup(`<b>Start:</b> ${name}`)
            .addTo(map);

            // Update hidden fields
            document.getElementById('start-lat').value = lat;
            document.getElementById('start-lng').value = lng;
        }
    });

    // Geolocation - "Locate Me" Button
    const locateBtn = document.getElementById('locate-me-btn');
    if (locateBtn) {
        locateBtn.addEventListener('click', () => {
            if (navigator.geolocation) {
                // visual feedback
                locateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                
                navigator.geolocation.getCurrentPosition(
                    async (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        let name = "Current Location";

                        // Reverse geocoding to get actual place name
                        try {
                            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`);
                            const data = await response.json();
                            if (data && data.display_name) {
                                // Simplify name to just the first few components
                                const parts = data.display_name.split(',').map(s => s.trim());
                                name = parts.slice(0, 3).join(', ');
                            }
                        } catch (err) {
                            console.error("Reverse geocoding failed", err);
                        }

                        selectedStart = { lat, lng, name };
                        startInput.value = name;
                        startSuggestions.innerHTML = '';

                        // Place marker on map
                        if (startMarker) map.removeLayer(startMarker);
                        startMarker = L.marker([lat, lng], {
                            icon: L.icon({
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                iconSize: [25, 41],
                                iconAnchor: [12, 41],
                                popupAnchor: [1, -34],
                                shadowSize: [41, 41]
                            })
                        })
                        .bindPopup(`<b>Start:</b> ${name}`)
                        .addTo(map);

                        // Center map on user
                        map.setView([lat, lng], 15);

                        // Update hidden fields
                        document.getElementById('start-lat').value = lat;
                        document.getElementById('start-lng').value = lng;

                        // restore icon
                        locateBtn.innerHTML = '<i class="fa-solid fa-crosshairs"></i>';
                    },
                    (error) => {
                        console.error("Geolocation error:", error);
                        alert("Could not detect current location. Please check your browser permissions.");
                        locateBtn.innerHTML = '<i class="fa-solid fa-crosshairs"></i>';
                    },
                    { enableHighAccuracy: true, timeout: 5000 }
                );
            } else {
                alert("Geolocation is not supported by this browser.");
            }
        });
    }

    // End location search with autocomplete
    const endInput = document.getElementById('end-location-input');
    const endSuggestions = document.getElementById('end-suggestions');
    
    endInput.addEventListener('input', (e) => {
        debouncedSearchLocation(e.target.value, endSuggestions);
    });

    endSuggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.suggestion-item');
        if (item && !item.classList.contains('disabled')) {
            const lat = parseFloat(item.dataset.lat);
            const lng = parseFloat(item.dataset.lng);
            const name = item.dataset.name;

            selectedEnd = { lat, lng, name };
            endInput.value = name;
            endSuggestions.innerHTML = '';

            // Place marker on map
            if (endMarker) map.removeLayer(endMarker);
            endMarker = L.marker([lat, lng], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            })
            .bindPopup(`<b>Destination:</b> ${name}`)
            .addTo(map);

            // Update hidden fields
            document.getElementById('end-lat').value = lat;
            document.getElementById('end-lng').value = lng;
        }
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        const routeForm = document.getElementById('route-form');
        if (!routeForm.contains(e.target)) {
            startSuggestions.innerHTML = '';
            endSuggestions.innerHTML = '';
        }
    });

    // Handle Route Form Submission
    const routeForm = document.getElementById('route-form');
    routeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!selectedStart || !selectedEnd) {
            alert('Please select both start and end locations from the suggestions.');
            return;
        }
        
        const btn = document.getElementById('btn-calc');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Calculating...';
        btn.disabled = true;

        const startLng = selectedStart.lng;
        const startLat = selectedStart.lat;
        const endLng = selectedEnd.lng;
        const endLat = selectedEnd.lat;

        try {
            // Hit the Django API
            const response = await fetch(`/api/route/?start_lat=${startLat}&start_lng=${startLng}&end_lat=${endLat}&end_lng=${endLng}&start_location=${encodeURIComponent(selectedStart.name)}&end_location=${encodeURIComponent(selectedEnd.name)}`);
            const data = await response.json();

            if (data.status === 'success') {
                // Clear existing route if it exists
                if (currentRouteLine) {
                    map.removeLayer(currentRouteLine);
                }

                // Extract coordinates for Leaflet (needs [lat, lng])
                const latLngs = data.path.map(pt => [pt.lat, pt.lng]);
                
                // Draw new polyline with vibrant green glow
                currentRouteLine = L.polyline(latLngs, {
                    color: '#10B981', // var(--primary-color)
                    weight: 5,
                    opacity: 0.8,
                    lineCap: 'round',
                    lineJoin: 'round'
                }).addTo(map);

                // Zoom map to fit the generated route exactly
                map.fitBounds(currentRouteLine.getBounds(), { padding: [50, 50] });

                // Update UI Metrics with distance and emissions
                document.getElementById('eco-metrics').classList.remove('hidden');
                
                // Display distance and emissions prevented
                const metricsHtml = `
                    <div class="metric-row">
                        <div class="metric">
                            <span class="metric-label">Distance</span>
                            <strong class="metric-value">${data.distance_km} km</strong>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Fuel Saved</span>
                            <strong class="metric-value">${data.fuel_saved_liters} L</strong>
                        </div>
                    </div>
                    <div class="metric-row">
                        <div class="metric">
                            <span class="metric-label">CO₂ Prevented</span>
                            <strong class="metric-value">${data.co2_prevented_kg} kg</strong>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Status</span>
                            <strong class="metric-value success">Optimized</strong>
                        </div>
                    </div>
                `;
                document.querySelector('.eco-metrics-card').innerHTML = `<h3>Route Analysis</h3>${metricsHtml}<div class="eco-impact"><i class="fa-solid fa-seedling"></i><span>Estimated Eco-Savings active!</span></div>`;
            } else {
                alert('Routing Error: ' + data.message);
            }
        } catch (error) {
            console.error(error);
            alert('Failed to connect to the routing engine.');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
});
