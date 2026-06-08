import os
from datetime import datetime, timezone, timedelta
import requests
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

APP_VERSION = "0.0.2"

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# senseBox IDs are configurable via env var — Phase 4 requirement.
# Fallback to the original 3 boxes if the env var is not set.
SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
).split(",")

OPENSENSEMAP_API = "https://api.opensensemap.org/boxes"

# Data must not be older than this
MAX_DATA_AGE_HOURS = 1


def get_temperature_from_box(box_id):
    """
    Fetches temperature reading from a single senseBox.
    Returns the temperature as float, or None if:
    - The box is unreachable
    - No temperature sensor found
    - Data is older than 1 hour
    """
    try:
        response = requests.get(
            f"{OPENSENSEMAP_API}/{box_id}",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        for sensor in data.get("sensors", []):
            if "temp" in sensor.get("title", "").lower():
                measurement = sensor.get("lastMeasurement")
                if not measurement:
                    return None

                created_at = datetime.fromisoformat(
                    measurement["createdAt"].replace("Z", "+00:00")
                )
                age = datetime.now(timezone.utc) - created_at

                if age > timedelta(hours=MAX_DATA_AGE_HOURS):
                    return None

                return float(measurement["value"])

    except Exception:  # pylint: disable=broad-except
        return None

    return None


def get_temperature_status(average):
    """
    Returns a human-readable status based on the average temperature.
    - Below 10:   Too Cold
    - 10 to 36:   Good
    - Above 36:   Too Hot
    """
    if average < 10:
        return "Too Cold"
    if average <= 36:
        return "Good"
    return "Too Hot"


@app.route("/version")
def get_version():
    """
    GET /version
    Returns the current running version of HiveBox.
    """
    return jsonify({"version": APP_VERSION})


@app.route("/temperature")
def get_temperature():
    """
    GET /temperature
    Returns average temperature from all senseBox devices.
    Only includes readings from the last hour.
    """
    readings = [
        temp
        for box_id in SENSEBOX_IDS
        if (temp := get_temperature_from_box(box_id)) is not None
    ]

    if not readings:
        return jsonify({
            "error": "No valid temperature data available",
            "detail": "All senseBox readings are older than 1 hour or unavailable"
        }), 503

    average = round(sum(readings) / len(readings), 2)

    return jsonify({
        "average_temperature": average,
        "unit": "°C",
        "status": get_temperature_status(average),
        "boxes_used": len(readings),
        "boxes_total": len(SENSEBOX_IDS)
    })


if __name__ == "__main__":
    print(f"Starting HiveBox v{APP_VERSION}")
    app.run(host="0.0.0.0", port=5000, debug=False)