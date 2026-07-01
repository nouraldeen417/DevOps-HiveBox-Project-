# HiveBox 🐝 — Phase 3

Phase 3 focuses on improving code quality, container best practices, automated testing, and Continuous Integration (CI) for HiveBox.

<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox/" imageanchor="1">
    <img width="90%" src="https://devopsroadmap.io/assets/images/module-03-overview-3269b01a0471696a3a1e5a86b4c03a4f.png" />
  </a><br/>
</p>
<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox/" imageanchor="1">
    <img width="90%" src="https://devopsroadmap.io/assets/images/hivebox-architecture-phase-03-f62020476900f5db5a97f27e43e9ab8b.png" />
  </a><br/>
</p>

This phase introduces:
- Dockerfile linting with Hadolint
- Python code analysis with Pylint
- CI automation using GitHub Actions
- OpenSSF Scorecard security checks
- New `/temperature` API endpoint
- Unit testing for all endpoints

---

## Project Structure

```text
hivebox/
├── .github/
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml
│       ├── codeql.yml
│       ├── dependency-review.yml
│       └── scorecard.yml
├── src/
│   ├── __init__.py
│   └── app.py
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── Dockerfile
├── requirements.txt
├── README.md
└── LICENSE.md
```

---

## Development Tools & Workflows Objective

### 🐳 Hadolint

Hadolint is a Dockerfile linter used to detect:
- bad Docker practices
- security issues
- inefficient image layers
- syntax problems

### Why do we use Hadolint?

- Improves Docker image quality
- Encourages container best practices
- Helps create production-ready containers

### Run Hadolint Locally

#### Install Hadolint

```bash
wget -O /usr/local/bin/hadolint \
https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64

chmod +x /usr/local/bin/hadolint
```

#### Run Hadolint on Dockerfile

```bash
hadolint Dockerfile
```

### VS Code Extension

Install the Hadolint VS Code extension for real-time Dockerfile analysis.

---

### 🐍 Pylint

Pylint is a Python static code analyzer used to:
- enforce clean code standards
- detect bugs and bad practices
- improve readability and maintainability

### Why do we use Pylint?

- Detects Python issues early
- Encourages PEP8 compliance
- Maintains consistent code quality

### Run Pylint Locally

#### Install Pylint

```bash
pip install pylint
```

#### Verify installation

```bash
pylint --version
```

#### Run Pylint on source code

```bash
pylint src/
```

### VS Code Extension

Install the Pylint VS Code extension for inline linting and suggestions.

---

### 🛡️ OpenSSF Scorecard

OpenSSF Scorecard is a GitHub security analysis tool that checks repository security practices.

It analyzes:
- GitHub Actions security
- branch protection
- token permissions
- dependency pinning
- workflow safety

### Why do we use OpenSSF Scorecard?

- Improves repository security
- Detects insecure CI/CD configurations
- Applies DevSecOps best practices

---

### 🔒 OpenSSF Scorecard Recommendations

