import pandas as pd
import joblib

model = joblib.load("models/random_forest_model.pkl")

# ── Check what columns the model expects ──
print("=" * 50)
print("MODEL EXPECTS THESE FEATURES (in order):")
print("=" * 50)
try:
    print(model.feature_names_in_)
except:
    print("⚠️ Model has no feature_names_in_ attribute")

print()

# ══════════════════════════════════════════
# TEST 1 — 4 AM, no traffic, short route
# ══════════════════════════════════════════
test1 = pd.DataFrame([{
    "route_length_km":          7.4,
    "traffic_density":          200,
    "average_speed_kmph":       32.0,
    "congestion_index":         0.0,
    "hour_of_day":              4,
    "peak_hour_flag":           0,
    "rain_intensity_mm_per_hr": 0.0,
    "visibility_m":             10000,
    "wind_speed_kmph":          6.4,
    "temperature_c":            26.6,
    "strike_activity_level":    0,
    "protest_or_event_flag":    0,
    "road_block_flag":          0,
    "accident_present":         0,
    "travel_time_minutes":      round(7.4 / 32.0 * 60, 2),  # 13.88
    "weather_type_cloudy":      1,
    "weather_type_fog":         0,
    "weather_type_heavy_rain":  0,
    "weather_type_rain":        0
}])
p1 = round(model.predict(test1)[0], 2)
print(f"TEST 1 — 4 AM | short 7.4km | no traffic")
print(f"  travel_time_minutes : {round(7.4/32.0*60, 2)}")
print(f"  Predicted delay     : {p1} min")
print(f"  Total time          : {round(7.4/32.0*60 + p1, 2)} min")
print()

# ══════════════════════════════════════════
# TEST 2 — 8 AM peak, heavy traffic, same distance
# ══════════════════════════════════════════
test2 = pd.DataFrame([{
    "route_length_km":          7.4,
    "traffic_density":          550,
    "average_speed_kmph":       18.0,
    "congestion_index":         0.65,
    "hour_of_day":              8,
    "peak_hour_flag":           1,
    "rain_intensity_mm_per_hr": 0.0,
    "visibility_m":             10000,
    "wind_speed_kmph":          6.4,
    "temperature_c":            26.6,
    "strike_activity_level":    0,
    "protest_or_event_flag":    0,
    "road_block_flag":          0,
    "accident_present":         0,
    "travel_time_minutes":      round(7.4 / 18.0 * 60, 2),  # 24.67
    "weather_type_cloudy":      1,
    "weather_type_fog":         0,
    "weather_type_heavy_rain":  0,
    "weather_type_rain":        0
}])
p2 = round(model.predict(test2)[0], 2)
print(f"TEST 2 — 8 AM peak | same 7.4km | heavy traffic")
print(f"  travel_time_minutes : {round(7.4/18.0*60, 2)}")
print(f"  Predicted delay     : {p2} min")
print(f"  Total time          : {round(7.4/18.0*60 + p2, 2)} min")
print()

# ══════════════════════════════════════════
# TEST 3 — Long route Fort Kochi 16km
# ══════════════════════════════════════════
test3 = pd.DataFrame([{
    "route_length_km":          16.0,
    "traffic_density":          200,
    "average_speed_kmph":       32.0,
    "congestion_index":         0.0,
    "hour_of_day":              4,
    "peak_hour_flag":           0,
    "rain_intensity_mm_per_hr": 0.0,
    "visibility_m":             10000,
    "wind_speed_kmph":          6.4,
    "temperature_c":            26.6,
    "strike_activity_level":    0,
    "protest_or_event_flag":    0,
    "road_block_flag":          0,
    "accident_present":         0,
    "travel_time_minutes":      round(16.0 / 32.0 * 60, 2),  # 30.0
    "weather_type_cloudy":      1,
    "weather_type_fog":         0,
    "weather_type_heavy_rain":  0,
    "weather_type_rain":        0
}])
p3 = round(model.predict(test3)[0], 2)
print(f"TEST 3 — 4 AM | long 16km Fort Kochi | no traffic")
print(f"  travel_time_minutes : {round(16.0/32.0*60, 2)}")
print(f"  Predicted delay     : {p3} min")
print(f"  Total time          : {round(16.0/32.0*60 + p3, 2)} min")
print()

# ══════════════════════════════════════════
# TEST 4 — Accident + rain scenario
# ══════════════════════════════════════════
test4 = pd.DataFrame([{
    "route_length_km":          10.5,
    "traffic_density":          500,
    "average_speed_kmph":       20.0,
    "congestion_index":         0.6,
    "hour_of_day":              9,
    "peak_hour_flag":           1,
    "rain_intensity_mm_per_hr": 8.0,
    "visibility_m":             1000,
    "wind_speed_kmph":          15.0,
    "temperature_c":            24.0,
    "strike_activity_level":    0,
    "protest_or_event_flag":    0,
    "road_block_flag":          0,
    "accident_present":         1,   # ← accident
    "travel_time_minutes":      round(10.5 / 20.0 * 60, 2),  # 31.5
    "weather_type_cloudy":      0,
    "weather_type_fog":         0,
    "weather_type_heavy_rain":  0,
    "weather_type_rain":        1    # ← rain
}])
p4 = round(model.predict(test4)[0], 2)
print(f"TEST 4 — 9 AM peak | 10.5km | accident + rain")
print(f"  travel_time_minutes : {round(10.5/20.0*60, 2)}")
print(f"  Predicted delay     : {p4} min")
print(f"  Total time          : {round(10.5/20.0*60 + p4, 2)} min")
print()

# ══════════════════════════════════════════
# SANITY CHECK — delays must vary
# ══════════════════════════════════════════
print("=" * 50)
print("SANITY CHECK")
print("=" * 50)
print(f"  Test1 delay (4AM, short, clear)    : {p1} min")
print(f"  Test2 delay (8AM, same dist, peak) : {p2} min  ← must be > Test1")
print(f"  Test3 delay (4AM, long 16km)       : {p3} min  ← must be > Test1")
print(f"  Test4 delay (9AM, accident+rain)   : {p4} min  ← must be highest")
print()

if p2 > p1:
    print("✅ Peak hour correctly increases delay")
else:
    print("❌ Peak hour not affecting delay — check feature order")

if p3 > p1:
    print("✅ Longer route correctly increases delay")
else:
    print("❌ Route length not affecting delay — check travel_time_minutes")

if p4 > p2:
    print("✅ Accident + rain correctly spikes delay")
else:
    print("❌ Accident/rain not affecting delay — check one-hot encoding")