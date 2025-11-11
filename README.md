# Agentic Mobility AI - Bus Insurance Recommendation System

## Overview
This project implements **Agentic Mobility AI**, a system that analyzes bus trips and provides personalized insurance recommendations based on delay and accident probabilities. The system integrates:  

- **Zephyr 7B Beta** from Hugging Face for AI-based risk analysis.
- A dataset of bus insurance policies.
- A FastAPI backend serving trip data, probabilities, and AI-generated recommendations.
- A Leaflet-based frontend for visualizing bus routes, delays, and AI recommendations interactively on a map.

---

## Key Features

- **Dynamic Risk Analysis:** Computes delay and accident probabilities for each bus trip.
- **Policy Selection:** Matches the risk probabilities with the most relevant insurance policies.
- **AI Recommendations:** Uses Zephyr to generate structured JSON recommendations.
- **Interactive Map Visualization:** Click on bus lines to see risk levels and AI recommendations.

---

## Important Note: Hugging Face API Key

⚠️ **The Hugging Face API key is required to run the AI recommendation engine.**  

- The key is **not included** in this repository because Hugging Face blocks shared keys.  
- Without your own API key, the AI recommendation endpoint (`/recommendation/<trip_id>`) **will not work**, but map and route data still load.

**Setup:**

1. Create an account at [Hugging Face](https://huggingface.co/).  
2. Generate a personal API token.  
3. Create a `.env` file in the `backend` folder:

```bash
HF_API_KEY=your_personal_huggingface_api_key_here
Installation & Running the Project
1. Clone the repository
bash
Copier le code
git clone https://github.com/yourusername/agentic-mobility.git
cd agentic-mobility
2. Set up Python environment for backend
bash
Copier le code
python -m venv venv
# Activate environment:
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
3. Install backend dependencies
bash
Copier le code
pip install -r requirements.txt
4. Run the backend server
bash
Copier le code
uvicorn backend.main:app --reload
Server runs at http://127.0.0.1:8000

Endpoints:

/lines → bus routes (GeoJSON)

/route_probs → delay & accident probabilities

/recommendation/<trip_id> → AI recommendation for a trip

5. Run the frontend
Option A – Open in Browser:
Open frontend/index.html directly in your browser.

Option B – Serve via Python HTTP server (optional for full local testing):

bash
Copier le code
cd frontend
# Python 3
python -m http.server 8080
Then open: http://127.0.0.1:8080

The map will load bus lines and show interactive popups.

AI recommendations work if your Hugging Face API key is set.
