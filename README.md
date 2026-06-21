# 🌿 GreenRoute

**GreenRoute** is an eco-routing engine for Nairobi, Kenya that calculates the most fuel-efficient driving route between two points — not just the shortest or fastest one. It factors in road elevation/grade, surface type, live traffic, and admin-defined road closures to estimate real fuel and CO₂ savings for every trip.

The project is built on Django, with a custom routing layer powered by [OSMnx](https://osmnx.readthedocs.io/) and [NetworkX](https://networkx.org/), and ships with both a public client dashboard and an internal admin panel for managing the system.

## ✨ Key Features

- **Eco-weighted A\* routing** — Roads are scored with a custom `eco_weight` (uphill/downhill grade penalties, surface type, traffic, and restricted-access penalties) instead of raw distance, then routed with an A* search guided by a Pythagorean heuristic.
- **Bounding-box subgraphing** — Instead of searching the entire Nairobi road graph on every request, the engine slices out a small subgraph around the start/end points so routes resolve in milliseconds.
- **Live traffic awareness** — Optional integration with the TomTom Traffic Incidents API to penalize roads currently affected by jams.
- **Fuel & CO₂ savings estimates** — Each route returns estimated liters of fuel and kg of CO₂ saved versus a standard route, with support for custom vehicle fuel economy and fuel price.
- **Location search** — Place-name search powered by the Photon (OpenStreetMap) geocoding API.
- **Client portal** — Public eco-route planner, login, route history (with CSV export), and a chat channel to message admins.
- **Admin panel** — Dashboard, user management, route history/analytics, live road modifiers (closures/traffic zones), system-wide routing parameters, and an in-app technical docs page.
- **M-Pesa ready** — Ships with `django-daraja` installed for future M-Pesa payment integration.

## 🏗️ How It Works

1. **Map preparation** (`build_map.py`, run once / offline): Downloads the Nairobi drivable road network via OSMnx, enriches it with elevation data, calculates an `eco_weight` per road segment based on grade, and saves the result as `nairobi_eco_map.graphml`.
2. **App boot** (`main/apps.py`): The pre-compiled `.graphml` file is loaded into memory once when the Django app starts, so requests never re-download or re-process the map.
3. **Per-request routing** (`main/views.py → calculate_route`):
   - Snaps the requested start/end coordinates to the nearest road nodes.
   - Carves out a small bounding-box subgraph around the trip.
   - Applies live traffic penalties (TomTom) and any active admin-defined road modifiers (closures / traffic zones).
   - Runs an A* search over the subgraph using `eco_weight` as the cost function.
   - Returns the path as GPS coordinates plus distance, fuel saved, and CO₂ prevented — and logs the trip to `RouteHistory` for analytics.

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django |
| Routing engine | OSMnx, NetworkX |
| Geospatial | GeoPandas, Shapely, pyproj |
| Frontend | Django Templates, Vanilla JavaScript, Leaflet.js, Font Awesome |
| Database | SQLite |
| Static files | WhiteNoise |
| Deployment | Railway (Gunicorn) |
| Payments (planned) | django-daraja (M-Pesa) |

## 📁 Project Structure

```
GreenRoute/
├── Core/                   # Django project settings, URLs, WSGI/ASGI entrypoints
├── main/                   # Primary app: models, views, URLs, admin
│   ├── models.py           # RouteHistory, SystemSettings, DirectMessage, RoadModifier
│   ├── views.py            # Routing engine, client portal, admin panel logic
│   └── migrations/
├── templates/               # Client + admin HTML templates
├── static/                  # CSS, JS, images
├── build_map.py             # One-time script to generate nairobi_eco_map.graphml
├── debug_route.py           # Standalone script for debugging routing logic
├── nairobi_eco_map.graphml  # Pre-compiled Nairobi road graph (loaded at boot)
├── requirements.txt
└── manage.py
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (recommended)
- pip / virtualenv
- A pre-built `nairobi_eco_map.graphml` (included in the repo) or the ability to run `build_map.py` to generate your own

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/GObwocha/GreenRoute.git
cd GreenRoute

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env with your own values

# 5. Apply database migrations
python manage.py migrate

# 6. Create an admin user
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

The client dashboard will be available at `http://127.0.0.1:8000/`, and the admin panel at `http://127.0.0.1:8000/admin-panel/`.

### Environment Variables

Defined in `.env` (see `.env.example`):

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` — set `False` in production |
| `TOMTOM_API_KEY` | API key from [TomTom Developer Portal](https://developer.tomtom.com/) for live traffic data (optional — routing falls back gracefully without it) |

### Regenerating the Road Map (optional)

The repo ships with a pre-compiled `nairobi_eco_map.graphml`. If you need to rebuild it (e.g. to refresh OSM data or adjust elevation penalties):

```bash
python build_map.py
```

This downloads the Nairobi drive network, fetches elevation data, computes `eco_weight` per edge, and writes a new `nairobi_eco_map.graphml`. It can take 15+ minutes due to the elevation API calls.

## 📡 API Reference

### `GET /api/route/`

Calculates the most fuel-efficient route between two coordinates.

**Parameters**

| Param | Type | Required | Description |
|---|---|---|---|
| `start_lat`, `start_lng` | float | ✅ | Starting coordinates |
| `end_lat`, `end_lng` | float | ✅ | Destination coordinates |
| `custom_fuel_economy` | float | ❌ | Override vehicle fuel consumption (L/100km) |
| `custom_fuel_price` | float | ❌ | Fuel price per liter, used to estimate cost saved |
| `start_location`, `end_location` | string | ❌ | Human-readable place names, stored with the route history |

**Example**

```
GET /api/route/?start_lat=-1.288&start_lng=36.785&end_lat=-1.295&end_lng=36.795
```

```json
{
  "status": "success",
  "traffic_data_applied": false,
  "path": [
    {"lat": -1.2880124, "lng": 36.7850221},
    {"lat": -1.2881589, "lng": 36.7853045}
  ],
  "distance_km": 1.42,
  "nodes_traversed": 18,
  "fuel_saved_liters": 0.02,
  "co2_prevented_kg": 0.05
}
```

**Error Response (400)**

```json
{
  "status": "error",
  "message": "No drivable route exists between these two points on the current map."
}
```

### `GET /api/search-location/`

Searches for a place by name (scoped to Nairobi) via the Photon geocoding API.

| Param | Type | Required | Description |
|---|---|---|---|
| `query` | string | ✅ | Place name, minimum 2 characters |

```
GET /api/search-location/?query=Thika
```

```json
{
  "status": "success",
  "results": [
    {"name": "Thika, Kiambu, Kenya", "lat": -1.0396, "lng": 37.0900, "type": "city"}
  ]
}
```

## 👥 Contributing

This project follows a strict **feature-branch workflow** — no one (including the repo owner) commits directly to `main`.

1. Accept the GitHub collaborator invite, then clone the repo.
2. Create a branch from inside the cloned folder: `git checkout -b feature/your-feature-name`
3. Commit your work: `git add . && git commit -m "Description of change"`
4. Push your branch: `git push -u origin feature/your-feature-name`
5. Open a Pull Request on GitHub for review before merging into `main`.
6. Keep your branch up to date with `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/your-feature-name
   git merge main
   ```

## 📄 License

No license file is currently specified in this repository.
