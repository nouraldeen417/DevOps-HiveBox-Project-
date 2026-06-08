"""Temperature fetching and status logic."""
from datetime import datetime, timezone, timedelta

import requests

from src.config import OPENSENSEMAP_API, MAX_DATA_AGE_HOURS


def get_temperature_from_box(box_id):
    """
    Fetch temperature from a single senseBox.
    Returns float or None if unavailable/stale.
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
    """Return human-readable status based on average temperature."""
    if average < 10:
        return "Too Cold"
    if average <= 36:
        return "Good"
    return "Too Hot"