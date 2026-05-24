from flask import Flask, jsonify
import requests
from datetime import datetime, timezone, timedelta
app = Flask(__name__)
SENSEBOXES = [
    "5eba5fbad46fb8001b799786",
    "5c21ff8f919bf8001adf2488",
    "5ade1acf223bd80019a1011c"
]


def get_temperature(box_id):
    url = f"https://api.opensensemap.org/boxes/{box_id}"
    response = requests.get(url)
    data = response.json()
    for sensor in data["sensors"]:
        if "temperatur" in sensor["title"].lower():
            measurement = sensor["lastMeasurement"]
            # check timestamp
            measured_at = datetime.fromisoformat(
                measurement["createdAt"].replace("Z", "+00:00")
            )
            age = datetime.now(timezone.utc) - measured_at
            # skip if older than 1 hour
            if age > timedelta(hours=1):
                return None
            return float(measurement["value"])
    return None


@app.route("/version")
def version():
    return jsonify({"version": "0.0.1"})


@app.route("/temperature")
def temperature():
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
        "boxes_used": len(readings)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
