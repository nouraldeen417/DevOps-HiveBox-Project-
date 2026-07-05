# Containers

Covers the app's `Dockerfile` and the `docker-compose.yml` used for
early functional verification in CI.

## Dockerfile — Multi-Stage Build

Two stages, `builder` and final, both on `python:3.12-slim`.

**Stage 1 — `builder`:**
- Copies only `requirements.txt` first (so dependency install is cached
  independently of source code changes).
- Installs dependencies into a custom prefix (`--prefix=/install`) instead of
  the default system location, so only the installed packages — not pip's
  cache or build tooling — get carried into the final image.

**Stage 2 — final:**
- Starts fresh from `python:3.12-slim` (none of the builder stage's layers,
  pip cache, or `requirements.txt` itself are carried over).
- `PYTHONDONTWRITEBYTECODE=1` / `PYTHONUNBUFFERED=1` — skips `.pyc` files and
  makes logs stream immediately instead of buffering (matters for container
  log visibility).
- Creates a dedicated non-root system user/group (`appuser`/`appgroup`) —
  the app never runs as root.
- Copies installed packages from `/install` (builder) to `/usr/local` (where
  Python expects them at runtime), then copies `src/` — nothing else from
  the repo (no tests, no docs, no CI config) ends up in the image.
- Switches to `appuser` before `CMD`.
- Exposes `5000`, runs via `python -m src.app`.

**Why multi-stage matters here:** the final image only contains the Python
runtime, installed dependencies, and application code — no compilers, no
build cache, no source files unrelated to running the app. Smaller image,
smaller attack surface, and a non-root runtime user.

## `docker-compose.test.yml` — Early Functional Check in CI

**Purpose:** this is *not* a local dev convenience file — it's used inside
the CI pipeline to catch broken functionality early, before the heavier KIND
+ Venom end-to-end suite runs. Fast to spin up, runs against a real Valkey +
MinIO, and confirms the app's actual runtime behavior (caching, storage,
readiness) works before committing to a full cluster-based test run.

**Services:**

| Service | Role |
|---|---|
| `app` | The built image (`ghcr.io/nouraldeen417/devops-hivebox:test`), configured via env vars to point at the other services in this compose network |
| `valkey` | `valkey/valkey:8-alpine`, with a `valkey-cli ping` healthcheck |
| `minio` | `minio/minio:latest`, with a healthcheck against `/minio/health/live` |
| `minio-init` | One-shot `minio/mc` container that creates the `hivebox` bucket before the app starts, so `/store` works on the very first call instead of failing on a missing bucket |

**Startup ordering:** `app` waits on `valkey: service_healthy`,
`minio: service_healthy`, **and** `minio-init: service_completed_successfully`
— so the app never starts against a cache/storage backend that isn't
actually ready yet, and never races the bucket-creation step.

**On the hardcoded credentials:** `minioadmin`/`minioadmin` and the test
`APP_VERSION: test` are hardcoded intentionally. This file only stands up an
isolated, ephemeral test environment for CI functional checks — it's not
used for anything resembling a real deployment, so hardcoding here trades
zero security for simplicity and speed, on purpose.

### Running it locally
```bash
docker compose -f docker-compose.yml up --build
curl http://localhost:5000/version
curl http://localhost:5000/store
docker compose -f docker-compose.yml down -v
```