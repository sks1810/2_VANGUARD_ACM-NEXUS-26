import os
import sys
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(__file__))

from detection.pothole_adapter import get_pothole_detections
from detection.accident_adapter import get_accident_detections
from risk_engine.scorer import calculate_route_risk
from weather import get_weather_risk
from traffic import get_traffic_data
from routes import get_route_segments
from optimizer import optimize_route

app = FastAPI(title="NEXUS Road Risk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check
@app.get("/")
def root():
    return {"status": "NEXUS API running ✅"}


# ── Single route analysis (old endpoint — keep for testing)
@app.post("/analyze")
async def analyze(
    pothole_video:  UploadFile = File(...),
    accident_video: UploadFile = File(...),
    city:           str = Form(default="Kozhikode"),
    origin:         str = Form(default="Kozhikode"),
    destination:    str = Form(default="Calicut Beach")
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as p_tmp:
        shutil.copyfileobj(pothole_video.file, p_tmp)
        pothole_path = p_tmp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as a_tmp:
        shutil.copyfileobj(accident_video.file, a_tmp)
        accident_path = a_tmp.name

    try:
        pothole_raw    = get_pothole_detections(pothole_path)
        accident_raw   = get_accident_detections(accident_path)

        potholes_flat  = [p for frame in pothole_raw  for p in frame["potholes"]]
        accidents_flat = [a for frame in accident_raw for a in frame["accidents"]]

        weather_data   = get_weather_risk(city=city)
        traffic_data   = get_traffic_data(origin=origin, destination=destination)

        result = calculate_route_risk(
            pothole_detections=potholes_flat,
            accident_detections=accidents_flat,
            weather_data=weather_data,
            traffic_data=traffic_data
        )

        result["weather"] = weather_data
        result["traffic"] = traffic_data

        return result

    finally:
        os.unlink(pothole_path)
        os.unlink(accident_path)


# ── Multi-stop delivery route optimizer (main endpoint)
@app.post("/optimize-route")
async def optimize(
    pothole_video:  UploadFile = File(...),
    accident_video: UploadFile = File(...),
    stops:          str = Form(...)  # comma separated: "Thrissur,Palakkad,Kozhikode"
):
    stops_list = [s.strip() for s in stops.split(",")]

    if len(stops_list) < 2:
        return {"error": "Provide at least 2 stops"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as p_tmp:
        shutil.copyfileobj(pothole_video.file, p_tmp)
        pothole_path = p_tmp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as a_tmp:
        shutil.copyfileobj(accident_video.file, a_tmp)
        accident_path = a_tmp.name

    try:
        pothole_raw    = get_pothole_detections(pothole_path)
        accident_raw   = get_accident_detections(accident_path)

        potholes_flat  = [p for frame in pothole_raw  for p in frame["potholes"]]
        accidents_flat = [a for frame in accident_raw for a in frame["accidents"]]

        segments = get_route_segments(stops_list)

        result = optimize_route(
            stops=stops_list,
            segments=segments,
            pothole_detections=potholes_flat,
            accident_detections=accidents_flat
        )

        return result

    finally:
        os.unlink(pothole_path)
        os.unlink(accident_path)