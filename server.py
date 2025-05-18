from flask import Flask, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

@app.route("/api/irrigation-results", methods=["GET"])
def get_irrigation_results():
    today = "2025-05-17"
    block_file = os.path.join("Irrigation_Outputs", today, "D2_Bay_1_irrigation.json")

    if not os.path.exists(block_file):
        return jsonify({"error": "File not found"}), 404

    with open(block_file, "r") as f:
        data = json.load(f)
        return jsonify(data)

if __name__ == "__main__":
    app.run(port=5000)
