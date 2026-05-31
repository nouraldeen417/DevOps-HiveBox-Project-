# HiveBox 🐝

A scalable RESTful API for beekeepers, built around [openSenseMap](https://opensensemap.org/). Fetches real sensor data from physical senseBox devices and returns clean JSON.

![CI](https://github.com/nouraldeen417/DevOps-HiveBox-Project-/actions/workflows/ci.yaml/badge.svg)

---

## Project Structure

```
hivebox/
├── .github/
│   └── workflows/
│       ├── ci.yml          ← CI pipeline
│       └── scorecard.yml   ← OpenSSF security scan
├── src/
│   ├── __init__.py
│   └── app.py              ← Flask application
├── tests/
│   ├── __init__.py
│   └── test_app.py         ← pytest tests
├── conftest.py             ← pytest path config
├── .dockerignore
├── .flake8                 ← linting config
├── .trivyignore            ← ignored CVEs with reasons
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Local Development

### 1. Clone the repo

```bash
git clone https://github.com/your-username/hivebox.git
cd hivebox
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python src/app.py
```

### 5. Test endpoints

```bash
curl http://localhost:5000/version
# {"version": "0.0.1"}

curl http://localhost:5000/temperature
# {"temperature": 18.5, "unit": "celsius", "boxes_used": 3}
```

---

## Running Tests

```bash
pytest tests/
```

Run a single test:

```bash
pytest tests/test_app.py::test_version
pytest tests/test_app.py::test_temperature
```

---

## Docker

```bash
# Build
docker build -t hivebox .

# Run
docker run -p 5000:5000 hivebox

# Test
curl http://localhost:5000/temperature
```

---

## API Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/version` | Current app version | `{"version": "0.0.1"}` |
| GET | `/temperature` | Average temp from 3 senseBoxes (max 1hr old) | `{"temperature": 18.5, "unit": "celsius", "boxes_used": 3}` |

> Returns `503` if no fresh temperature data is available from any senseBox.

---

## CI Pipeline

Runs automatically on every push to any branch.

```
lint (flake8 + hadolint)
      ↓
test (pytest)
      ↓
build → scan (trivy) → smoke test
```

| Job | What it does |
|-----|-------------|
| lint | Checks Python code (flake8) and Dockerfile (hadolint) |
| test | Runs all pytest unit tests |
| build | Builds Docker image, scans for CVEs, runs smoke test on /version |

---

## Security

- **Trivy** scans the Docker image for CRITICAL and HIGH CVEs on every build
- **Non-root user** — container runs as `appuser` not root
- **OpenSSF Scorecard** — runs weekly and on every push to main
- **CVEs with no available fix** are documented in `.trivyignore` with reasons

---

## Contributing Workflow

1. Pick an issue from the [project board](../../projects)
2. Create a branch: `git checkout -b feature/your-issue-name`
3. Make your changes
4. Push and open a PR — write `closes #N` in the description
5. CI runs automatically — all checks must pass before merge

> Direct pushes to `main` are blocked. All changes must go through a PR.

---

## Phases

| Phase | Focus |
|-------|-------|
| **1** | Foundation — Flask app, /version, Docker |
| **2** | /temperature endpoint, CI pipeline, security scanning |
| **3** | Caching, /health, /metrics |
| **4+** | Kubernetes, Terraform, monitoring |

---

