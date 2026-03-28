import os
import math
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_KEY      = os.getenv("GOOGLE_MAPS_API_KEY")


# ── 1. Extended Weather ──────────────────────────────────────────────
def get_full_weather(city="Kozhikode"):
    url = "https://api.openweathermap.org/data/2.5/weather"
    r = requests.get(url, params={"q": city, "appid": OPENWEATHER_KEY, "units": "metric"}, timeout=5).json()

    if "weather" not in r:
        return {
            "weather_type": "clear", "rain_intensity_mm_per_hr": 0,
            "visibility_m": 10000, "wind_speed_kmph": 10, "temperature_c": 30
        }

    wid  = r["weather"][0]["id"]
    desc = r["weather"][0]["description"].lower()

    # Map to your friend's 5 categories
    if wid < 300:
        weather_type = "heavy_rain"
    elif wid < 400:
        weather_type = "rain"
    elif wid < 600:
        weather_type = "heavy_rain" if wid >= 502 else "rain"
    elif wid < 700:
        weather_type = "clear"
    elif wid < 800:
        weather_type = "fog"
    elif wid == 800:
        weather_type = "clear"
    else:
        weather_type = "cloudy"

    rain_intensity  = r.get("rain", {}).get("1h", 0.0)
    visibility_m    = r.get("visibility", 10000)
    wind_speed_kmph = round(r["wind"]["speed"] * 3.6, 1)   # m/s → km/h
    temperature_c   = r["main"]["temp"]

    return {
        "weather_type":            weather_type,
        "rain_intensity_mm_per_hr": round(rain_intensity, 2),
        "visibility_m":            visibility_m,
        "wind_speed_kmph":         wind_speed_kmph,
        "temperature_c":           round(temperature_c, 1)
    }


# ── 2. Traffic Data ──────────────────────────────────────────────────
def get_full_traffic(origin, destination):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    r = requests.get(url, params={
        "origins": origin, "destinations": destination,
        "departure_time": "now", "traffic_model": "best_guess", "key": GOOGLE_KEY
    }, timeout=5).json()

    element     = r["rows"][0]["elements"][0]
    normal_sec  = element["duration"]["value"]
    traffic_sec = element["duration_in_traffic"]["value"]
    distance_m  = element["distance"]["value"]

    route_length_km     = round(distance_m / 1000, 2)
    normal_min          = normal_sec / 60
    traffic_min         = traffic_sec / 60
    delay_ratio         = (traffic_min - normal_min) / max(normal_min, 1)
    congestion_index    = round(min(max(delay_ratio, 0.0), 1.0), 2)
    average_speed_kmph  = round((route_length_km / traffic_min) * 60, 1) if traffic_min > 0 else 60
    traffic_density     = int(200 + congestion_index * 500)   # estimated 200–700

    return {
        "route_length_km":     route_length_km,
        "average_speed_kmph":  average_speed_kmph,
        "congestion_index":    congestion_index,
        "traffic_density":     traffic_density,
        "normal_duration_min": round(normal_min, 1),
        "traffic_duration_min": round(traffic_min, 1)
    }


# ── 3. Build Full Payload ────────────────────────────────────────────
def build_payload(
    origin="Kozhikode",
    destination="Calicut Beach",
    city="Kozhikode",
    accident_detections=None,
    road_block_flag=0,
    strike_activity_level=0,
    protest_or_event_flag=0
):
    now  = datetime.now()
    hour = now.hour
    peak = 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0

    weather = get_full_weather(city)
    traffic = get_full_traffic(origin, destination)

    accident_present = 1 if accident_detections else 0

    payload = {
        # Route
        "route_length_km":          traffic["route_length_km"],
        "average_speed_kmph":       traffic["average_speed_kmph"],

        # Traffic
        "traffic_density":          traffic["traffic_density"],
        "congestion_index":         traffic["congestion_index"],
        "hour_of_day":              hour,
        "peak_hour_flag":           peak,

        # Weather
        "rain_intensity_mm_per_hr": weather["rain_intensity_mm_per_hr"],
        "visibility_m":             weather["visibility_m"],
        "weather_type":             weather["weather_type"],
        "wind_speed_kmph":          weather["wind_speed_kmph"],
        "temperature_c":            weather["temperature_c"],

        # Events
        "strike_activity_level":    strike_activity_level,
        "protest_or_event_flag":    protest_or_event_flag,
        "road_block_flag":          road_block_flag,
        "accident_present":         accident_present,
    }

    return payload


# ── 4. Send to Friend's API ──────────────────────────────────────────
def send_payload(payload, api_url):
    try:
        r = requests.post(api_url, json=payload, timeout=10)
        print("✅ Sent! Status:", r.status_code)
        print("Response:", r.json())
        return r.json()
    except Exception as e:
        print(f"❌ Failed to send: {e}")
        return None


# ── 5. Test Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    payload = build_payload(
        origin="Kozhikode",
        destination="Calicut Beach",
        city="Kozhikode",
        accident_detections=[],     # pass real detections from accident_adapter
        road_block_flag=0,
        strike_activity_level=0,
        protest_or_event_flag=0
    )

    print("\n── Payload to send ──")
    print(json.dumps(payload, indent=2))

    # Uncomment when you have your friend's API URL:
    # send_payload(payload, "https://your-friends-api.com/predict")