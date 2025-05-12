# -*- coding: utf-8 -*-
from flask import Flask, jsonify
import subprocess
import datetime

app = Flask(__name__)

@app.route("/api/run_engine", methods=["POST"])
def run_engine():
    try:
        subprocess.run(["python", "src/weather_fetcher.py"], check=True)
        subprocess.run(["python", "src/ndvi_fetcher.py"], check=True)
        subprocess.run(["python", "src/irrigation_engine.py"], check=True)

        return jsonify({
            "status": "success",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
