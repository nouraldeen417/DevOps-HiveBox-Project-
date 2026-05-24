# HiveBox 🐝

A scalable RESTful API for beekeepers, built around [openSenseMap](https://opensensemap.org/). Fetches real sensor data (temperature, humidity, pressure) from physical senseBox devices and returns clean JSON.

---

## Project Structure

```
hivebox/
├── src/
│   ├── __init__.py
│   └── app.py          ← Flask application
├── tests/
│   ├── __init__.py
│   └── test_app.py     ← pytest tests
├── conftest.py         ← pytest path config
├── Dockerfile
├── requirements.txt
└── LICENSE.md
└── Documentations/
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

### 5. Test it

```bash
curl http://localhost:5000/version
# {"version": "0.0.1"}
```

---

## Running Tests

```bash
pytest tests/
```

---

## Docker

```bash
# Build
docker build -t hivebox .

# Run
docker run -p 5000:5000 hivebox

# Test
curl http://localhost:5000/version
```

---

## API Endpoints

| Method | Endpoint   | Response                  |
|--------|------------|---------------------------|
| GET    | `/version` | `{"version": "0.0.1"}`   |

> More endpoints coming in later phases (`/temperature`, `/humidity`, `/health`, `/metrics`)

---

## Contributing Workflow

1. Pick an issue from the [project board](../../projects)
2. Create a branch: `git checkout -b feature/your-issue-name`
3. Make your changes
4. Push and open a PR — write `closes #N` in the description
5. PR gets reviewed and merged → issue auto-closes

> Direct pushes to `main` are blocked. All changes must go through a PR.

---

