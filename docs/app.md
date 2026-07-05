# HiveBox App

Flask-based REST API that aggregates temperature data from openSenseMap
senseBoxes, caches it in Valkey, and periodically archives it to MinIO.

## Endpoints

### `GET /version`
Returns the deployed app version. This is **not hardcoded** — it reflects
whatever `APP_VERSION` is set to at deploy time (see
[Configuration](#configuration-srcconfigpy)), so the value below is just the
current default and will change release to release (e.g. via the CD
pipeline's image tagging).
```json
{ "version": "0.0.2" }
```

### `GET /temperature`
Returns average temperature across all configured senseBoxes.

- Checks the Valkey cache first. If a cached value exists, it's returned
  directly (and used to update Prometheus gauges).
- If no cache, fetches live from each senseBox, averages the valid readings,
  caches the result, and returns it.
- If **no** senseBox returns valid data (all unreachable or all readings
  older than 1 hour), responds `503`:
  ```json
  { "error": "No valid temperature data available",
    "detail": "All senseBox readings are older than 1 hour or unavailable" }
  ```
- Success response:
  ```json
  { "average_temperature": 23.5, "unit": "°C", "status": "Good",
    "boxes_used": 3, "boxes_total": 3 }
  ```
- Status thresholds (`get_temperature_status`):
  | Range | Status |
  |---|---|
  | `< 10` | Too Cold |
  | `10 – 36` | Good |
  | `> 36` | Too Hot |

### `GET /store`
Manually triggers a fresh fetch + store to MinIO (bypasses cache — always
hits openSenseMap live, unlike `/temperature`).
- No data available → `503`, increments `hivebox_store_errors_total`.
- MinIO write fails → `503`, increments `hivebox_store_errors_total`.
- Success → `{"status": "stored", "data": {...}}`, increments
  `hivebox_store_operations_total{trigger="manual"}`.

A background scheduler also calls the same fetch-and-store logic every
**5 minutes** automatically (`trigger="scheduled"`... — see note below).

> **Note:** the scheduled job currently doesn't pass a `trigger` label
> explicitly when calling `store_temperature`, so scheduled vs. manual store
> operations should be double-checked against the actual Counter call if the
> label ever needs to be relied on for dashboards.

### `GET /readyz`
Readiness probe. **This does make a live call to openSenseMap** for each
configured senseBox (to count how many are currently unreachable) — it does
not rely purely on cache. What it avoids is *failing readiness just because
the live API is down*:

- Counts `unreachable` boxes via live check.
- Fails (`503`) only if **both**:
  - `unreachable >= (total_boxes // 2) + 1`, **and**
  - the Valkey cache is stale (`is_cache_fresh()` returns `False`)
- If the cache is still fresh, the pod stays Ready even if openSenseMap is
  fully down.
- Also updates `hivebox_cache_age_seconds`, `hivebox_cache_fresh`, and
  `hivebox_boxes_used` on every call (note: `boxes_used` here reflects a
  **live** check, whereas `/temperature`'s `boxes_used` may reflect a
  **cached** value — the two can disagree momentarily).

### `GET /metrics`
Not an explicit route — auto-registered by `prometheus_flask_exporter`
(`PrometheusMetrics(app)`), which also adds Flask's default HTTP metrics
(request counts, latencies, etc.) alongside the custom metrics below.

## Custom Prometheus Metrics (`src/metrics.py`)

| Metric | Type | Meaning |
|---|---|---|
| `hivebox_temperature_celsius` | Gauge | Current average temperature |
| `hivebox_temperature_status` | Gauge | 0=Too Cold, 1=Good, 2=Too Hot |
| `hivebox_boxes_total` | Gauge | Configured senseBox count |
| `hivebox_boxes_used` | Gauge | Boxes currently returning valid data |
| `hivebox_cache_age_seconds` | Gauge | Age of cached temperature data |
| `hivebox_cache_fresh` | Gauge | 1=fresh, 0=stale |
| `hivebox_store_operations_total` | Counter (`trigger` label) | Successful MinIO writes |
| `hivebox_store_errors_total` | Counter | Failed MinIO writes |
| `hivebox_ready` | Gauge | 1=ready, 0=not ready |

## Configuration (`src/config.py`)

All configuration is via environment variables, with sane local defaults:

| Env var | Default | Purpose |
|---|---|---|
| `SENSEBOX_IDS` | 3 hardcoded IDs (comma-separated) | Which senseBoxes to poll |
| `APP_VERSION` | `0.0.2` | Reported by `/version` |
| `VALKEY_HOST` | `localhost` | Valkey connection |
| `VALKEY_PORT` | `6379` | Valkey connection |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO connection |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO credentials |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO credentials |
| `MINIO_BUCKET` | `hivebox` | Bucket for stored readings |

Fixed constants (not configurable via env): `MAX_DATA_AGE_HOURS = 1`
(a senseBox reading older than this is treated as unavailable),
`CACHE_TTL_SECONDS = 300` (5 minutes).

## Caching Layer (`src/cache.py`)

Backed by Valkey via `redis-py`, lazily-initialized singleton client.

- `set_cached_temperature(data)` — stores under key `"temperature"` with a
  5-minute TTL (`SETEX`).
- `get_cached_temperature()` — returns the parsed value, or `None` if
  missing/expired/on any error (fails silently, doesn't raise).
- `get_cache_age()` — derived from Valkey's `TTL` command:
  - `TTL == -2` (key doesn't exist) → returns `None`
  - `TTL == -1` (key exists, no expiry set) → returns `0` (treated as fresh)
  - otherwise → `CACHE_TTL_SECONDS - ttl`
  - Valkey unreachable → returns `None`
- `is_cache_fresh()` — **returns `True` if the cache key doesn't exist yet**
  (age is `None`), on the reasoning that "never cached" isn't the same
  failure state as "cached, but gone stale." Only an existing-but-expired
  cache counts as `False`. This matters for `/readyz` on a cold start.

## Storage Layer (`src/storage.py`)

Backed by MinIO via `boto3`'s S3 client, lazily-initialized singleton.

- `ensure_bucket()` — checks bucket existence (`head_bucket`), creates it if
  missing.
- `store_temperature(data)` — writes `temperature/{UTC timestamp}.json` to
  the bucket. Returns `True`/`False`; swallows all exceptions (no error
  detail is propagated beyond `False`).

## Temperature Fetch Logic (`src/temperature.py`)

- `get_temperature_from_box(box_id)` — calls
  `https://api.opensensemap.org/boxes/{box_id}` (30s timeout), finds the
  sensor whose title contains `"temp"` (case-insensitive), and returns its
  `lastMeasurement` value **only if** that measurement is younger than
  `MAX_DATA_AGE_HOURS` (1 hour). Returns `None` on any failure: HTTP error,
  missing sensor, missing measurement, or stale data.
- `get_temperature_status(average)` — see thresholds table above.

## Running Locally

```bash
# 1. Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run the app (must run from repo root — imports are absolute, e.g. `from src.config import ...`)
python -m src.app
# App starts on http://0.0.0.0:5000

# 3. Verify it's up
curl http://localhost:5000/version
# {"version": "0.0.2"}

curl http://localhost:5000/temperature
curl http://localhost:5000/metrics

# 4. Run unit tests
pytest
```

**Note on dependencies:** the app doesn't hard-fail without Valkey/MinIO
running — `/version` works regardless, and `/temperature` still works by
falling back to a live openSenseMap fetch if the cache is unreachable (see
[Caching Layer](#caching-layer-srccachepy)). `/store` will fail (`503`)
without a reachable MinIO. For full-stack local testing (app + Valkey +
MinIO together), use `docker-compose.test.yml`, which also handles bucket
pre-creation and readiness retries.



## Unit Tests

Tests mock `src.temperature.requests.get` (via `unittest.mock.patch`) rather
than hitting the real openSenseMap API, using a `make_mock_response()` helper
that builds a fake senseBox payload with a configurable temperature value and
data age.

Run with:
```bash
pytest
```

**Covered:**
| Area | What's tested |
|---|---|
| `/version` | Returns `200`; JSON matches `APP_VERSION`; confirms current default is `"0.0.2"` |
| `/temperature` | `200` + correct response shape on valid fresh data; `503` when all readings are older than 1 hour (`minutes_old=90`); `503` when the openSenseMap call raises an exception |
| `get_temperature_status()` | All three bands (`Too Cold`/`Good`/`Too Hot`) plus explicit boundary checks confirming `10` and `36` are both `"Good"` (inclusive on both edges) |
| `/metrics` | Returns `200` and contains Flask's default `flask_http` metrics |

**Not yet covered by these unit tests** (worth knowing so it's not assumed
tested): `/store`, `/readyz`, the Valkey caching layer (`src/cache.py`), the
MinIO storage layer (`src/storage.py`), and the background scheduler. These
likely need mocking Valkey/MinIO clients directly, or are exercised only at
the integration/e2e level (KIND + Venom) rather than in unit tests — worth
confirming which, so there isn't a false sense of coverage.