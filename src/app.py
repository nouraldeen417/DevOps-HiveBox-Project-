"""HiveBox Flask application."""
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from apscheduler.schedulers.background import BackgroundScheduler
from src.metrics import (temperature_gauge, temperature_status_gauge,boxes_total_gauge,
                         boxes_used_gauge ,readyz_status_gauge, cache_age_gauge, cache_fresh_gauge ,
                         store_operations_total, store_errors_total )
from src.config import APP_VERSION, SENSEBOX_IDS
from src.temperature import get_temperature_from_box, get_temperature_status
from src.cache import get_cached_temperature, set_cached_temperature, is_cache_fresh, get_cache_age
from src.storage import store_temperature

app = Flask(__name__)
metrics = PrometheusMetrics(app)


def fetch_and_cache_temperature():
    """Fetch temperature from all boxes and cache the result."""
    readings = [
        temp
        for box_id in SENSEBOX_IDS
        if (temp := get_temperature_from_box(box_id)) is not None
    ]
    if not readings:
        return None
    average = round(sum(readings) / len(readings), 2)
    data = {
        "average_temperature": average,
        "unit": "°C",
        "status": get_temperature_status(average),
        "boxes_used": len(readings),
        "boxes_total": len(SENSEBOX_IDS)
    }
    set_cached_temperature(data)
    return data


# scheduler runs store_temperature every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: store_temperature(fetch_and_cache_temperature()),
    "interval",
    minutes=5
)
scheduler.start()


@app.route("/version")
def get_version():
    """Return current app version."""
    return jsonify({"version": APP_VERSION})


@app.route("/temperature")
def get_temperature():
    """Return average temperature from all senseBoxes."""
    cached = get_cached_temperature()
    if cached:
        # Still update metrics from cached data
        temperature_gauge.set(cached['average_temperature'])
        boxes_total_gauge.set(cached['boxes_total'])
        boxes_used_gauge.set(cached['boxes_used'])
        temperature_status_gauge.set(
            {'Too Cold': 0, 'Good': 1, 'Too Hot': 2}[cached['status']]
        )
        return jsonify(cached)

    data = fetch_and_cache_temperature()
    if not data:
        return jsonify({
            "error": "No valid temperature data available",
            "detail": "All senseBox readings are older than 1 hour or unavailable"
        }), 503

    temperature_gauge.set(data['average_temperature'])
    boxes_total_gauge.set(data['boxes_total'])
    boxes_used_gauge.set(data['boxes_used'])
    temperature_status_gauge.set(
        {'Too Cold': 0, 'Good': 1, 'Too Hot': 2}[data['status']]
    )
    return jsonify(data)


@app.route("/store")
def store():
    """Manually trigger storing current temperature to MinIO."""
    data = fetch_and_cache_temperature()
    if not data:
        store_errors_total.inc()
        return jsonify({"error": "No data to store"}), 503

    success = store_temperature(data)
    if not success:
        store_errors_total.inc()
        return jsonify({"error": "Failed to store data"}), 503

    store_operations_total.labels(trigger='manual').inc()
    return jsonify({"status": "stored", "data": data})


@app.route("/readyz")
def readyz():
    """
    Readiness check.
    Returns 503 if 50%+1 boxes are down AND cache is older than 5 minutes.
    """
    unreachable = sum(
        1 for box_id in SENSEBOX_IDS
        if get_temperature_from_box(box_id) is None
    )
    threshold = (len(SENSEBOX_IDS) // 2) + 1
    fresh = is_cache_fresh()

    # Always update these on every readyz call
    cache_age_gauge.set(get_cache_age() or 0)
    cache_fresh_gauge.set(1 if fresh else 0)
    boxes_used_gauge.set(len(SENSEBOX_IDS) - unreachable)

    if unreachable >= threshold and not fresh:
        readyz_status_gauge.set(0)
        return jsonify({
            "status": "not ready",
            "unreachable_boxes": unreachable,
            "cache_fresh": False
        }), 503

    readyz_status_gauge.set(1)
    return jsonify({
        "status": "ready",
        "unreachable_boxes": unreachable,
        "cache_fresh": fresh
    })

if __name__ == "__main__":
    print(f"Starting HiveBox v{APP_VERSION}")
    app.run(host="0.0.0.0", port=5000, debug=False)
