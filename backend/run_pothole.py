import cv2
import sys
from detection.pothole_adapter import get_pothole_detections

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "short_poth.mp4"
COLORS = {"Low": (0, 255, 0), "Medium": (0, 165, 255), "High": (0, 0, 255)}

cap = cv2.VideoCapture(VIDEO)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()

results = get_pothole_detections(VIDEO, max_frames=total_frames)
detections_by_frame = {d["frame"]: d["potholes"] for d in results}

cap = cv2.VideoCapture(VIDEO)
frame_num = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    for p in detections_by_frame.get(frame_num, []):
        x1, y1, x2, y2 = p["bbox"]
        color = COLORS[p["severity"]]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"Pothole {p['severity']} {p['confidence']:.2f}",
                    (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Pothole Detection", frame)
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()