The following security improvements were applied based on recommendations from OpenSSF Scorecard via [StepSecurity](https://app.stepsecurity.io).

---

### Harden Runner

StepSecurity Harden Runner is a GitHub Action that installs a security agent on the GitHub-hosted runner.

It protects against:
- credential exfiltration during CI runs
- compromised dependencies making unexpected network calls
- supply chain attacks targeting the build environment

#### Why do we use Harden Runner?

- Monitors all outbound network traffic during every CI job
- Blocks unexpected connections that could steal secrets
- Applies zero-trust security to the build pipeline

#### How it is applied

Added as the first step in every job across all workflow files:

```yaml
- name: Harden runner
  uses: step-security/harden-runner@<pinned-sha>
  with:
    egress-policy: audit
```

---

### Pin Actions to Full Length Commit SHA

GitHub Action tags like `@v4` and Docker tags are mutable — they can be updated at any time to point to different code.

Pinning to a full SHA guarantees:
- the exact code that ran last time runs again
- a compromised tag cannot inject malicious code into your pipeline
- builds are fully reproducible

##### Why do we pin actions?

- Tags are mutable and can be silently changed by maintainers
- A full SHA is immutable — it points to one exact commit forever
- Recommended by GitHub's own Security Hardening guide

##### How it is applied

Every `uses:` line in all workflow files was updated from a tag to a full SHA:

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

#### Why do we use Dependabot?

- Keeps dependencies up to date automatically
- Alerts you when a package you use gets a security fix
- Reduces the risk of running known vulnerable dependencies

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

#### Why do we use CodeQL?

- Catches vulnerabilities before they reach production
- Runs automatically on every push and pull request
- Also runs on a weekly schedule to catch new CVEs in unchanged code
- Results appear under Repository → Security → Code scanning alerts

#### How it is applied

A new workflow was added at `.github/workflows/codeql.yml` that initializes and runs CodeQL analysis on the Python codebase.

---

### Dependency Review Workflow

The Dependency Review workflow runs on every Pull Request and blocks merging if the PR introduces a dependency with a known CVE.

It protects against:
- adding a vulnerable package version in a feature branch
- accidental downgrades to insecure versions
- supply chain attacks via compromised dependencies

#### Why do we use Dependency Review?

- Acts as a security gate on every PR before it reaches `main`
- Posts a clear summary comment on the PR showing exactly what was scanned
- Blocks merging automatically if any dependency has a medium or higher CVE

#### How it is applied

A new workflow was added at `.github/workflows/dependency-review.yml` that triggers only on pull requests targeting `main`.

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/your-username/hivebox.git
cd hivebox
```

---

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Run the application

```bash
python src/app.py
```

---

### 5. Test the API

```bash
curl http://localhost:5000/version
```

Expected response:

```json
{
  "version": "0.0.1"
}
```

---

## Running Tests

Run unit tests using pytest:

```bash
pytest tests/
```

---

## API Endpoints

| Method | Endpoint        | Description |
|--------|-----------------|-------------|
| GET    | `/version`      | Returns current app version |
| GET    | `/temperature`  | Returns average temperature from senseBox devices |

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
  "version": "0.0.1"
}
```

---

## `/temperature` Endpoint 🌡️

### Endpoint

```text
/temperature
```

### Parameters

No parameters required.

### Requirements

- Fetch data from openSenseMap API
- Return average temperature from all available senseBox sensors
- Ignore sensor data older than 1 hour
- Handle unavailable sensor data safely

### Example Response

```json
{
  "average_temperature": 24.6,
  "unit": "°C"
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

### Test API inside container

```bash
curl http://localhost:5000/version
```

---

## Continuous Integration (CI)

GitHub Actions workflows are used for automated CI.

### CI Pipeline Includes

- Python linting using Pylint
- Dockerfile linting using Hadolint
- Docker image build validation & testing using Trivy
- Automated unit testing
- API integration testing
- OpenSSF Scorecard security analysis
- CodeQL static security analysis
- Dependency review on every pull request
- Automated dependency updates via Dependabot

---

## GitHub Actions Workflows

### `ci.yml`

Main CI workflow responsible for:
- linting
- testing
- Docker builds

### `scorecard.yml`

Security workflow responsible for:
- repository security analysis
- workflow security validation
- DevSecOps checks

### `codeql.yml`

SAST workflow responsible for:
- static analysis of Python source code
- security vulnerability detection
- weekly scheduled scans for new CVEs

### `dependency-review.yml`

Dependency gate workflow responsible for:
- scanning dependency changes on every pull request
- blocking merges that introduce known CVEs
- posting scan summaries as PR comments

---

## CI Testing

The CI pipeline automatically:
1. Builds the Docker image and checking it using Trivy
2. Starts the application
3. Calls `/version`
4. Verifies correct JSON response

---

## Contributing Workflow

1. Pick an issue from the project board

2. Create a feature branch

```bash
git checkout -b feature/your-feature-name
```

3. Commit using Conventional Commits

4. Push changes and create Pull Request

5. Reference issue using:

```text
closes #issue-number
```

---
