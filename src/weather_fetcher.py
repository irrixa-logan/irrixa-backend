 # ✅ Upgraded Irrixa MK1 – weather_fetcher.py (Tomorrow.io Free Tier + Full Integration)
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

# === Date Logic ===
today_str = str(today)
yesterday_str = str(today - datetime.timedelta(days=1))
tomorrow_str = str(today + datetime.timedelta(days=1))

# === Time Range ===
now = datetime.datetime.utcnow()
start_time = (now - datetime.timedelta(days=1)).isoformat() + "Z"
end_time = (now + datetime.timedelta(days=1)).isoformat() + "Z"

# === Fields to Fetch ===
fields = [
    "temperature", "humidity", "windSpeed", "precipitationIntensity", "solarGHI"
]

# === API Request ===
url = f"https://api.tomorrow.io/v4/timelines?location={LAT},{LON}&fields={','.join(fields)}&timesteps=1d&units=metric&apikey={API_KEY}&startTime={start_time}&endTime={end_time}"
print("🌤️  Requesting 3-day weather data from Tomorrow.io")
response = requests.get(url)
if response.status_code != 200:
    print("❌ API Error:", response.status_code, response.text)
    raise Exception("Failed to fetch weather data")

weather_data = response.json()

# === Process Data ===
try:
    intervals = weather_data["data"]["timelines"][0]["intervals"]
    final = []

    for entry in intervals:
        date_str = entry["startTime"].split("T")[0]
        values = entry["values"]

        temp = values.get("temperature")
        solar = values.get("solarGHI") or 20

        # Fake ETo Estimate (Hargreaves-style)
        eto = round(0.0023 * ((temp or 20) + 17) * solar, 2)

        item = {
            "date": date_str,
            "temp_min": temp,  # Free tier only has single temp
            "temp_max": temp,
            "humidity": values.get("humidity"),
            "wind_speed": values.get("windSpeed"),
            "solar_ghi": solar,
            "precip_mm": values.get("precipitationIntensity"),
            "eto_estimated": eto,
            "rain_yesterday": 0,
            "rain_forecast": 0
        }

        final.append(item)

    # Add 72h logic (yesterday/today/tomorrow)
    for day in final:
        if day["date"] == today_str:
            for other in final:
                if other["date"] == yesterday_str:
                    day["rain_yesterday"] = other.get("precip_mm", 0)
                if other["date"] == tomorrow_str:
                    day["rain_forecast"] = other.get("precip_mm", 0)

    # Save JSON
    save_path = os.path.join(weather_dir, "weather_data.json")
    with open(save_path, "w") as f:
        json.dump(final, f, indent=2)
    print(f"✅ Weather data saved to {save_path}")

    # Dashboard Copy
    dash_weather_dir = os.path.join(base_dir, "dashboard", "public", "Weather", str(today))
    os.makedirs(dash_weather_dir, exist_ok=True)
    shutil.copy(save_path, os.path.join(dash_weather_dir, "weather_data.json"))
    print(f"🔁 Weather file auto-copied to dashboard: {dash_weather_dir}")

except Exception as e:
    print("❌ Failed to parse weather data:", e)
    raise