import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_traffic_data(origin="Kozhikode", destination="Calicut Beach"):
    if not GOOGLE_API_KEY:
        return None  # skip traffic if no key

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "departure_time": "now",
        "traffic_model": "best_guess",
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5).json()
        element = response["rows"][0]["elements"][0]

        normal_sec  = element["duration"]["value"]
        traffic_sec = element["duration_in_traffic"]["value"]

        return {
            "normal_duration_min":  round(normal_sec / 60, 1),
            "traffic_duration_min": round(traffic_sec / 60, 1)
        }
    except Exception as e:
        print(f"Traffic API error: {e}")
        return None