# HiveBox 🐝 — Phase 3

Phase 3 focuses on improving code quality, container best practices, automated testing, and Continuous Integration (CI) for HiveBox.

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
│   └── workflows/
│       ├── ci.yml
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

## Development Tools

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
- Docker image build validation & testin using Trivy
- Automated unit testing
- API integration testing
- OpenSSF Scorecard security analysis

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
