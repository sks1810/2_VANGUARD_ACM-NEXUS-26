from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import requests
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv


load_dotenv()
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "fallback_key")
GOOGLE_KEY      = os.getenv("GOOGLE_MAPS_API_KEY",  "fallback_key")
WAREHOUSE_LAT   = 9.9816
WAREHOUSE_LON   = 76.2999
DEFAULT_CITY    = "Ernakulam"

# Real destination for /payload traffic check (~8 km from warehouse)
TRAFFIC_TEST_DEST = "Lulu Mall, Edapally, Kochi, Kerala"


app = FastAPI(title="NEXUS Smart Delivery Routing API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)


model = joblib.load("models/random_forest_model.pkl")


try:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
    fs = firestore.client()
    firebase_ready = True
    print("✅ Firebase Firestore connected")
except Exception as e:
    firebase_ready = False
    fs = None
    print(f"⚠️ Firebase not connected: {e}")


# ══════════════════════════════════════════
#  WEBSOCKET MANAGER
# ══════════════════════════════════════════
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data))
            except:
                pass


manager = ConnectionManager()


# ══════════════════════════════════════════
#  SCHEMAS
# ══════════════════════════════════════════
class RouteInput(BaseModel):
    route_length_km:          float
    traffic_density:          float
    average_speed_kmph:       float
    congestion_index:         float
    hour_of_day:              int
    peak_hour_flag:           int
    rain_intensity_mm_per_hr: float
    visibility_m:             float
    weather_type:             str
    wind_speed_kmph:          float
    temperature_c:            float
    strike_activity_level:    int
    protest_or_event_flag:    int
    road_block_flag:          int
    accident_present:         int


class DeliveryPlanInput(BaseModel):
    drivers:     list
    created_at:  str
    total_delay: float
    total_time:  float


class Detection(BaseModel):
    lat: float; lng: float; type: str; severity: str
    confidence: float; label: str; route_id: str; timestamp: str


detections_store = []


# ══════════════════════════════════════════
#  GEOCODING CACHE
# ══════════════════════════════════════════
geocode_cache = {}


def geocode_location(address: str) -> dict | None:
    if address in geocode_cache:
        return geocode_cache[address]
    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": GOOGLE_KEY},
            timeout=5
        ).json()
        if r.get("status") == "OK":
            loc    = r["results"][0]["geometry"]["location"]
            result = {"lat": loc["lat"], "lng": loc["lng"],
                      "formatted": r["results"][0]["formatted_address"]}
            geocode_cache[address] = result
            return result
        print(f"⚠️ Geocoding status: {r.get('status')} for: {address}")
    except Exception as e:
        print(f"⚠️ Geocoding failed for '{address}': {e}")
    return None


# ══════════════════════════════════════════
#  WEATHER
# ══════════════════════════════════════════
def get_full_weather(city=DEFAULT_CITY):
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": OPENWEATHER_KEY, "units": "metric"},
            timeout=5
        ).json()
        if "weather" not in r:
            raise ValueError("No weather data")
        wid = r["weather"][0]["id"]
        if   wid < 300:  wt = "heavy_rain"
        elif wid < 400:  wt = "rain"
        elif wid < 502:  wt = "rain"
        elif wid < 600:  wt = "heavy_rain"
        elif wid < 700:  wt = "fog"
        elif wid == 800: wt = "clear"
        else:            wt = "cloudy"
        return {
            "weather_type":             wt,
            "rain_intensity_mm_per_hr": round(r.get("rain", {}).get("1h", 0.0), 2),
            "visibility_m":             r.get("visibility", 10000),
            "wind_speed_kmph":          round(r["wind"]["speed"] * 3.6, 1),
            "temperature_c":            round(r["main"]["temp"], 1)
        }
    except Exception as e:
        print(f"⚠️ Weather failed: {e}")
        return {"weather_type": "clear", "rain_intensity_mm_per_hr": 0,
                "visibility_m": 10000, "wind_speed_kmph": 10, "temperature_c": 30}


# ══════════════════════════════════════════
#  TRAFFIC  (with zero-distance guard)
# ══════════════════════════════════════════
def get_traffic(origin: str, destination: str):
    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins":        origin,
                "destinations":   destination,
                "departure_time": "now",
                "traffic_model":  "best_guess",
                "key":            GOOGLE_KEY
            },
            timeout=5
        ).json()

        el = r["rows"][0]["elements"][0]

        # ✅ Guard: element must be OK
        if el.get("status") != "OK":
            raise ValueError(f"Element status: {el.get('status')}")

        dist_m  = el["distance"]["value"]
        norm_s  = el["duration"]["value"]
        traf_s  = el["duration_in_traffic"]["value"]

        # ✅ Guard: distance must be non-zero
        if dist_m == 0:
            raise ValueError("Distance is 0 — origin and destination are the same")

        dist_km = round(dist_m / 1000, 2)
        norm    = norm_s  / 60
        traffic = traf_s  / 60
        delay_r = (traffic - norm) / max(norm, 1)
        cong    = round(min(max(delay_r, 0.0), 1.0), 2)
        speed   = round((dist_km / traffic) * 60, 1) if traffic > 0 else 40

        return {
            "route_length_km":    dist_km,
            "average_speed_kmph": speed,
            "congestion_index":   cong,
            "traffic_density":    int(200 + cong * 500)
        }
    except Exception as e:
        print(f"⚠️ Traffic failed: {e}")
        h    = datetime.now().hour
        peak = 1 if h in [7, 8, 9, 17, 18, 19] else 0
        return {
            "route_length_km":    8.0,
            "average_speed_kmph": 18.0 if peak else 32.0,
            "congestion_index":   0.6  if peak else 0.15,
            "traffic_density":    400  if peak else 180
        }


