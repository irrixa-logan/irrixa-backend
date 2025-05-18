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
        return jsonify({"error": "Folder not found"}), 404

    results = []
    for filename in os.listdir(folder):
        if filename.endswith("_irrigation.json"):
            file_path = os.path.join(folder, filename)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

    return jsonify(results)


    if not os.path.exists(block_file):
        return jsonify({"error": "File not found"}), 404

    with open(block_file, "r") as f:
        data = json.load(f)
        return jsonify(data)

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)

