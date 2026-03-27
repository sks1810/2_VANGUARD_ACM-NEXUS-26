import os
import cv2
import numpy as np
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_MODEL = os.path.join(BASE_DIR, "models", "yolov8n.pt")

_model = None

def _load_model(model_path):
    global _model
    if _model is None:
        _model = YOLO(model_path)
    return _model

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea + 1e-5)

def get_accident_detections(video_path, model_path=DEFAULT_MODEL, iou_thresh=0.25, max_frames=100):
    model = _load_model(model_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    detections = []
    frame_num = 0

    while cap.isOpened() and frame_num < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1
        results = model(frame, verbose=False)[0]
        vehicles = []

        for box in results.boxes:
            cls = int(box.cls[0])
            if cls in [2, 3, 5, 7]:  # car, motorcycle, bus, truck
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                vehicles.append({"bbox": [x1, y1, x2, y2], "confidence": round(conf, 3)})

        accidents = []
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                iou = compute_iou(vehicles[i]["bbox"], vehicles[j]["bbox"])
                if iou > iou_thresh:
                    accidents.append({
                        "vehicle_1": vehicles[i],
                        "vehicle_2": vehicles[j],
                        "iou": round(iou, 3)
                    })

        if accidents:
            detections.append({
                "frame": frame_num,
                "accidents": accidents
            })

    cap.release()
    return detections