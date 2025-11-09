from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from langchain_agent.agent import generate_recommendation

# === Chemins fichiers ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, ".", "public", "data")
ROUTE_PROBS_PATH = os.path.join(DATA_DIR, "route_probs.json")
LINES_PATH = os.path.join(DATA_DIR, "lines.geojson")

# === Initialisation FastAPI ===
app = FastAPI(title="Agentic Mobility & Transport Insurance Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Chargement des données ===
with open(ROUTE_PROBS_PATH, "r", encoding="utf-8") as f:
    route_probs = json.load(f)

# Accès rapide par trip_id
route_dict = {item["trip_id"]: item for item in route_probs}

@app.get("/")
def root():
    return {"message": "✅ API Mobility Planner active", "routes": len(route_probs)}

@app.get("/recommendation/{trip_id}")
def get_recommendation(trip_id: str):
    trip_data = route_dict.get(trip_id)
    if not trip_data:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")

    delay_prob = trip_data.get("delay_prob", 0)
    accident_prob = trip_data.get("accident_prob", 0)

    rec = generate_recommendation(trip_id, delay_prob, accident_prob)

    # 🧠 Sécurité : on garantit toujours les 4 champs attendus
    return {
        "titre": rec.get("titre", "💡 Recommandation IA"),
        "analyse": rec.get("analyse", "Analyse non disponible."),
        "polices_recommandees": rec.get("polices_recommandees", []),
        "recommandation": rec.get("recommandation", "Aucune recommandation."),
        "delay_prob": delay_prob,
        "accident_prob": accident_prob,
        "trip_id": trip_id,
    }

@app.get("/route_probs")
def get_route_probs():
    return route_dict

@app.get("/lines")
def get_lines():
    if not os.path.exists(LINES_PATH):
        raise HTTPException(status_code=404, detail="Fichier lines.geojson non trouvé")
    with open(LINES_PATH, "r", encoding="utf-8") as f:
        lines_data = json.load(f)
    return lines_data
