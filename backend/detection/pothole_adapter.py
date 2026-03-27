import os
import cv2
import numpy as np
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_MODEL = os.path.join(BASE_DIR, "models", "best.pt")

_model = None

def _load_model(model_path):
    global _model
    if _model is None:
        _model = YOLO(model_path)
    return _model

def get_pothole_detections(video_path, model_path=DEFAULT_MODEL, conf=0.4, iou=0.5, max_frames=100):
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
        h = frame.shape[0]
        results = model.predict(frame, conf=conf, iou=iou, imgsz=640, verbose=False)

        frame_detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])

                bbox_area = (x2 - x1) * (y2 - y1) / (h ** 2)
                y_center_norm = (y1 + y2) / 2 / h
                score = 0.6 * bbox_area + 0.4 * (1 - y_center_norm)

                if score < 0.08:
                    severity = "Low"
                elif score < 0.20:
                    severity = "Medium"
                else:
                    severity = "High"

                frame_detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": round(confidence, 3),
                    "severity": severity
                })

        if frame_detections:
            detections.append({
                "frame": frame_num,
                "potholes": frame_detections
            })

    cap.release()
    return detections