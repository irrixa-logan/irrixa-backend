from flask import Flask, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

@app.route("/api/irrigation-results", methods=["GET"])
def get_irrigation_results():
    today = "2025-05-17"
    folder = os.path.join(os.path.dirname(__file__), "Irrigation_Outputs", today)

    if not os.path.exists(folder):
        return jsonify([])  # Return an empty list, not an error

    results = []
    for filename in os.listdir(folder):
        if filename.endswith("_irrigation.json"):
            file_path = os.path.join(folder, filename)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        results.extend(data)  # Flatten any nested list
                    elif isinstance(data, dict):
                        results.append(data)
            except Exception as e:
                print(f"⚠️ Skipped {filename}: {e}")

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

