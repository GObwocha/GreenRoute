/**
 * GreenRoute - Client-side Interactive Logic
 * 
 * Frontend Engineer: This file is linked across the admin dashboard and login templates.
 * Place custom interactive components, dashboard graph refreshers, and client-side
 * validation logic here.
 */

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

    // Handle Route Form Submission
    const routeForm = document.getElementById('route-form');
    routeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const btn = document.getElementById('btn-calc');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Calculating...';
        btn.disabled = true;

        const startLng = document.getElementById('start-lng').value;
        const startLat = document.getElementById('start-lat').value;
        const endLng = document.getElementById('end-lng').value;
        const endLat = document.getElementById('end-lat').value;

        try {
            // Hit the Django API
            const response = await fetch(`/api/route/?start_lat=${startLat}&start_lng=${startLng}&end_lat=${endLat}&end_lng=${endLng}`);
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

                // Update UI Metrics
                document.getElementById('eco-metrics').classList.remove('hidden');
                document.getElementById('metric-nodes').innerText = data.path.length;
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
