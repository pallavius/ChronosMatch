import json
from pathlib import Path

from flask import Flask, jsonify, render_template

app = Flask(__name__)

ROOT = Path(__file__).resolve().parent
SNAPSHOT_PATH = ROOT / "book_snapshot.json"


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/snapshot")
def get_snapshot():
    try:
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        return jsonify(data)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return jsonify({"error": "Waiting for engine data"}), 503


if __name__ == "__main__":
    app.run(debug=False, port=5000)