# ══════════════════════════════════════════
#  WEATHER ONE-HOT ENCODER
#  Order matches training columns exactly:
#  15: weather_type_cloudy
#  16: weather_type_fog
#  17: weather_type_heavy_rain
#  18: weather_type_rain
#  (clear = all zeros — baseline category)
# ══════════════════════════════════════════
def encode_weather(wt: str) -> dict:
    w = wt.lower().replace(" ", "_")
    return {
        "weather_type_cloudy":     1 if w == "cloudy"     else 0,
        "weather_type_fog":        1 if w == "fog"        else 0,
        "weather_type_heavy_rain": 1 if w == "heavy_rain" else 0,
        "weather_type_rain":       1 if w == "rain"       else 0,
    }


# ══════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════
@app.get("/")
def root():
    return {
        "status":    "NEXUS API running ✅",
        "version":   "5.1",
        "endpoints": ["/config", "/orders", "/payload",
                      "/predict_delay", "/delivery_plan/save",
                      "/detections", "/docs"]
    }


@app.get("/config")
def get_config():
    return {
        "google_maps_key": GOOGLE_KEY,
        "warehouse":       {"lat": WAREHOUSE_LAT, "lng": WAREHOUSE_LON},
        "city":            DEFAULT_CITY
    }


# ══════════════════════════════════════════
#  /orders
# ══════════════════════════════════════════
@app.get("/orders")
def get_orders():
    if not firebase_ready:
        return {"error": "Firebase not connected", "drivers": []}
    try:
        assigned_docs = fs.collection("assigned_orders").stream()
        drivers       = []

        for doc in assigned_docs:
            data        = doc.to_dict()
            order_ids   = data.get("orderIds",    [])
            driver_id   = data.get("driverId",    doc.id)
            driver_name = data.get("driverName",  data.get("driver", driver_id))
            hub         = data.get("hub",         DEFAULT_CITY)

            hub_coords = geocode_location(f"{hub}, Kerala, India") \
                         or {"lat": WAREHOUSE_LAT, "lng": WAREHOUSE_LON}

            orders = []
            for oid in order_ids:
                order_doc = fs.collection("orders").document(oid).get()
                if not order_doc.exists:
                    print(f"⚠️ Order {oid} not found")
                    continue

                odata       = order_doc.to_dict()
                odata["id"] = order_doc.id
                location    = odata.get("location", "")

                coords = geocode_location(location) if location else None
                if not coords:
                    print(f"⚠️ Could not geocode: {location}")
                    continue

                odata["lat"]               = coords["lat"]
                odata["lng"]               = coords["lng"]
                odata["formatted_address"] = coords.get("formatted", location)
                orders.append(odata)

            if orders:
                drivers.append({
                    "doc_id":      doc.id,
                    "driver_id":   driver_id,
                    "driver_name": driver_name,
                    "hub":         hub,
                    "hub_lat":     hub_coords["lat"],
                    "hub_lng":     hub_coords["lng"],
                    "date":        data.get("date", ""),
                    "orders":      orders,
                    "order_count": len(orders)
                })

        return {"drivers": drivers, "total_drivers": len(drivers)}
    except Exception as e:
        return {"error": str(e), "drivers": []}


# ══════════════════════════════════════════
#  /payload  — uses real destination now
# ══════════════════════════════════════════
@app.get("/payload")
def get_payload():
    h = datetime.now().hour
    return {
        **get_full_weather(DEFAULT_CITY),
        **get_traffic(
            f"{WAREHOUSE_LAT},{WAREHOUSE_LON}",
            TRAFFIC_TEST_DEST           # ✅ real destination ~8 km away
        ),
        "hour_of_day":           h,
        "peak_hour_flag":        1 if h in [7, 8, 9, 17, 18, 19] else 0,
        "strike_activity_level": 0,
        "protest_or_event_flag": 0,
        "road_block_flag":       0,
        "accident_present":      0
    }


