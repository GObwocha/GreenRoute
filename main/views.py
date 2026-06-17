from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
import secrets
#Libraries for the routing engine
from django.http import JsonResponse
from .apps import MainConfig
from .models import RouteHistory
import networkx as nx
import osmnx as ox
import requests
from math import radians, cos, sin, asin, sqrt

# Create your views here.
def client_dashboard(request):
    # This view serves the public interactive Eco-Planner dashboard
    return render(request, 'client_dashboard.html')

def haversine_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def calculate_distance_from_path(path_coords):
    """
    Sum up the distances between consecutive points in a path.
    Returns distance in kilometers.
    """
    if len(path_coords) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(len(path_coords) - 1):
        lat1, lng1 = path_coords[i]['lat'], path_coords[i]['lng']
        lat2, lng2 = path_coords[i+1]['lat'], path_coords[i+1]['lng']
        total_distance += haversine_distance(lat1, lng1, lat2, lng2)
    
    return total_distance

TOMTOM_API_KEY = "BjZuNCQClsYUuPtHAPxKXSyzXSaQeQMS"

def get_live_traffic_penalties(bbox):
    """
    Calls TomTom once to get all traffic jams in the bounding box.
    Returns a list of coordinates where traffic is heavy.
    """
    min_lng, min_lat, max_lng, max_lat = bbox
    
    # TomTom Incident API endpoint
    url = f"https://api.tomtom.com/traffic/services/5/incidentDetails?key={TOMTOM_API_KEY}&bbox={min_lng},{min_lat},{max_lng},{max_lat}&fields={'{incidents{geometry{type,coordinates}}}'}"
    
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        
        jam_coordinates = []
        if 'incidents' in data:
            for incident in data['incidents']:
                # Extract the line of coordinates where the jam is happening
                for coord in incident['geometry']['coordinates']:
                    jam_coordinates.append((coord[1], coord[0])) # Store as (lat, lng)
        return jam_coordinates
    except Exception as e:
        print(f"Traffic API failed: {e}. Defaulting to standard route.")
        return [] # If TomTom fails, return no jams so the app doesn't crash

def search_location(request):
    """
    Search for a location by place name using Nominatim (OpenStreetMap).
    Returns the top 5 results with coordinates and display name.
    
    Required Parameters:
    - query (string): Place name to search for (e.g., "Thika", "Nairobi CBD")
    """
    query = request.GET.get('query', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            "status": "error",
            "message": "Query must be at least 2 characters long."
        }, status=400)
    
    try:
        # Photon API endpoint (Nominatim alternative, no strict rate limits)
        url = "https://photon.komoot.io/api/"
        params = {
            'q': f"{query}, Nairobi, Kenya",
            'limit': 5
        }
        
        headers = {
            'User-Agent': 'GreenRoute-EcoRouter/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('features', [])
        
        if not results:
            return JsonResponse({
                "status": "success",
                "results": [],
                "message": f"No results found for '{query}' in Nairobi"
            })
        
        # Format results for frontend
        formatted_results = []
        for result in results:
            props = result.get('properties', {})
            geom = result.get('geometry', {})
            coords = geom.get('coordinates', [0, 0])
            
            # Format display name
            name_parts = []
            if props.get('name'): name_parts.append(props.get('name'))
            if props.get('street'): name_parts.append(props.get('street'))
            if props.get('district'): name_parts.append(props.get('district'))
            if props.get('city'): name_parts.append(props.get('city'))
            
            display_name = ", ".join(name_parts) if name_parts else query
            
            formatted_results.append({
                "name": display_name,
                "lat": float(coords[1]),
                "lng": float(coords[0]),
                "type": props.get('osm_value', 'unknown')
            })
        
        return JsonResponse({
            "status": "success",
            "results": formatted_results
        })
    
    except requests.Timeout:
        return JsonResponse({
            "status": "error",
            "message": "Location search timed out. Please try again."
        }, status=504)
    
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Location search failed: {str(e)}"
        }, status=500)

