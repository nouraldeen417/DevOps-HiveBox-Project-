# HiveBox 🐝 — Phase 4

Phase 4 focuses on Kubernetes deployment, Continuous Integration improvements, Continuous Delivery automation, and security hardening for HiveBox.

<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox/" imageanchor="1">
    <img width="90%" src="https://devopsroadmap.io/assets/images/module-04-overview-b8303bb10b6f537c8c8a00d5aa73f1cc.png" />
  </a><br/>
</p>
<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox/" imageanchor="1">
    <img width="90%" src="https://devopsroadmap.io/assets/images/hivebox-architecture-phase-04-9f5eecf3d87c6915d1f8245602c8f8d5.png" />
  </a><br/>
</p>

This phase introduces:
- Kubernetes deployment with KIND
- Horizontal Pod Autoscaler (HPA)
- Prometheus metrics endpoint
- SonarQube code quality gate
- Terrascan Kubernetes manifest scanning
- Continuous Delivery via GitHub Actions
- Integration testing against real running container
- senseBox IDs configurable via environment variables
- Temperature status field in API response

---

## Project Structure

```text
hivebox/
├── .github/
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       ├── codeql.yml
│       ├── dependency-review.yml
│       └── scorecard.yml
├── K8S/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── src/
│   ├── __init__.py
│   └── app.py
├── tests/
│   ├── __init__.py
│   ├── test_app.py
│   └── integration/
│       ├── __init__.py
│       └── test_integration.py
├── Dockerfile
├── kind-config.yaml
├── sonar-project.properties
├── requirements.txt
├── RADAR.md
├── README.md
└── LICENSE.md
```

---

## Code Changes

### senseBox IDs — Configurable via Environment Variable

Previously the senseBox IDs were hardcoded in `app.py`. They are now read from an environment variable so they can be changed per environment without touching code.

#### Why configurable?

- No code changes needed to swap senseBox devices
- Different environments can use different boxes
- Follows the 12-factor app principle — configuration lives in the environment

#### How it works

```python
SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
).split(",")
```

The fallback value is used when no environment variable is set — useful for local development without any configuration.

#### Set the environment variable locally

```bash
export SENSEBOX_IDS="id1,id2,id3"
python src/app.py
```

#### Set it in Kubernetes

Configured via `K8S/configmap.yaml` — Kubernetes injects it automatically into the pod as an environment variable.

---

### `/metrics` Endpoint 📊

#### Endpoint

```text
/metrics
```

#### Parameters

No parameters required.

#### Requirements

- Returns default Prometheus metrics about the app
- Auto-instruments all Flask routes
- No manual metric definition needed

#### Why Prometheus metrics?

- Industry standard for application monitoring
- Tracks request counts, latency, error rates automatically
- Feeds into Grafana dashboards in Phase 5

#### How it works

```python
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)
```

Two lines of code — the `/metrics` endpoint is created automatically.

#### Example Response

```text
flask_http_request_total{method="GET",status="200"} 5.0
flask_http_request_duration_seconds_count{...} 5.0
```

#### Test the endpoint

```bash
curl http://localhost:5000/metrics
```

---

### `/temperature` Endpoint — Status Field 🌡️

#### Endpoint

```text
/temperature
```

#### Parameters

No parameters required.

#### Requirements

- Fetch data from openSenseMap API
- Return average temperature from all available senseBox sensors
- Ignore sensor data older than 1 hour
- Handle unavailable sensor data safely
- Return a human-readable status based on the average temperature

#### Status logic

| Average temperature | Status |
|---|---|
| Below 10°C | Too Cold |
| Between 10°C and 36°C | Good |
| Above 36°C | Too Hot |

#### Example Response

```json
{
  "average_temperature": 24.6,
  "unit": "°C",
  "status": "Good",
  "boxes_used": 2,
  "boxes_total": 3
}
```

#### Error Response (503)

```json
{
  "error": "No valid temperature data available",
  "detail": "All senseBox readings are older than 1 hour or unavailable"
}
```

---

## Integration Tests

Integration tests hit the real running server — no mocking. Unlike unit tests which fake HTTP calls, integration tests prove the whole app works end to end.

#### Unit tests vs Integration tests

| | Unit tests | Integration tests |
|---|---|---|
| How they work | Mock everything | Hit the real running server |
| Speed | Instant | Slower |
| What they prove | Logic is correct | The whole app works end to end |
| Internet needed | No | Yes |
| Location | `tests/test_app.py` | `tests/integration/test_integration.py` |

