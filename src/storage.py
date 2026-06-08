"""MinIO (S3-compatible) storage layer."""
import json
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from src.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET
)

_client = None


def get_client():
    """Return MinIO client, create if not exists."""
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"http://{MINIO_ENDPOINT}",
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        )
    return _client


def ensure_bucket():
    """Create bucket if it doesn't exist."""
    try:
        get_client().head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        get_client().create_bucket(Bucket=MINIO_BUCKET)


def store_temperature(data):
    """Store temperature data as JSON file in MinIO."""
    try:
        ensure_bucket()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        key = f"temperature/{timestamp}.json"
        get_client().put_object(
            Bucket=MINIO_BUCKET,
            Key=key,
            Body=json.dumps(data),
            ContentType="application/json"
        )
        return True
    except Exception:  # pylint: disable=broad-except
        return False