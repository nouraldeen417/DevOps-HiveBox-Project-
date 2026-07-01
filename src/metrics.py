"""Custom Prometheus metrics for HiveBox."""
from prometheus_client import Gauge, Counter

# Temperature
temperature_gauge = Gauge(
    'hivebox_temperature_celsius',
    'Current average temperature from senseBoxes'
)

temperature_status_gauge = Gauge(
    'hivebox_temperature_status',
    'Temperature status: 0=Too Cold, 1=Good, 2=Too Hot'
)

# senseBox availability
boxes_total_gauge = Gauge(
    'hivebox_boxes_total',
    'Total number of configured senseBoxes'
)

boxes_used_gauge = Gauge(
    'hivebox_boxes_used',
    'Number of senseBoxes returning valid data'
)

# Cache
cache_age_gauge = Gauge(
    'hivebox_cache_age_seconds',
    'Age of cached temperature data in seconds'
)

cache_fresh_gauge = Gauge(
    'hivebox_cache_fresh',
    'Whether cache is fresh: 1=fresh, 0=stale'
)

# Store operations
store_operations_total = Counter(
    'hivebox_store_operations_total',
    'Total number of MinIO store operations',
    ['trigger']  # 'manual' or 'scheduled'
)

store_errors_total = Counter(
    'hivebox_store_errors_total',
    'Total number of failed MinIO store operations'
)

# Readyz
readyz_status_gauge = Gauge(
    'hivebox_ready',
    'Whether app is ready: 1=ready, 0=not ready'
)
