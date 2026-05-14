from django.shortcuts import render

#Libraries for the routing engine
from django.http import JsonResponse
from .apps import MainConfig
import networkx as nx
import osmnx as ox

# Create your views here.
def index(request):
    return render(request, 'index.html')

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
        orig_node = ox.distance.nearest_nodes(graph, start_lng,start_lat)
        dest_node = ox.distance.nearest_nodes(graph, end_lng,end_lat)

        route = nx.shortest_path(graph, orig_node, dest_node, weight='eco_weight')
        route_coords = [{"lat": graph.nodes[node]['y'], "lng": graph.nodes[node]['x']} for node in route]

        return JsonResponse({
            "status": "success",
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

def admin_panel(request):
    return render(request, 'admin_panel.html')