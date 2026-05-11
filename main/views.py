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
    try:
        start_lat = float(request.GET.get('start_lat'))
        start_lng = float(request.GET.get('start_lng'))
        end_lat = float(request.GET.get('end_lat'))
        end_lng = float(request.GET.get('end_lng'))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Please provide valid coordinates."}, status=400)
    
    graph = MainConfig.kilimani_graph

    try:
        orig_node = ox.distance.nearest_nodes(graph, start_lng,start_lat)
        dest_node = ox.distance.nearest_nodes(graph, end_lng,end_lat)

        route = nx.shortest_path(graph, orig_node, dest_node, weight='eco_weight')
        route_coords = [{"lat": graph.nodes[node]['y'], "lng": graph.nodes[node]['x']} for node in route]

        return JsonResponse({
            "status": "success",
            "path": route_coords
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)