# ══════════════════════════════════════════
#  /predict_delay
#  Feature column order EXACTLY matches
#  training data (verified from dataset):
#  0  route_length_km
#  1  traffic_density
#  2  average_speed_kmph
#  3  congestion_index
#  4  hour_of_day
#  5  peak_hour_flag
#  6  rain_intensity_mm_per_hr
#  7  visibility_m
#  8  wind_speed_kmph
#  9  temperature_c
#  10 strike_activity_level
#  11 protest_or_event_flag
#  12 road_block_flag
#  13 accident_present
#  14 travel_time_minutes      ← most important (77.5%)
#  15 weather_type_cloudy
#  16 weather_type_fog
#  17 weather_type_heavy_rain
#  18 weather_type_rain
# ══════════════════════════════════════════
@app.post("/predict_delay")
def predict_delay(data: RouteInput):
    try:
        # ✅ Calculate base travel time (feature #14 — 77.5% importance)
        tt = (data.route_length_km / data.average_speed_kmph * 60) \
             if data.average_speed_kmph > 0 else 25.0

        we = encode_weather(data.weather_type)

        df = pd.DataFrame([{
            "route_length_km":          data.route_length_km,
            "traffic_density":          data.traffic_density,
            "average_speed_kmph":       data.average_speed_kmph,
            "congestion_index":         data.congestion_index,
            "hour_of_day":              data.hour_of_day,
            "peak_hour_flag":           data.peak_hour_flag,
            "rain_intensity_mm_per_hr": data.rain_intensity_mm_per_hr,
            "visibility_m":             data.visibility_m,
            "wind_speed_kmph":          data.wind_speed_kmph,
            "temperature_c":            data.temperature_c,
            "strike_activity_level":    data.strike_activity_level,
            "protest_or_event_flag":    data.protest_or_event_flag,
            "road_block_flag":          data.road_block_flag,
            "accident_present":         data.accident_present,
            "travel_time_minutes":      tt,     # ← feature 14
            **we                                # ← features 15-18
        }])

        delay = float(model.predict(df)[0])
        delay = max(0.0, round(delay, 2))

        return {
            "delay_minutes":        delay,
            "travel_time_minutes":  round(tt + delay, 2),
            "source":               "random_forest_model"
        }

    except Exception as e:
        print(f"⚠️ Prediction failed: {e}")
        # Fallback formula
        tt    = (data.route_length_km / max(data.average_speed_kmph, 1)) * 60
        delay = round(tt * 0.15 * (1 + data.congestion_index * 0.5), 2)
        return {
            "delay_minutes":        delay,
            "travel_time_minutes":  round(tt + delay, 2),
            "source":               "fallback"
        }


# ══════════════════════════════════════════
#  /delivery_plan/save
# ══════════════════════════════════════════
@app.post("/delivery_plan/save")
def save_delivery_plan(data: DeliveryPlanInput):
    if not firebase_ready:
        return {"status": "Firebase not connected"}
    try:
        saved_plans = []

        for driver in data.drivers:
            plan_ref = fs.collection("delivery_plans").add({
                "driver_id":   driver["driver_id"],
                "driver_name": driver["driver_name"],
                "hub":         driver["hub"],
                "date":        driver["date"],
                "created_at":  data.created_at,
                "total_delay": driver["total_delay"],
                "total_time":  driver["total_time"],
                "orders":      driver["orders"]
            })
            plan_id = plan_ref[1].id

            for order in driver["orders"]:
                order_doc_id = order.get("order_id")
                if order_doc_id:
                    fs.collection("orders").document(order_doc_id).update({
                        "delivery_order":  order["delivery_order"],
                        "estimated_delay": order["estimated_delay"],
                        "best_route":      order["best_route"],
                        "plan_id":         plan_id,
                        "optimized_at":    data.created_at,
                        "status":          "scheduled"
                    })

            saved_plans.append({
                "driver_id":   driver["driver_id"],
                "driver_name": driver["driver_name"],
                "plan_id":     plan_id,
                "orders":      len(driver["orders"])
            })

        return {"status": "saved to Firebase ✅", "plans": saved_plans}
    except Exception as e:
        return {"status": f"Firebase error: {str(e)}"}


# ══════════════════════════════════════════
#  DETECTIONS
# ══════════════════════════════════════════
@app.get("/detections")
def get_detections():
    return detections_store


@app.post("/detections/add")
async def add_detection(d: Detection):
    detections_store.append(d.dict())
    await manager.broadcast({"type": "new_detection", "detection": d.dict()})
    return {"status": "added", "total": len(detections_store)}


# ══════════════════════════════════════════
#  WEBSOCKET
# ══════════════════════════════════════════
@app.websocket("/ws/live")
async def live_feed(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.websocket("/ws/truck")
async def truck_gps(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            if msg.get("type") == "gps_update":
                await manager.broadcast({
                    "type":  "truck_location",
                    "lat":   msg["lat"],
                    "lng":   msg["lng"],
                    "speed": msg.get("speed"),
                    "ts":    msg.get("ts")
                })
    except WebSocketDisconnect:
        manager.disconnect(ws)