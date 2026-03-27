import cv2
import numpy as np
from ultralytics import YOLO
import os

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea + 1e-5)

def get_accident_detections(video_path, model_path, iou_thresh=0.25, max_frames=100):
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return []

    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return []

    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)
    all_detections = []
    frame_count = 0

    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)[0]
        vehicles = []

        for box in results.boxes:
            cls = int(box.cls[0])
            if cls in [2, 3, 5, 7]:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                vehicles.append((x1, y1, x2, y2, conf))

        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                box1 = vehicles[i][:4]
                box2 = vehicles[j][:4]
                iou = compute_iou(box1, box2)
                if iou > iou_thresh:
                    avg_conf = (vehicles[i][4] + vehicles[j][4]) / 2
                    all_detections.append({
                        "class": "accident",
                        "confidence": round(avg_conf, 2),
                        "severity": "High",
                        "frame": frame_count,
                        "iou_score": round(iou, 2)
                    })

        frame_count += 1

    cap.release()
    return all_detections


if __name__ == "__main__":
    detections = get_accident_detections(
        video_path="test.mp4",
        model_path="models/yolov8n.pt"
    )
    print(f"✅ Accidents detected: {len(detections)}")
    for d in detections[:5]:
        print(d)