import pandas as pd
import json
from math import radians, sin, cos, sqrt, atan2
import random

# Charger ton fichier GTFS
stops = pd.read_csv("gtfs/stops.txt")        # colonnes : stop_id, stop_name, stop_lat, stop_lon
stop_times = pd.read_csv("gtfs/stop_times.txt")  # colonnes : trip_id, stop_id, stop_sequence
trips = pd.read_csv("gtfs/trips.txt")            # colonnes : trip_id, route_id

# Fonction Haversine pour calculer la distance en km entre deux lat/lon
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Rayon de la Terre en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# Créer un dictionnaire pour stocker les probabilités par trajet
route_probs = {}

# Calculer la distance totale et le nombre d'arrêts pour chaque trip
for trip_id, group in stop_times.groupby("trip_id"):
    stops_trip = group.sort_values("stop_sequence")["stop_id"].tolist()
    total_dist = 0
    for i in range(len(stops_trip)-1):
        s1 = stops[stops["stop_id"] == stops_trip[i]].iloc[0]
        s2 = stops[stops["stop_id"] == stops_trip[i+1]].iloc[0]
        total_dist += haversine(s1["stop_lat"], s1["stop_lon"], s2["stop_lat"], s2["stop_lon"])
    
    n_stops = len(stops_trip)
    route_probs[trip_id] = {
        "total_dist": total_dist,
        "n_stops": n_stops
    }

# Trouver la distance maximale pour normalisation
max_dist = max([v["total_dist"] for v in route_probs.values()])

# Calculer les probabilités réalistes
for trip_id, v in route_probs.items():
    total_dist_norm = v["total_dist"] / max_dist if max_dist != 0 else 0
    n_stops = v["n_stops"]
    
    # Probabilités réalistes avec plafonds raisonnables
    delay_prob = round(
        min(0.4, 0.05 + total_dist_norm*0.3 + n_stops*0.005 + random.uniform(-0.02, 0.02)), 2
    )
    accident_prob = round(
        min(0.05, 0.01 + total_dist_norm*0.01 + n_stops*0.001 + random.uniform(-0.005, 0.005)), 3
    )
    
    route_probs[trip_id] = {
        "delay_prob": delay_prob,
        "accident_prob": accident_prob
    }

# Convertir en liste d'objets
route_probs_list = [
    {"trip_id": trip_id, **vals} for trip_id, vals in route_probs.items()
]

# Sauvegarder en JSON
with open("route_probs.json", "w", encoding="utf-8") as f:
    json.dump(route_probs_list, f, indent=2, ensure_ascii=False)

print("✅ JSON généré avec succès au format liste !")



print("JSON généré avec succès !")
