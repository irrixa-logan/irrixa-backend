from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import subprocess
from datetime import date

# === Init Flask ===
app = Flask(__name__)
CORS(app)

# === Set Paths ===
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Configs"))
ENGINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "irrigation_engine.py"))
WEATHER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "weather_fetcher.py"))
ACTUALS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "actual_irrigation_log.json"))

# === Save Config + Auto-run Engine ===
@app.route("/api/save_config/<block_name>", methods=["POST"])
def save_config(block_name):
    try:
        data = request.get_json(force=True)
        block_path = os.path.join(CONFIG_DIR, f"{block_name}.json")

        print(f"📝 Save request received for: {block_name}")
        print(f"📦 Incoming data: {data}")
        print(f"📁 Saving to: {block_path}")

        if not os.path.exists(block_path):
            return jsonify({"error": f"Block config not found: {block_path}"}), 404

        with open(block_path, "r") as f:
            config = json.load(f)

        config.update(data)

        with open(block_path, "w") as f:
            json.dump(config, f, indent=2)

        print("✅ Config file updated successfully")
        print(f"⚙️ Running irrigation engine: {ENGINE_PATH}")

        result = subprocess.run(
            ["python", ENGINE_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode == 0:
            print("✅ Engine executed successfully")
            print(result.stdout)
        else:
            print("❌ Engine execution failed")
            print(result.stderr)

        return jsonify({"status": "saved and engine run"})

    except Exception as e:
        print(f"❌ Error during save or engine run: {e}")
        return jsonify({"error": str(e)}), 500

# === Save Actual Irrigation Applied ===
@app.route("/api/save_actual_irrigation", methods=["POST"])
def save_actual_irrigation():
    try:
        data = request.get_json(force=True)
        today_str = data.get("date") or str(date.today())
        block = data.get("block")
        mm = data.get("mm")

        if not block or mm is None:
            return jsonify({"error": "Missing block or mm"}), 400

        print(f"📥 Saving actual irrigation for {block} on {today_str}: {mm} mm")

        if os.path.exists(ACTUALS_PATH):
            with open(ACTUALS_PATH, "r") as f:
                full_log = json.load(f)
        else:
            full_log = {}

        full_log.setdefault(today_str, {})[block] = mm

        with open(ACTUALS_PATH, "w") as f:
            json.dump(full_log, f, indent=2)

        print(f"✅ Saved irrigation for {block}: {mm} mm")
        return jsonify({"status": "success"})

    except Exception as e:
        print(f"❌ Exception in save_actual_irrigation: {e}")
        return jsonify({"error": str(e)}), 500

# === Manual Run: Engine Only ===
@app.route("/api/run_engine", methods=["POST"])
def run_engine_only():
    try:
        print("🔁 Manual engine run requested")
        result = subprocess.run(
            ["python", ENGINE_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode == 0:
            print("✅ Engine executed manually")
            print(result.stdout)
            return jsonify({"status": "success", "output": result.stdout})
        else:
            print("❌ Engine run failed")
            print(result.stderr)
            return jsonify({"status": "error", "error": result.stderr}), 500

    except Exception as e:
        print(f"❌ Engine run exception: {e}")
        return jsonify({"error": str(e)}), 500

# === Manual Run: Weather Only ===
@app.route("/api/refresh_weather", methods=["POST"])
def refresh_weather():
    try:
        print(f"🌤️ Weather refresh requested: {WEATHER_PATH}")

        result = subprocess.run(
            ["python", WEATHER_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode == 0:
            print("✅ Weather updated")
            print(result.stdout)
            return jsonify({"status": "success", "output": result.stdout})
        else:
            print("❌ Weather update failed")
            print(result.stderr)
            return jsonify({"status": "error", "error": result.stderr}), 500

    except Exception as e:
        print(f"❌ Weather refresh exception: {e}")
        return jsonify({"error": str(e)}), 500

# === Run Flask Server ===
if __name__ == "__main__":
    print("🔥 Irrixa Flask backend running on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001)
