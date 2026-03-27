import cv2
import sys
from detection.accident_adapter import get_accident_detections

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "crash1.mp4"

cap = cv2.VideoCapture(VIDEO)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()

results = get_accident_detections(VIDEO, max_frames=total_frames)
detections_by_frame = {d["frame"]: d["accidents"] for d in results}

cap = cv2.VideoCapture(VIDEO)
frame_num = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    for acc in detections_by_frame.get(frame_num, []):
        for key, color in [("vehicle_1", (0, 255, 255)), ("vehicle_2", (0, 165, 255))]:
            x1, y1, x2, y2 = acc[key]["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cx = (acc["vehicle_1"]["bbox"][0] + acc["vehicle_2"]["bbox"][2]) // 2
        cy = (acc["vehicle_1"]["bbox"][1] + acc["vehicle_2"]["bbox"][3]) // 2
        cv2.putText(frame, f"ACCIDENT iou={acc['iou']}", (cx - 60, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Accident Detection", frame)
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()