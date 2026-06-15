from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
import secrets
#Libraries for the routing engine
from django.http import JsonResponse
from .apps import MainConfig
import networkx as nx
import osmnx as ox
import requests

# Create your views here.
def client_dashboard(request):
    # This view serves the public interactive Eco-Planner dashboard
    return render(request, 'client_dashboard.html')

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
    
    #3. Math Engine
    try:
        # Snap the GPS coordinates to the nearest physical road
        orig_node = ox.distance.nearest_nodes(graph, start_lng, start_lat)
        dest_node = ox.distance.nearest_nodes(graph, end_lng, end_lat)

        # Create a temporary copy of the graph to keep the master memory pristine
        temp_graph = graph.copy()

        # Approximate bounding box for the Kilimani map area
        nairobi_bbox = (36.65, -1.45, 37.11, -1.15)
        
        # Fetch live traffic incident locations from TomTom
        jam_coords = get_live_traffic_penalties(nairobi_bbox)

        # Map out any active traffic jam nodes
        jam_nodes = set()
        if jam_coords:
            for lat, lng in jam_coords:
                jam_nodes.add(ox.distance.nearest_nodes(temp_graph, lng, lat))

        # --- PENALTY CONFIGURATIONS ---
        TRAFFIC_MULTIPLIER = 10     # Gridlocked roads feel 10x longer
        SURFACE_MULTIPLIER = 5      # Unpaved/dirt roads feel 5x longer
        RESTRICTED_MULTIPLIER = 100 # Massive penalty to effectively block private gates

        # Process every single road segment within the active bounding map
        for u, v, key, data in temp_graph.edges(keys=True, data=True):
            
            # 1. LIVE TRAFFIC PENALTY
            if u in jam_nodes or v in jam_nodes:
                data['eco_weight'] = data['eco_weight'] * TRAFFIC_MULTIPLIER

            # 2. ROAD QUALITY CHECK
            # Safely read surface data (handles cases where OSM stores attributes as lists)
            surface_attr = data.get('surface', 'paved')
            surface = surface_attr[0] if isinstance(surface_attr, list) else surface_attr
            
            if surface in ['unpaved', 'dirt', 'mud', 'gravel', 'ground']:
                data['eco_weight'] = data['eco_weight'] * SURFACE_MULTIPLIER

            # 3. RESTRICTED ACCESS CHECK
            # Check for gates, private driveways, or closed pathways
            access_attr = data.get('access', 'yes')
            access = access_attr[0] if isinstance(access_attr, list) else access_attr
            
            if access in ['private', 'no', 'delivery']:
                data['eco_weight'] = data['eco_weight'] * RESTRICTED_MULTIPLIER

        # Run the shortest path logic over the heavily weighted, customized map
        route = nx.shortest_path(temp_graph, orig_node, dest_node, weight='eco_weight')

        # Convert the node path back into a serializable list of GPS coordinates
        route_coords = [{"lat": temp_graph.nodes[node]['y'], "lng": temp_graph.nodes[node]['x']} for node in route]

        return JsonResponse({
            "status": "success",
            "traffic_data_applied": bool(jam_coords),
            "path": route_coords
        })

    except nx.NetworkXNoPath:
        return JsonResponse({
            "status": "error", 
            "message": "No accessible, public, or drivable route exists between these points."
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"An internal routing error occorred: {str(e)}"
            }, status=500)

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_panel(request):
    return render(request, 'admin_panel.html')

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