#### Run integration tests locally

```bash
# Terminal 1 — start the app
python src/app.py

# Terminal 2 — run integration tests
PYTHONPATH=$(pwd) pytest tests/integration/ -v
```

---

## Development Tools & Used GitHub Actions



### Harden Runner

StepSecurity Harden Runner installs a security agent on the GitHub-hosted runner.

It protects against:
- credential exfiltration during CI runs
- compromised dependencies making unexpected network calls
- supply chain attacks targeting the build environment

#### Why do we use Harden Runner?

- Monitors all outbound network traffic during every CI job
- Blocks unexpected connections that could steal secrets
- Applies zero-trust security to the build pipeline

---

### Pin Actions to Full Length Commit SHA

GitHub Action tags like `@v4` are mutable — they can be updated at any time to point to different code.

#### Why do we pin actions?

- Tags are mutable and can be silently changed by maintainers
- A full SHA is immutable — it points to one exact commit forever
- Recommended by GitHub's own Security Hardening guide

##### How it is applied

```yaml
# Before (mutable — unsafe)
uses: actions/checkout@v4

# After (pinned — safe)
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

---

### Dependabot Configuration

Dependabot automatically opens Pull Requests when your dependencies have outdated versions or known CVEs.

It monitors:
- Python packages in `requirements.txt`
- GitHub Actions in all workflow files
- Docker base images in the Dockerfile

#### How it is applied

A configuration file was added at `.github/dependabot.yml` covering all three ecosystems on a weekly schedule.

---

### CodeQL Workflow (SAST)

CodeQL is GitHub's Static Application Security Testing tool. It scans your source code without running it and finds security vulnerabilities.

It detects:
- hardcoded secrets
- insecure function calls
- injection risks
- unsafe data handling

#### How it is applied

A new workflow was added at `.github/workflows/codeql.yml` that initializes and runs CodeQL analysis on the Python codebase on every push, pull request, and weekly schedule.

---

### Dependency Review Workflow

The Dependency Review workflow runs on every Pull Request and blocks merging if the PR introduces a dependency with a known CVE.

#### How it is applied

A new workflow was added at `.github/workflows/dependency-review.yml` that triggers only on pull requests targeting `main`.

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/moelgenady/DevOps-HiveBox.git
cd DevOps-HiveBox
```

---

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Run the application

```bash
PYTHONPATH=$(pwd) python src/app.py
```

---

### 5. Test the API

```bash
curl http://localhost:5000/version
curl http://localhost:5000/temperature
curl http://localhost:5000/metrics
```

Expected response for `/version`:

```json
{
  "version": "0.0.2"
}
```

---

## Running Tests

Run unit tests:

```bash
PYTHONPATH=$(pwd) pytest tests/test_app.py -v
```

Run integration tests (requires running app):

```bash
PYTHONPATH=$(pwd) pytest tests/integration/ -v
```

Run all tests:

```bash
PYTHONPATH=$(pwd) pytest tests/ -v
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/version` | Returns current app version |
| GET | `/temperature` | Returns average temperature with status |
| GET | `/metrics` | Returns Prometheus metrics |

---

## `/version` Endpoint

### Endpoint

```text
/version
```

### Parameters

No parameters required.

### Response

```json
{
  "version": "0.0.2"
}
```

---

## Docker

### Build Docker image

```bash
docker build -t hivebox:0.0.2 .
```

### Run container

```bash
docker run -p 5000:5000 hivebox:0.0.2
```

### Run container with custom senseBox IDs

```bash
docker run -p 5000:5000 \
  -e SENSEBOX_IDS="id1,id2,id3" \
  hivebox:0.0.2
```

### Test API inside container

```bash
curl http://localhost:5000/version
curl http://localhost:5000/temperature
curl http://localhost:5000/metrics
```

---

## Kubernetes Deployment

### Tools Required

#### Install KIND

KIND (Kubernetes IN Docker) runs a real Kubernetes cluster inside Docker containers on your laptop.

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind --version
```

#### Install kubectl

kubectl is the command-line tool for controlling Kubernetes clusters.

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/kubectl
kubectl version --client
```

---

### Create the KIND Cluster

```bash
kind create cluster --name hivebox --config kind-config.yaml
```

Install Ingress-Nginx into the cluster:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

