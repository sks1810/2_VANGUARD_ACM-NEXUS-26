from itertools import permutations
from weather import get_weather_risk
from traffic import get_traffic_data

def analyze_segment(segment, pothole_detections, accident_detections):
    """Score a single segment using all risk factors."""
    from risk_engine.scorer import calculate_route_risk

    weather_data = get_weather_risk(city=segment["from"])
    traffic_data = {
        "normal_duration_min":  segment["normal_duration_min"],
        "traffic_duration_min": segment["traffic_duration_min"]
    }

    result = calculate_route_risk(
        pothole_detections=pothole_detections,
        accident_detections=accident_detections,
        weather_data=weather_data,
        traffic_data=traffic_data
    )

    result["from"]        = segment["from"]
    result["to"]          = segment["to"]
    result["distance_km"] = segment["distance_km"]
    result["weather"]     = weather_data
    result["traffic"]     = traffic_data

    return result

def optimize_route(stops, segments, pothole_detections, accident_detections):
    """
    Analyze all segments and find safest delivery order.
    For demo: scores each segment in given order.
    For full optimization: tries all permutations of middle stops.
    """
    # Score each segment in given order
    scored_segments = []
    for segment in segments:
        scored = analyze_segment(segment, pothole_detections, accident_detections)
        scored_segments.append(scored)

    # Find highest risk segment
    max_risk = max(scored_segments, key=lambda x: x["risk_score"])

    # Overall route risk = average of all segments
    overall_score = round(
        sum(s["risk_score"] for s in scored_segments) / len(scored_segments), 2
    )

    if overall_score >= 0.7:
        overall_level  = "HIGH"
        overall_action = "REPRIORITIZE NOW 🔴"
    elif overall_score >= 0.4:
        overall_level  = "MEDIUM"
        overall_action = "MONITOR ⚠️"
    else:
        overall_level  = "LOW"
        overall_action = "ON TRACK ✅"

    return {
        "optimized_stops":  stops,
        "overall_score":    overall_score,
        "overall_level":    overall_level,
        "overall_action":   overall_action,
        "segments":         scored_segments,
        "highest_risk_segment": {
            "from":       max_risk["from"],
            "to":         max_risk["to"],
            "risk_score": max_risk["risk_score"],
            "risk_level": max_risk["risk_level"],
            "reason":     max_risk["reason"]
        }
    }