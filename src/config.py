"""HiveBox configuration — all env vars and constants in one place."""
import os

APP_VERSION = "0.0.2"

SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
).split(",")

OPENSENSEMAP_API = "https://api.opensensemap.org/boxes"
MAX_DATA_AGE_HOURS = 1
CACHE_TTL_SECONDS = 300  # 5 minutes

VALKEY_HOST = os.environ.get("VALKEY_HOST", "localhost")
VALKEY_PORT = int(os.environ.get("VALKEY_PORT", "6379"))

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "hivebox")