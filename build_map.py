import osmnx as ox
import networkx as nx

print("0. Configuring OSMnx...")
# FIX 1: Ignore the corrupted local cache and force a fresh download
ox.settings.use_cache = False
# FIX 2: Give the server 5 minutes to send the massive Nairobi map so it doesn't time out
ox.settings.timeout = 300 

print("1. Downloading full Nairobi Map (This will take a few minutes)...")
graph = ox.graph_from_place("Nairobi, Kenya", network_type='drive')

print("2. Fetching Elevation Data (This might take 15+ minutes. Grab a coffee!)...")
original_url = ox.settings.elevation_url_template

# Using Open Topo Data
ox.settings.elevation_url_template = "https://api.opentopodata.org/v1/aster30m?locations={locations}"

# Lowering batch_size prevents the "413 Payload Too Large" error
graph = ox.elevation.add_node_elevations_google(graph, batch_size=30, pause=1.5)
graph = ox.elevation.add_edge_grades(graph)

ox.settings.elevation_url_template = original_url 

print("3. Calculating Eco-Weights...")
UPHILL_PENALTY = 20
DOWNHILL_PENALTY = 2

for u, v, key, data in graph.edges(keys=True, data=True):
    length = data.get('length', 0)
    grade = data.get('grade', 0) 
    
    if grade > 0: 
        eco_weight = length * (1 + (grade * UPHILL_PENALTY))
    elif grade < 0: 
        eco_weight = length * (1 + (abs(grade) * DOWNHILL_PENALTY))
    else: 
        eco_weight = length
    
    data['eco_weight'] = eco_weight

print("4. Saving Compiled Map to Hard Drive...")
ox.save_graphml(graph, filepath="nairobi_eco_map.graphml")
print("Done! You can now boot Django instantly.")