"""HiveBox API - Beekeeper environmental monitoring."""
from datetime import datetime, timezone, timedelta
import os
import requests
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

SENSEBOXES = os.getenv(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
).split(",")


def get_temperature_status(average):
    """Return status string based on temperature average."""
    if average < 10:
        return "Too Cold"
    if average <= 36:
        return "Good"
    return "Too Hot"


def get_temperature(box_id):
    """Fetch temperature from a senseBox, return None if stale or missing."""
    url = f"https://api.opensensemap.org/boxes/{box_id}"
    response = requests.get(url, timeout=10)
    data = response.json()
    for sensor in data["sensors"]:
        if "temperatur" in sensor["title"].lower():
            measurement = sensor["lastMeasurement"]
            measured_at = datetime.fromisoformat(
                measurement["createdAt"].replace("Z", "+00:00")
            )
            age = datetime.now(timezone.utc) - measured_at
            if age > timedelta(hours=1):
                return None
            return float(measurement["value"])
    return None


@app.route("/version")
def version():
    """Return current application version."""
    return jsonify({"version": "0.0.1"})


@app.route("/temperature")
def temperature():
    """Return average temperature from all configured senseBoxes."""
    readings = []
    for box_id in SENSEBOXES:
        temp = get_temperature(box_id)
        if temp is not None:
            readings.append(temp)
    if not readings:
        return jsonify({"error": "No temperature data available"}), 503
    average = round(sum(readings) / len(readings), 2)
    return jsonify({
        "temperature": average,
        "unit": "celsius",
        "boxes_used": len(readings),
        "status": get_temperature_status(average)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
