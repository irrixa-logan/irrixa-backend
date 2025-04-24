 # irrixa_config_server.py – Backend API with Auto-Trigger Engine
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, subprocess

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "Configs")
ENGINE_PATH = os.path.join(BASE_DIR, "src", "irrigation_engine.py")
os.makedirs(CONFIG_DIR, exist_ok=True)

@app.route('/api/save_config/<block_name>', methods=['POST'])
def save_block_config(block_name):
    try:
        data = request.get_json()
        filename = os.path.join(CONFIG_DIR, f"{block_name}.json")

        # Load existing config if it exists
        if os.path.exists(filename):
            with open(filename, "r") as f:
                existing = json.load(f)
        else:
            existing = {}

        # Update with incoming fields
        for key in ["crop", "crop_stage", "irrigation_type", "application_rate_mm_hr"]:
            if key in data:
                existing[key] = data[key]

        with open(filename, "w") as f:
            json.dump(existing, f, indent=2)

        # 🔁 Auto-run irrigation engine
        subprocess.run(["python", ENGINE_PATH], check=True)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
