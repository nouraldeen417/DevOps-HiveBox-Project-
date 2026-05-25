from datetime import datetime, timezone, timedelta
import requests
from flask import Flask, jsonify

APP_VERSION = "0.0.1"

app = Flask(__name__)

# These are the 3 senseBox IDs from Phase 1.
# Stored here as a list so adding more boxes later is just one line.
SENSEBOX_IDS = [
    "5eba5fbad46fb8001b799786",
    "5c21ff8f919bf8001adf2488",
    "5ade1acf223bd80019a1011c",
]

OPENSENSEMAP_API = "https://api.opensensemap.org/boxes"

# Data must not be older than this — Phase 3 requirement
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
            timeout=5  # never wait forever — 5 seconds max
        )
        response.raise_for_status()  # raises error if status is 4xx or 5xx
        data = response.json()

        # Loop through sensors to find the temperature one
        for sensor in data.get("sensors", []):
            if "temp" in sensor.get("title", "").lower():
                measurement = sensor.get("lastMeasurement")

                if not measurement:
                    return None

                # Parse the timestamp and check freshness
                created_at = datetime.fromisoformat(
                    measurement["createdAt"].replace("Z", "+00:00")
                )
                age = datetime.now(timezone.utc) - created_at

                # Reject data older than 1 hour — Phase 3 requirement
                if age > timedelta(hours=MAX_DATA_AGE_HOURS):
                    return None

                return float(measurement["value"])

    except (requests.RequestException, ValueError, KeyError):
        # If anything goes wrong with one box, skip it — don't crash the whole API
        return None
    except Exception:  
     return None
    return None


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
    readings = []

    for box_id in SENSEBOX_IDS:
        temp = get_temperature_from_box(box_id)
        if temp is not None:
            readings.append(temp)

    # If no valid readings found, return a clear error
    if not readings:
        return jsonify({
            "error": "No valid temperature data available",
            "detail": "All senseBox readings are older than 1 hour or unavailable"
        }), 503

    average = round(sum(readings) / len(readings), 2)

    return jsonify({
        "average_temperature": average,
        "unit": "°C",
        "boxes_used": len(readings),
        "boxes_total": len(SENSEBOX_IDS)
    })


if __name__ == "__main__":
    print(f"Starting HiveBox v{APP_VERSION}")
    app.run(host="0.0.0.0", port=5000, debug=False)