def calculate_route(request):
    #1. Safely grab data from URL
    start_lat_raw = request.GET.get('start_lat')
    start_lng_raw = request.GET.get('start_lng')
    end_lat_raw = request.GET.get('end_lat')
    end_lng_raw = request.GET.get('end_lng')

    #ERROR CHECK 1:Did frontend forget a parameter?
    if not all([start_lat_raw, start_lng_raw, end_lat_raw, end_lng_raw]):
        return JsonResponse({
            "status": "error",
            "message": "Missing parameters. Please provide start_lat, start_lng, end_lat and end_lng."
        }, status=400)
    
    #ERROR CHECK 2: Are the corrdinates actual numbers?
    try:
        start_lat = float(start_lat_raw)
        start_lng = float(start_lng_raw)
        end_lat = float(end_lat_raw)
        end_lng = float(end_lng_raw)
    except ValueError:
        return JsonResponse({
            "status": "error",
            "message": "Invlaid coordinates. All parameters must be valid decimal numbers."
        }, status=400)
    
    #Make sure the map is successfully laoded during server boot
    graph = MainConfig.nairobi_graph
    if graph is None:
        return JsonResponse({
            "status": "error",
            "message": "The routing engine is offline or still booting up."
        }, status=503)
    
    # 3. The Math Engine (Now with A*, Subgraphing, and Selective Updates!)
    import time
    try:
        def debug_log(msg):
            with open('route_debug.log', 'a') as f:
                f.write(f"{time.time()}: {msg}\n")
                
        t0 = time.time()
        debug_log("[API] Route calculation started")
        
        # Snap the GPS coordinates to the nearest physical road
        orig_node = ox.distance.nearest_nodes(graph, start_lng, start_lat)
        dest_node = ox.distance.nearest_nodes(graph, end_lng, end_lat)
        debug_log(f"[API] Nearest nodes found in {time.time()-t0:.2f}s")

        # --- OPTIMIZATION 1: Bounding Box Subgraphing ---
        # Instead of copying the entire Nairobi map, slice out a tiny rectangle around the route
        t1 = time.time()
        buffer = 0.05  # Roughly a 5km safety margin around the start/end points
        min_lat = min(start_lat, end_lat) - buffer
        max_lat = max(start_lat, end_lat) + buffer
        min_lng = min(start_lng, end_lng) - buffer
        max_lng = max(start_lng, end_lng) + buffer
        
        debug_log(f"[API] bbox: {min_lat}, {max_lat}, {min_lng}, {max_lng}")
        
        # Filter map nodes that only exist inside this specific box
        nodes_in_bbox = [
            n for n, data in graph.nodes(data=True)
            if min_lat <= data['y'] <= max_lat and min_lng <= data['x'] <= max_lng
        ]
        
        debug_log(f"[API] nodes_in_bbox found: {len(nodes_in_bbox)}")
        
        # Create a tiny, temporary map just for this specific truck trip. 
        # (This drops the copy time from seconds to milliseconds!)
        temp_graph = graph.subgraph(nodes_in_bbox).copy()
        debug_log(f"[API] Subgraph created in {time.time()-t1:.2f}s. Nodes: {len(temp_graph.nodes)}")
        
        # --- OPTIMIZATION 2: Selective Updates ---
        # Feed TomTom the exact coordinates of our tiny bounding box, not the whole county
        t2 = time.time()
        route_bbox = (min_lng, min_lat, max_lng, max_lat)
        debug_log("[API] Calling TomTom...")
        jam_coords = get_live_traffic_penalties(route_bbox)
        debug_log(f"[API] Traffic fetched in {time.time()-t2:.2f}s")
        
        t3 = time.time()
        jam_nodes = set()
        if jam_coords:
            try:
                # Vectorized call: build KDTree ONCE instead of thousands of times
                lats = [c[0] for c in jam_coords]
                lngs = [c[1] for c in jam_coords]
                nearest = ox.distance.nearest_nodes(temp_graph, lngs, lats)
                
                # nearest_nodes returns a numpy array or list when given lists
                import numpy as np
                if isinstance(nearest, (list, np.ndarray)):
                    jam_nodes.update(nearest)
                else:
                    jam_nodes.add(nearest)
            except Exception as e:
                debug_log(f"Error mapping jam nodes: {e}")

        TRAFFIC_MULTIPLIER = 10
        SURFACE_MULTIPLIER = 5
        RESTRICTED_MULTIPLIER = 100

        # This loop now only processes a few hundred local streets instead of 50,000+!
        for u, v, key, data in temp_graph.edges(keys=True, data=True):
            
            # Safely fix the string data type bug from the GraphML load
            try:
                current_weight = float(data.get('eco_weight', 1.0))
            except (TypeError, ValueError):
                current_weight = 1.0
            
            if u in jam_nodes or v in jam_nodes:
                current_weight = current_weight * TRAFFIC_MULTIPLIER

            surface_attr = data.get('surface', 'paved')
            surface = surface_attr[0] if isinstance(surface_attr, list) else surface_attr
            if surface in ['unpaved', 'dirt', 'mud', 'gravel', 'ground']:
                current_weight = current_weight * SURFACE_MULTIPLIER

            access_attr = data.get('access', 'yes')
            access = access_attr[0] if isinstance(access_attr, list) else access_attr
            if access in ['private', 'no', 'delivery']:
                current_weight = current_weight * RESTRICTED_MULTIPLIER
                
            data['eco_weight'] = current_weight

        print(f"[API] Weights processed in {time.time()-t3:.2f}s")

        # --- OPTIMIZATION 3: A* Search Algorithm ---
        t4 = time.time()
        def heuristic(node, target):
            # Pythagorean logic to guide the algorithm directly toward the destination
            n_data = temp_graph.nodes[node]
            t_data = temp_graph.nodes[target]
            return ((n_data['x'] - t_data['x'])**2 + (n_data['y'] - t_data['y'])**2)**0.5

        # Execute A* Search instead of standard Dijkstra
        print(f"[API] Starting A* search...")
        route = nx.astar_path(temp_graph, orig_node, dest_node, heuristic=heuristic, weight='eco_weight')
        print(f"[API] A* Search finished in {time.time()-t4:.2f}s. Path length: {len(route)}")

        # Convert back to GPS coordinates for the frontend
        route_coords = [{"lat": temp_graph.nodes[node]['y'], "lng": temp_graph.nodes[node]['x']} for node in route]

        # Calculate route metrics
        t5 = time.time()
        distance_km = calculate_distance_from_path(route_coords)
        nodes_count = len(route_coords)
        print(f"[API] Distance calculated in {time.time()-t5:.2f}s")
        
        # Estimate eco metrics
        # Assuming standard fuel consumption: ~8 L/100km
        # Green route is ~20% more efficient due to less congestion/uphill
        standard_fuel = distance_km / 100 * 8  # liters
        eco_fuel = standard_fuel * 0.8  # 20% more efficient
        fuel_saved = standard_fuel - eco_fuel
        
        # CO2 emissions: ~2.31 kg CO2 per liter of fuel (average for petrol vehicles)
        co2_saved = fuel_saved * 2.31
        
        # Get location names from query params (optional - for future reverse geocoding)
        start_location = request.GET.get('start_location', None)
        end_location = request.GET.get('end_location', None)
        
        # Save route history for analytics
        try:
            RouteHistory.objects.create(
                start_location_name=start_location,
                start_lat=start_lat,
                start_lng=start_lng,
                end_location_name=end_location,
                end_lat=end_lat,
                end_lng=end_lng,
                distance_km=distance_km,
                nodes_traversed=nodes_count,
                fuel_saved_liters=fuel_saved,
                co2_prevented_kg=co2_saved,
                traffic_applied=bool(jam_coords)
            )
        except Exception as e:
            print(f"Failed to save route history: {e}")

        return JsonResponse({
            "status": "success",
            "traffic_data_applied": bool(jam_coords),
            "path": route_coords,
            "distance_km": round(distance_km, 2),
            "nodes_traversed": nodes_count,
            "fuel_saved_liters": round(fuel_saved, 2),
            "co2_prevented_kg": round(co2_saved, 2)
        })

    except nx.NetworkXNoPath:
        return JsonResponse({
            "status": "error", 
            "message": "No accessible, public, or drivable route exists between these points."
        }, status=400)
    
    except Exception as e:
        # The safety net you verified earlier!
        return JsonResponse({
            "status": "error",
            "message": f"An internal routing error occurred: {str(e)}"
        }, status=500)

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

