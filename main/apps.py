from django.apps import AppConfig
import osmnx as ox


class MainConfig(AppConfig):
    name = 'main'
    default_auto_field = 'django.db.models.BigAutoField'

    nairobi_graph = None

    def ready(self):
        import os
        if os.environ.get('RUN_MAIN'):
            print("Booting up Django: Loading Nairobi map...")

            graph = ox.graph_from_place("Nairobi, Kenya", network_type='drive')

            UPHILL_PENALTY = 20
            DOWNHILL_PENALTY = 2

            for u,v,key, data in graph.edges(keys=True, data=True):
                length = data.get('length',0)
                grade = data.get('grade',0)
                if grade > 0:
                    eco_weight = length * (1 +(grade * UPHILL_PENALTY))
                elif grade < 0:
                    eco_weight = length * (1 + (abs(grade) * DOWNHILL_PENALTY))
                else:
                    eco_weight = length
                data['eco_weight'] = eco_weight

            MainConfig.nairobi_graph = graph
            print("Map successfully loaded into Django's memory")
