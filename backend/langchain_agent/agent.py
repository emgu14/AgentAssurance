import os
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from typing import Dict, List

# === 🔐 Charger le token Hugging Face depuis .env ===
load_dotenv()
HF_TOKEN = os.getenv("HF_API_KEY")
if not HF_TOKEN:
    raise ValueError("❌ Token Hugging Face manquant ! Ajoute HF_API_KEY dans ton fichier .env.")

# === 🤖 Initialisation du client Hugging Face ===
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=HF_TOKEN)

# === 📂 Charger les polices depuis le fichier JSON ===
POLICIES_FILE = "public/data/bus_insurance_policies.json"
with open(POLICIES_FILE, "r", encoding="utf-8") as f:
    POLICIES = json.load(f)

# === 🔍 Extraire JSON depuis Zephyr ===
def extract_json(ai_text: str) -> List[Dict]:
    """
    Extrait les objets JSON contenant title + analysis depuis la réponse de Zephyr.
    Si échec, renvoie un fallback avec texte brut.
    """
    try:
        # Zephyr peut renvoyer plusieurs objets séparés par des accolades
        items = []
        brace_count = 0
        current = ""
        for c in ai_text:
            if c == "{":
                brace_count += 1
            if brace_count > 0:
                current += c
            if c == "}":
                brace_count -= 1
                if brace_count == 0:
                    items.append(json.loads(current))
                    current = ""
        return items if items else [{"title": "Analyse et recommandations", "analysis": ai_text}]
    except Exception:
        return [{"title": "Analyse et recommandations", "analysis": ai_text}]

# === 🎯 Fonction principale de recommandation avec LLM en français ===
def generate_recommendation(trip_id: str, accident_prob: float, delay_prob: float) -> Dict:
    """
    Génère une recommandation simple et claire pour un trajet donné.
    - trip_id: identifiant du trajet
    - accident_prob: probabilité d'accident
    - delay_prob: probabilité de retard
    """
    # 🔹 Sélection des polices pertinentes selon triggers
    selected_policies = []
    for policy in POLICIES:
        trigger = policy.get("trigger", {})
        type_ = policy.get("type", "")
        if type_ == "accident" and accident_prob >= trigger.get("accident_prob", 0):
            selected_policies.append(policy)
        elif type_ == "retard" and delay_prob >= trigger.get("delay_prob", 0):
            selected_policies.append(policy)
        elif type_ not in ["accident", "retard"]:
            selected_policies.append(policy)

    # 🔹 Créer un prompt concis pour Zephyr
    prompt = f"""
Tu es un agent d’assurance expert pour les entreprises de transport.
Explique de manière simple sans redondance et courte l'intérêt de ces polices pour un trajet {trip_id} :
{[p.get("policy_name") for p in selected_policies]}
Fais un résumé cohérent de chaque police en une phrases maximum.
Réponds uniquement avec des objets JSON contenant:
{{
  "title": "string",
  "analysis": "string"
}}
Liste toutes les polices dans un tableau JSON, sans texte libre ou redondance.
"""

    try:
        response = client.chat.completions.create(
            model="HuggingFaceH4/zephyr-7b-beta",
            messages=[
                {"role": "system", "content": "Tu es un agent d’assurance expert pour les entreprises de transport."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.6
        )

        ai_text = response.choices[0].message["content"].strip()
        parsed = extract_json(ai_text)

        return {
            "titre": f"Recommandation pour {trip_id}",
            "analyse": f"Résumé des polices pour le trajet {trip_id}",
            "polices_recommandees": parsed  # liste d'objets {title, analysis}
        }

    except Exception as e:
        # fallback si Zephyr échoue
        return {
            "titre": f"Recommandation pour {trip_id} - Erreur Zephyr",
            "analyse": str(e),
            "polices_recommandees": selected_policies
        }
