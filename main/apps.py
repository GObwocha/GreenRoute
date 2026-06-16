from django.apps import AppConfig
import osmnx as ox

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
    # Updated variable name to reflect the massive upgrade!
    nairobi_graph = None

    def ready(self):
        import os
        if os.environ.get('RUN_MAIN'):
            print("Booting up Django: Loading pre-compiled Nairobi map from disk...")
            
            # Instantly load the compiled map we just saved!
            MainConfig.nairobi_graph = ox.load_graphml("nairobi_eco_map.graphml")
            
            print("Nairobi map successfully loaded into memory!")