from django.apps import AppConfig
import osmnx as ox
import os
from django.conf import settings

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
    # Updated variable name to reflect the massive upgrade!
    nairobi_graph = None

    def ready(self):
        # Construct the absolute path so Render never loses the file
        graph_path = os.path.join(settings.BASE_DIR, "nairobi_eco_map.graphml")
        
        # Only load if it hasn't been loaded yet (safe for production workers)
        if MainConfig.nairobi_graph is None:
            try:
                print(f"Booting up Django: Loading pre-compiled map from {graph_path}...")
                
                # Instantly load the compiled map we just saved!
                MainConfig.nairobi_graph = ox.load_graphml(graph_path)
                
                print("Nairobi map successfully loaded into memory!")
            except Exception as e:
                print(f"CRITICAL ERROR: Failed to load map. {e}")