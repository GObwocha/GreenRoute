import osmnx as ox
import networkx as nx
import time
import requests

def get_live_traffic_penalties(bbox):
    return []

def test_route():
    print("Starting test...")
    start_time = time.time()
    
    graph = ox.load_graphml("nairobi_eco_map.graphml")
    print(f"Graph loaded in {time.time() - start_time:.2f}s. Nodes: {len(graph.nodes)}")
    
    start_lat, start_lng = -1.2921, 36.8219
    end_lat, end_lng = -1.2647, 36.8018
    
    print("Calculating nearest nodes...")
    t0 = time.time()
    orig_node = ox.distance.nearest_nodes(graph, start_lng, start_lat)
    dest_node = ox.distance.nearest_nodes(graph, end_lng, end_lat)
    print(f"Nearest nodes calculated in {time.time() - t0:.2f}s")
    
    print("Subgraphing...")
    t0 = time.time()
    buffer = 0.05
    min_lat = min(start_lat, end_lat) - buffer
    max_lat = max(start_lat, end_lat) + buffer
    min_lng = min(start_lng, end_lng) - buffer
    max_lng = max(start_lng, end_lng) + buffer
    
    nodes_in_bbox = [
        n for n, data in graph.nodes(data=True)
        if min_lat <= data['y'] <= max_lat and min_lng <= data['x'] <= max_lng
    ]
    temp_graph = graph.subgraph(nodes_in_bbox).copy()
    print(f"Subgraph created in {time.time() - t0:.2f}s. Nodes: {len(temp_graph.nodes)}")
    
    print("Traffic api...")
    t0 = time.time()
    route_bbox = (min_lng, min_lat, max_lng, max_lat)
    jam_coords = get_live_traffic_penalties(route_bbox)
    print(f"Traffic fetched in {time.time() - t0:.2f}s")
    
    print("Processing weights...")
    t0 = time.time()
    jam_nodes = set()
    if jam_coords:
        for lat, lng in jam_coords:
            try:
                jam_nodes.add(ox.distance.nearest_nodes(temp_graph, lng, lat))
            except ValueError:
                pass
                
    for u, v, key, data in temp_graph.edges(keys=True, data=True):
        try:
            current_weight = float(data.get('eco_weight', 1.0))
        except (TypeError, ValueError):
            current_weight = 1.0
            
        data['eco_weight'] = current_weight
    print(f"Weights processed in {time.time() - t0:.2f}s")
    
    print("A* Search...")
    t0 = time.time()
    def heuristic(node, target):
        n_data = temp_graph.nodes[node]
        t_data = temp_graph.nodes[target]
        return ((n_data['x'] - t_data['x'])**2 + (n_data['y'] - t_data['y'])**2)**0.5
        
    try:
        route = nx.astar_path(temp_graph, orig_node, dest_node, heuristic=heuristic, weight='eco_weight')
        print(f"A* finished in {time.time() - t0:.2f}s. Path length: {len(route)}")
    except nx.NetworkXNoPath:
        print("No path found!")
    except Exception as e:
        print(f"Error in A*: {e}")

if __name__ == '__main__':
    test_route()