Wait for Ingress-Nginx to be ready:

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

Verify the cluster:

```bash
kubectl get nodes
kubectl get pods -A
```

---

### Kubernetes Manifests

All manifests live in the `K8S/` folder. Each file has a single responsibility.

#### `namespace.yaml`

Creates an isolated `hivebox` namespace so HiveBox resources are separated from system components.

#### `configmap.yaml`

Stores the senseBox IDs as an environment variable. Kubernetes injects it into the pod automatically. Changing the IDs requires only updating this file — no image rebuild needed.

#### `deployment.yaml`

Tells Kubernetes what to run and how many copies to keep alive. Runs 2 replicas for reliability. If a pod crashes, Kubernetes automatically restarts it. Includes liveness and readiness probes on `/version`.

#### `service.yaml`

Gives pods a stable internal name and IP. Without this, pods are unreachable because their IPs change on every restart.

#### `ingress.yaml`

Routes external HTTP traffic into the cluster via Ingress-Nginx. Without this, the app is only reachable from inside the cluster.

#### `hpa.yaml`

Horizontal Pod Autoscaler — automatically scales pods between 2 and 5 replicas based on CPU usage. Scales up when CPU hits 70%, scales back down when traffic drops.

---

### Deploy to Cluster

```bash
kubectl apply -f K8S/namespace.yaml
kubectl apply -f K8S/configmap.yaml
kubectl apply -f K8S/deployment.yaml
kubectl apply -f K8S/service.yaml
kubectl apply -f K8S/ingress.yaml
kubectl apply -f K8S/hpa.yaml
```

Or apply all at once:

```bash
kubectl apply -f K8S/
```

Verify everything is running:

```bash
kubectl get all -n hivebox
kubectl get hpa -n hivebox
kubectl get ingress -n hivebox
```

Test the app from your laptop:

```bash
curl http://localhost/version
curl http://localhost/temperature
curl http://localhost/metrics
```

---

### Update KIND Cluster After CD

Once CD pushes a new image to `ghcr.io`, update your local KIND cluster manually:

#### Tip!
In the next phase we will use Ansible to do that automatically, Well all works will be automatically once code is pushed to main branch


```bash
# Pull the new image
docker pull ghcr.io/moelgenady/devops-hivebox:latest

# Load image into KIND cluster
kind load docker-image ghcr.io/moelgenady/devops-hivebox:latest --name hivebox

# Restart the deployment with the new image
kubectl rollout restart deployment/hivebox -n hivebox

# Watch pods restart
kubectl rollout status deployment/hivebox -n hivebox
```

---
### To use HTTPS with Ingress-Nginx in KIND 
Generate a certificate locally, store it as a Kubernetes Secret, reference it in the Ingress. Works for KIND but browser will show a warning.

#### Step 1: Generate a Self-Signed Certificate
Generate a TLS certificate and private key valid for 365 days:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key \
  -out tls.crt \
  -subj "/CN=hivebox.local/O=hivebox"
```

##### This command creates:
###### tls.key
Private key used for TLS encryption
###### tls.crt
Public certificate presented to clients

####### The certificate is issued for the hostname hivebox.local.

#### Step 2: Create a Kubernetes TLS Secret
Create a TLS Secret from the generated certificate and key:

```bash
kubectl create secret tls hivebox-tls --cert=tls.crt --key=tls.key -n hivebox
```
##### This creates a Kubernetes Secret named hivebox-tls in the hivebox namespace.

#### Step 3: Configure the Ingress
Ensure the Ingress resource references the TLS Secret:
```yaml
tls: 
        - hosts: 
                - hivebox.local 
        secretName: hivebox-tls
```
#### Step 4: Add Hostname Mapping
Add the following entry to your local machine's /etc/hosts file:

```bash
echo "127.0.0.1 hivebox.local" | sudo tee -a /etc/hosts
```
##### This maps the hostname hivebox.local to your local Kubernetes environment so that browsers and command-line tools can resolve the hostname correctly.

#### Teste HTTPS

```bash
# -k flag skips certificate verification for self-signed certs
curl -k https://hivebox.local/version
curl -k https://hivebox.local/temperature
curl -k https://hivebox.local/metrics
```

--
### RADAR — Kubernetes Visual Dashboard

RADAR gives you a live visual UI of everything running in your KIND cluster. See `RADAR.md` for full installation and usage guide.

```bash
kubectl radar
```

Opens at `http://localhost:9280`.

