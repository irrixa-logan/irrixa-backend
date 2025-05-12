# ✅ Full Irrixa MK1 – irrigation_engine.py (with Persistent Actual Irrigation Logger)
import os
import json
import datetime
import csv
import shutil

# === Paths & Config ===
base_dir = os.path.dirname(os.path.dirname(__file__))
today_str = str(datetime.date.today())
ndvi_dir = os.path.join(base_dir, "NDVI", today_str)
weather_path = os.path.join(base_dir, "Weather", today_str, "weather_data.json")
config_dir = os.path.join(base_dir, "Configs")
global_config_path = os.path.join(config_dir, "global_settings.json")
irrigation_output_dir = os.path.join(base_dir, "Irrigation_Outputs", today_str)
dash_data_path = os.path.join(irrigation_output_dir, "block_irrigation.json")
dash_public_copy = os.path.join(base_dir, "dashboard", "public", "data", "block_irrigation.json")
ndvi_history_path = os.path.join(base_dir, "NDVI_HISTORY", "ndvi_history.json")
actual_log_persistent = os.path.join(base_dir, "actual_irrigation_log.json")

os.makedirs(irrigation_output_dir, exist_ok=True)
os.makedirs(os.path.dirname(ndvi_history_path), exist_ok=True)

# === Load NDVI history ===
try:
    with open(ndvi_history_path, "r") as f:
        ndvi_history = json.load(f)
except:
    ndvi_history = {}

# === Load global config ===
try:
    with open(global_config_path, "r") as f:
        global_config = json.load(f)
except:
    global_config = { "default_index_weights": {}, "rain_override_enabled": True }

# === Load actual irrigation log (persistent across days) ===
try:
    with open(actual_log_persistent, "r") as f:
        full_actual_log = json.load(f)
    actual_log = full_actual_log.get(today_str, {})
except:
    full_actual_log = {}
    actual_log = {}

# === Load weather ===
try:
    with open(weather_path, "r") as f:
        weather_data = json.load(f)
    today_weather = next(d for d in weather_data if d["date"] == today_str)
    eto_today = today_weather.get("eto_estimated", 5.5)
    rain_mm = today_weather.get("precip_mm", 0)
    rain_yesterday = today_weather.get("rain_yesterday", 0)
    rain_forecast = today_weather.get("rain_forecast", 0)
    temp_min = today_weather.get("temp_min", 10)
    temp_max = today_weather.get("temp_max", 30)
except:
    eto_today = 5.5
    rain_mm = 0
    rain_yesterday = 0
    rain_forecast = 0
    temp_min = 10
    temp_max = 30
    print("❌ Weather load failed – fallback ETo 5.5 mm")

# === Apply .txt override if it exists ===
override_path = os.path.join(base_dir, "Weather", "daily_eto_override.txt")
if os.path.exists(override_path):
    try:
        with open(override_path, "r") as f:
            eto_today = float(f.read().strip())
        print(f"⚠️ ETo override active: {eto_today} mm")
    except:
        print("⚠️ Failed to read ETo override, using default")

rain_72h = rain_yesterday + rain_mm + rain_forecast

# === Load NDVI summary ===
summary_files = [f for f in os.listdir(ndvi_dir) if f.endswith("_summary.json")]
csv_rows = []
dash_data = []

