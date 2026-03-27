def calculate_route_risk(pothole_detections, accident_detections, weather_data, traffic_data=None):

    # ── Weight 1: Potholes
    severity_weights = {"Low": 0.2, "Medium": 0.5, "High": 1.0}
    pothole_score = 0.0
    if pothole_detections:
        total = sum(
            severity_weights.get(d.get("severity", "Low"), 0.2) * d["confidence"]
            for d in pothole_detections
        )
        pothole_score = min(total / max(len(pothole_detections), 1), 1.0)

    # ── Weight 2: Accidents
    accident_score = 0.0
    if accident_detections:
        accident_score = min(
            sum(
                (d["vehicle_1"]["confidence"] + d["vehicle_2"]["confidence"]) / 2
                for d in accident_detections
            ) / max(len(accident_detections), 1),
            1.0
        )

    # ── Weight 3: Weather
    weather_score = weather_data.get("weather_risk", 0.1)

    # ── Weight 4: Traffic (optional)
    traffic_score = 0.0
    if traffic_data:
        normal = traffic_data.get("normal_duration_min", 1)
        actual = traffic_data.get("traffic_duration_min", 1)
        delay_ratio = (actual - normal) / max(normal, 1)
        traffic_score = min(max(delay_ratio, 0.0), 1.0)

    # ── Final weighted score
    final_score = (
        0.30 * accident_score +
        0.25 * pothole_score  +
        0.25 * weather_score  +
        0.20 * traffic_score
    )

    final_score = round(min(final_score, 1.0), 2)

    # ── Risk level
    if final_score >= 0.7:
        risk_level = "HIGH"
        action = "REPRIORITIZE NOW 🔴"
    elif final_score >= 0.4:
        risk_level = "MEDIUM"
        action = "MONITOR ⚠️"
    else:
        risk_level = "LOW"
        action = "ON TRACK ✅"

    # ── Reasons
    reasons = []
    if accident_detections:
        reasons.append(f"{len(accident_detections)} accident(s) detected")
    if pothole_detections:
        high = sum(1 for p in pothole_detections if p.get("severity") == "High")
        med  = sum(1 for p in pothole_detections if p.get("severity") == "Medium")
        reasons.append(f"{len(pothole_detections)} pothole(s) — {high} High, {med} Medium")
    if weather_score >= 0.7:
        reasons.append(f"Severe weather: {weather_data.get('description', 'unknown')}")
    elif weather_score >= 0.5:
        reasons.append(f"Poor weather: {weather_data.get('description', 'unknown')}")
    if traffic_score >= 0.5:
        reasons.append("Heavy traffic delay on route")

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "action": action,
        "reason": " | ".join(reasons) if reasons else "Route clear",
        "breakdown": {
            "accident": round(accident_score, 2),
            "pothole": round(pothole_score, 2),
            "weather": round(weather_score, 2),
            "traffic": round(traffic_score, 2)
        }
    }


if __name__ == "__main__":
    test_potholes = [
        {"class": "pothole", "confidence": 0.87, "severity": "High"},
        {"class": "pothole", "confidence": 0.65, "severity": "Medium"},
    ]
    test_accidents = [
        {
            "vehicle_1": {"confidence": 0.91, "bbox": [0,0,100,100]},
            "vehicle_2": {"confidence": 0.85, "bbox": [50,50,150,150]},
            "iou": 0.43
        }
    ]
    test_weather = {
        "weather_risk": 0.7,
        "description": "heavy rain"
    }

    result = calculate_route_risk(test_potholes, test_accidents, test_weather)
    print("\n── Route Risk Result ──")
    for k, v in result.items():
        print(f"{k}: {v}")