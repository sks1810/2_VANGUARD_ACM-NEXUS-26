import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_route_segments(stops):
    """
    Takes list of stops → returns list of segments with route info
    stops = ["Thrissur", "Palakkad", "Kozhikode", "Kannur"]
    """
    segments = []

    for i in range(len(stops) - 1):
        origin      = stops[i]
        destination = stops[i + 1]

        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin":           origin,
            "destination":      destination,
            "departure_time":   "now",
            "traffic_model":    "best_guess",
            "key":              GOOGLE_API_KEY
        }

        try:
            response = requests.get(url, params=params, timeout=5).json()
            leg = response["routes"][0]["legs"][0]

            normal_sec  = leg["duration"]["value"]
            traffic_sec = leg.get("duration_in_traffic", leg["duration"])["value"]
            distance_km = leg["distance"]["value"] / 1000

            segments.append({
                "from":                 origin,
                "to":                   destination,
                "distance_km":          round(distance_km, 1),
                "normal_duration_min":  round(normal_sec / 60, 1),
                "traffic_duration_min": round(traffic_sec / 60, 1),
                "polyline":             leg["steps"][0]["polyline"]["points"]
            })

        except Exception as e:
            print(f"Route error {origin}→{destination}: {e}")
            segments.append({
                "from":                 origin,
                "to":                   destination,
                "distance_km":          0,
                "normal_duration_min":  0,
                "traffic_duration_min": 0,
                "polyline":             ""
            })

    return segments