for file in summary_files:
    with open(os.path.join(ndvi_dir, file), "r") as f:
        data = json.load(f)

    block = data["block"]
    config_path = os.path.join(config_dir, f"{block}.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}

    ndvi_mode = config.get("ndvi_display_mode", "average")
    ndvi_avg = data.get("ndvi")
    ndvi_p80 = data.get("ndvi_p80")
    ndvi = ndvi_p80 if ndvi_mode == "p80" and ndvi_p80 is not None else ndvi_avg

    evi = data.get("evi", ndvi)
    gndvi = data.get("gndvi", ndvi)
    ndre = data.get("ndre", ndvi)
    confidence = data.get("confidence_score", 100)
    fallback = data.get("fallback_used", False)

    last_ndvi = ndvi_history.get(block)
    if last_ndvi is not None and ndvi is not None:
        ndvi_change = round(((ndvi - last_ndvi) / last_ndvi * 100), 1)
    else:
        ndvi_change = 0
    ndvi_history[block] = ndvi

    efficiency = config.get("efficiency", 0.95)
    application_rate = config.get("application_rate_mm_hr", 10)
    irrigation_type = config.get("irrigation_type", "unknown")
    crop = config.get("crop", "unknown")
    crop_stage = config.get("crop_stage", "unspecified")
    features = config.get("features", {})
    notes = config.get("notes", [])
    soil_type = config.get("soil_type", "loam")
    raw_used = config.get("raw_mm_per_m", 55)

    weights = global_config["default_index_weights"].get(crop, global_config["default_index_weights"].get("default", {"ndvi": 1, "evi": 0, "gndvi": 0, "ndre": 0}))
    raw_kc = (
    ndvi * weights.get("ndvi", 0) +
    evi * weights.get("evi", 0) +
    gndvi * weights.get("gndvi", 0) +
    ndre * weights.get("ndre", 0)
)



    if crop in ["beans", "broccoli"]:
        kc = min(round(raw_kc * 1.25, 3), 1.25)
    elif crop in ["citrus", "grapes", "almonds"]:
        kc = min(round(raw_kc * 1.1, 3), 1.2)
    else:
        kc = min(round(raw_kc * 1.25, 3), 1.2)

    etc = round(kc * eto_today, 2)
    etc_adj = round(etc / efficiency, 2)
    effective_rain = min(rain_mm, etc_adj) if global_config.get("rain_override_enabled", True) else 0
    irrigation_mm = max(etc_adj - effective_rain, 0)
    irrigation_minutes = round((irrigation_mm / application_rate) * 60, 1) if application_rate > 0 else None

    split_recommended = False
    split_into = []
    if irrigation_minutes:
        if irrigation_minutes > 30:
            split_recommended = True
            split_into = [round(irrigation_minutes / 3, 1)] * 3
        elif irrigation_minutes > 15:
            split_recommended = True
            split_into = [round(irrigation_minutes / 2, 1)] * 2

    priority_score = round(etc * (confidence / 100), 2)

    actual_irrigation = actual_log.get(block)
    irrigation_gap = None
    if actual_irrigation is not None:
        irrigation_gap = round(actual_irrigation - irrigation_mm, 2)

    result = {
        "block": block,
        "date": today_str,
        "ndvi": ndvi,
        "ndvi_avg": ndvi_avg,
        "ndvi_p80": ndvi_p80,
        "evi": evi,
        "gndvi": gndvi,
        "ndre": ndre,
        "kc": kc,
        "eto": eto_today,
        "etc": etc,
        "efficiency": efficiency,
        "irrigation_type": irrigation_type,
        "application_rate_mm_hr": application_rate,
        "irrigation_mm": irrigation_mm,
        "irrigation_minutes": irrigation_minutes,
        "confidence_score": confidence,
        "rain_mm": rain_mm,
        "fallback_used": fallback,
        "crop": crop,
        "crop_stage": crop_stage,
        "features": features,
        "notes": notes,
        "priority_score": priority_score,
        "why_this_recommendation": f"ETo = {eto_today} mm | NDVI change: {ndvi_change}% | {f'Crop stage: {crop_stage}' if crop_stage != 'unspecified' else ''} | {'Rainfall override enabled' if effective_rain > 0 else 'No rainfall applied'}",
        "soil_type": soil_type,
        "raw_mm_used": raw_used,
        "split_recommended": split_recommended,
        "split_into": split_into,
        "ndvi_change": ndvi_change,
        "stress_flag": ndvi_change <= -10,
        "ndvi_display_mode": ndvi_mode,
        "kc_components": {
            "weights": weights,
            "raw_kc": round(raw_kc, 3),
            "final_kc": kc
        },
        "actual_irrigation_mm": actual_irrigation,
        "irrigation_gap": irrigation_gap
    }

    dash_data.append(result)

    with open(os.path.join(irrigation_output_dir, f"{block}_irrigation.json"), "w") as f:
        json.dump(result, f, indent=2)

    print(f"💧 {block}: {irrigation_mm} mm → {irrigation_minutes} min (ETc={etc_adj}, Eff={efficiency}, Rain={rain_mm})")

    csv_rows.append([
        block, today_str, ndvi, kc, eto_today,
        irrigation_mm, irrigation_minutes, confidence,
        efficiency, rain_mm
    ])

with open(os.path.join(irrigation_output_dir, "irrixa_summary.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["block", "date", "ndvi", "kc", "eto", "irrigation_mm", "irrigation_minutes", "confidence", "efficiency", "rain_mm"])
    writer.writerows(csv_rows)

with open(dash_data_path, "w") as f:
    json.dump(dash_data, f, indent=2)
print(f"📊 Dashboard JSON saved: {dash_data_path}")

with open(ndvi_history_path, "w") as f:
    json.dump(ndvi_history, f, indent=2)

if global_config.get("auto_sync_dashboard", True):
    try:
        os.makedirs(os.path.dirname(dash_public_copy), exist_ok=True)
        shutil.copyfile(dash_data_path, dash_public_copy)
        print(f"📲 Dashboard data auto-synced to: {dash_public_copy}")
    except Exception as e:
        print(f"⚠️  Dashboard sync failed: {e}")
 