from django.db.models import Sum, Count

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_panel(request):
    total_routes = RouteHistory.objects.count()
    aggregates = RouteHistory.objects.aggregate(
        total_distance=Sum('distance_km'),
        total_fuel_saved=Sum('fuel_saved_liters'),
        total_co2_prevented=Sum('co2_prevented_kg')
    )
    
    context = {
        'total_routes': total_routes,
        'total_distance': round(aggregates['total_distance'] or 0.0, 2),
        'total_fuel_saved': round(aggregates['total_fuel_saved'] or 0.0, 2),
        'total_co2_prevented': round(aggregates['total_co2_prevented'] or 0.0, 2),
        'recent_routes': RouteHistory.objects.order_by('-created_at')[:5]
    }
    
    return render(request, 'admin_panel.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_routes(request):
    routes = RouteHistory.objects.order_by('-created_at')
    return render(request, 'admin_routes.html', {'routes': routes})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_users.html', {'users': users})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_nodes(request):
    # Some basic graph info
    graph = MainConfig.nairobi_graph
    if graph:
        nodes = len(graph.nodes)
        edges = len(graph.edges)
    else:
        nodes = 0
        edges = 0
    return render(request, 'admin_nodes.html', {'nodes': nodes, 'edges': edges})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_settings(request):
    return render(request, 'admin_settings.html')

def admin_login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Successfully authenticated as {user.username}.")
                return redirect('admin_panel')
            else:
                return render(request, 'admin_login.html', {"error_message": "Account does not have administrator access."})
        else:
            return render(request, 'admin_login.html', {"error_message": "Invalid username or password credentials."})
    return render(request, 'admin_login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_register_user(request):
    if request.method == 'POST':
        new_u = request.POST.get('new_username')
        new_e = request.POST.get('new_email')
        
        if not new_u or not new_e:
            messages.error(request, "Missing username or email parameters.")
            return redirect('admin_panel')
            
        if User.objects.filter(username=new_u).exists():
            messages.error(request, f"Username '{new_u}' is already taken.")
            return redirect('admin_panel')
            
        # Automatically generate a cryptographically secure random password
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        secure_password = "".join(secrets.choice(alphabet) for _ in range(16))
        
        try:
            user = User.objects.create_user(username=new_u, email=new_e, password=secure_password)
            messages.success(request, f"Successfully provisioned account '{new_u}'. Auto-generated Password: {secure_password}")
        except Exception as e:
            messages.error(request, f"Failed to provision user account: {str(e)}")
            
    return redirect('admin_panel')