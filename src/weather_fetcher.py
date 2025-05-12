 # ✅ Irrixa MK1 – Upgraded weather_fetcher.py (Tomorrow.io Free Tier, Full Field Set)
import os
import requests
import datetime
import json
import shutil
from dotenv import load_dotenv

# === Config ===
LAT = -34.509878
LON = 142.348070

# === Load API Key ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
API_KEY = os.getenv("TOMORROW_API_KEY")
if not API_KEY:
    raise Exception("❌ TOMORROW_API_KEY not found in .env")

# === Output Directory Setup ===
today = datetime.date.today()
base_dir = os.path.dirname(os.path.dirname(__file__))
weather_dir = os.path.join(base_dir, "Weather", str(today))
os.makedirs(weather_dir, exist_ok=True)

# === Date Strings ===
today_str = str(today)
yesterday_str = str(today - datetime.timedelta(days=1))
tomorrow_str = str(today + datetime.timedelta(days=1))

# === Time Range ===
now = datetime.datetime.utcnow()
start_time = (now - datetime.timedelta(days=1)).isoformat() + "Z"
end_time = (now + datetime.timedelta(days=1)).isoformat() + "Z"

# === Free Tier Safe Fields ===
fields = [
    "temperature",
    "humidity",
    "windSpeed",
    "solarGHI",
    "precipitationAccumulation",
    "evapotranspiration",
    "cloudCover",
    "pressureSeaLevel",
    "dewPoint",
    "windDirection",
    "visibility",
    "sunriseTime",
    "sunsetTime"
]

# === API Request ===
url = (
    f"https://api.tomorrow.io/v4/timelines?"
    f"location={LAT},{LON}&fields={','.join(fields)}"
    f"&timesteps=1d&units=metric&apikey={API_KEY}"
    f"&startTime={start_time}&endTime={end_time}"
)
print(f"🌤️  Requesting 3-day weather data from Tomorrow.io for ({LAT}, {LON})")
response = requests.get(url)
if response.status_code != 200:
    print("❌ API Error:", response.status_code, response.text)
    raise Exception("Failed to fetch weather data")

weather_data = response.json()

# === Process Data ===
try:
    intervals = weather_data["data"]["timelines"][0]["intervals"]
    print("🔍 Intervals fetched:", intervals)
    if not intervals:
        raise Exception("❌ No weather intervals returned from Tomorrow.io")

    final = []

    for entry in intervals:
        date_str = entry["startTime"].split("T")[0]
        values = entry["values"]

        item = {
            "date": date_str,
            "temp_avg": values.get("temperature") or 20,
            "humidity": values.get("humidity") or 60,
            "wind_speed": values.get("windSpeed") or 2,
            "solar_ghi": values.get("solarGHI") or 20,
            "precip_mm": values.get("precipitationAccumulation") or 0.0,
            "eto": values.get("evapotranspiration") or 0.0,
            "cloud_cover": values.get("cloudCover") or 40,
            "pressure": values.get("pressureSeaLevel") or 1010,
            "dew_point": values.get("dewPoint") or 12,
            "wind_direction": values.get("windDirection") or 180,
            "visibility_km": values.get("visibility") or 10,
            "sunrise": values.get("sunriseTime") or "",
            "sunset": values.get("sunsetTime") or "",
            "rain_yesterday": 0,
            "rain_forecast": 0
        }

        print(f"📅 {date_str} | ETo: {item['eto']} mm | Rain: {item['precip_mm']} mm | Solar: {item['solar_ghi']} W/m²")
        final.append(item)

    # === Add 72h logic (yesterday + tomorrow rain)
    for day in final:
        if day["date"] == today_str:
            for other in final:
                if other["date"] == yesterday_str:
                    day["rain_yesterday"] = other.get("precip_mm", 0.0)
                if other["date"] == tomorrow_str:
                    day["rain_forecast"] = other.get("precip_mm", 0.0)

    # === Save JSON to Irrixa Weather folder
    save_path = os.path.join(weather_dir, "weather_data.json")
    with open(save_path, "w") as f:
        json.dump(final, f, indent=2)
    print(f"✅ Weather data saved to {save_path}")

    # === Auto-copy to dashboard public folder
    dash_weather_dir = os.path.join(base_dir, "dashboard", "public", "Weather", str(today))
    os.makedirs(dash_weather_dir, exist_ok=True)
    shutil.copy(save_path, os.path.join(dash_weather_dir, "weather_data.json"))
    print(f"🔁 Weather file auto-copied to dashboard: {dash_weather_dir}")

except Exception as e:
    print("❌ Failed to parse weather data:", e)
    raise
