import cv2
import os
from ultralytics import YOLO

def get_pothole_detections(video_path, model_path, conf=0.4, iou=0.5, max_frames=100):
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

        frame_h = frame.shape[0]
        results = model.predict(frame, conf=conf, iou=iou, imgsz=640, verbose=False)

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])

                bbox_area = (x2 - x1) * (y2 - y1) / (frame_h ** 2)
                y_center_norm = (y1 + y2) / 2 / frame_h
                severity_score = 0.6 * bbox_area + 0.4 * (1 - y_center_norm)

                if severity_score < 0.002:
                    severity = "Low"
                elif severity_score < 0.01:
                    severity = "Medium"
                else:
                    severity = "High"

                all_detections.append({
                    "class": "pothole",
                    "confidence": round(confidence, 2),
                    "severity": severity,
                    "frame": frame_count
                })

        frame_count += 1

    cap.release()
    return all_detections


if __name__ == "__main__":
    detections = get_pothole_detections(
        video_path="test.mp4",
        model_path="models/yolov12n.pt"
    )
    print(f"✅ Potholes detected: {len(detections)}")
    for d in detections[:5]:
        print(d)