#### Check RADAR README 
---

## Continuous Integration (CI)

CI runs automatically on every Pull Request targeting `main`.

### CI Flow

```
lint the code and Dockerfile
  ↓
test
  ↓
build + sonarqube  (parallel) + integration tests
  ↓
terrascan
```

### CI Pipeline Includes

- Python linting using Pylint
- Dockerfile linting using Hadolint
- Unit tests with pytest
- Docker image build with layer caching
- Image vulnerability scanning using Trivy
- Integration tests against real running container
- Smoke tests for all endpoints
- SonarQube code quality and security analysis
- SonarQube quality gate enforcement
- Terrascan Kubernetes manifest scanning
- Concurrency control — cancels outdated runs on rapid pushes

### Concurrency Control

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

If you push multiple commits quickly, only the latest run matters. Previous runs are cancelled automatically — saves runner minutes.

### Docker Layer Caching

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

Unchanged Docker layers are restored from cache instead of rebuilt. Saves 1-3 minutes on every build after the first.

### Integration Tests in CI

After the container starts, `tests/integration/test_integration.py` runs against it using real HTTP calls — no mocking. This proves the whole app works end to end inside Docker before the image is ever pushed.

---

## SonarQube Code Quality Gate 🔍

SonarQube reads your Python source code and reports on code quality, security vulnerabilities, bugs, and test coverage.

### Why do we use SonarQube?

- Catches security vulnerabilities before they reach production
- Enforces code quality as a hard gate on every PR
- Tracks code quality trends over time
- Results appear on `sonarcloud.io` and as PR comments

### How it works

```
SonarQube scan step
  uploads code to SonarCloud → runs full analysis
        ↓
SonarQube quality gate check step
  waits for analysis to finish → fails CI if gate fails
```

Two steps are required — the scan alone does not enforce the gate.

### Configuration

SonarQube is configured via `sonar-project.properties` at the repo root:

```properties
sonar.projectKey=moelgenady_DevOps-HiveBox
sonar.organization=moelgenady
sonar.sources=src
sonar.tests=tests
sonar.python.version=3.12
```

### View results

Go to `https://sonarcloud.io` → your project → full quality report.

---

## Terrascan Kubernetes Manifest Scanning 🔐

Terrascan scans Kubernetes manifest files for security misconfigurations before they reach the cluster.

### Why do we use Terrascan?

- Catches containers running as root
- Detects missing resource limits
- Finds missing readiness and liveness probes
- Identifies privileged containers

### Why CLI not the GitHub Action?

The `tenable/terrascan-action` was archive

#### Note that: We used GitHub Actions instead of using CLI ,But it`s Recommended to use CLI.

---

## Continuous Delivery (CD) 🚀

CD runs automatically after CI passes on `main`. It builds the Docker image and pushes it to GitHub Container Registry.

### Why separate CI and CD?

- CI proves the code works — never pushes images
- CD delivers the proven code — builds and pushes image
- Clear separation of concerns
- CD never runs if CI failed

### How CD connects to CI

```yaml
on:
  workflow_run:
    workflows: [Continuous Integration]
    types: [completed]
    branches: [main]
```

CD wakes up when CI finishes. The job condition checks the result:

```yaml
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

If CI failed — CD job is skipped entirely. Nothing is pushed.

### The 3 image tags

Every CD run pushes 3 tags to `ghcr.io`:

| Tag | Purpose |
|---|---|
| `:latest` | Always points to the newest build |
| `:0.0.2` | Version tag matching `APP_VERSION` in `app.py` |
| `:sha-abc1234` | Exact git commit SHA for rollback |

The SHA tag means if `latest` breaks in production you know exactly which commit was the last good build and can roll back instantly.

### GITHUB_TOKEN

CD authenticates with `ghcr.io` using `GITHUB_TOKEN` — automatically provided by GitHub to every workflow. No secrets to configure. The `packages: write` permission in the job allows it to push images.

### Pull image from registry

```bash
docker pull ghcr.io/moelgenady/devops-hivebox:latest
```

## Contributing Workflow

1. Pick an issue from the project board

2. Create a feature branch from `development`

```bash
git checkout -b feature/your-feature-name
```

3. Commit using Conventional Commits

4. Push to `development` branch

5. Open Pull Request targeting `main`

6. CI runs automatically — all checks must pass

7. Reference issue using:

```text
closes #issue-number
```

---