from django.shortcuts import render

#Libraries for the routing engine
from django.http import JsonResponse
from .apps import MainConfig
import networkx as nx
import osmnx as ox
import requests

# Create your views here.
def index(request):
    return render(request, 'index.html')

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

        # A. Create a temporary copy of the graph so we don't permanently alter the memory
        # (Otherwise traffic jams from 8 AM will still be there at 2 PM)
        temp_graph = graph.copy()

        # B. Get the bounding box of Kilimani to feed to TomTom
        # (approximate bounding box for the Kilimani area)
        kilimani_bbox = (36.76, -1.30, 36.81, -1.27) 
        
        # C. Fetch live jams from TomTom
        jam_coords = get_live_traffic_penalties(kilimani_bbox)

        # D. Apply the Dynamic Traffic Penalty
        if jam_coords:
            # We snap the traffic jam GPS coordinates to our OSM map nodes
            jam_nodes = set()
            for lat, lng in jam_coords:
                jam_nodes.add(ox.distance.nearest_nodes(temp_graph, lng, lat))

            # Loop through the map and penalize any road connected to a traffic jam
            TRAFFIC_MULTIPLIER = 10 # Makes a gridlocked road "feel" 10x longer
            
            for u, v, key, data in temp_graph.edges(keys=True, data=True):
                if u in jam_nodes or v in jam_nodes:
                    data['eco_weight'] = data['eco_weight'] * TRAFFIC_MULTIPLIER

        # E. Calculate the route using the traffic-adjusted map
        route = nx.shortest_path(temp_graph, orig_node, dest_node, weight='eco_weight')

        # Convert back to GPS coordinates
        route_coords = [{"lat": temp_graph.nodes[node]['y'], "lng": temp_graph.nodes[node]['x']} for node in route]

        return JsonResponse({
            "status": "success",
            "traffic_data_applied": bool(jam_coords), # Let the frontend know if we used live data
            "path": route_coords
        })
    
    #ERROR CHECK 3: No physical road connects these points
    except nx.NetworkXNoPath:
        return JsonResponse({
            "status": "error",
            "message": "No drivable route exists between these two points on the current map"
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"An internal routing error occorred: {str(e)}"
            }, status=500)