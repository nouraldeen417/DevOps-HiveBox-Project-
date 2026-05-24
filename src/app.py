from flask import Flask, jsonify

# Single source of truth for version
# Future CI/CD will read this value automatically
APP_VERSION = "0.0.1"

app = Flask(__name__)


@app.route("/version")
def get_version():
    """
    GET /version
    Returns the current running version of HiveBox as JSON.
    """
    return jsonify({"version": APP_VERSION})


if __name__ == "__main__":
    print(f"Starting HiveBox v{APP_VERSION}")
    app.run(host="0.0.0.0", port=5000, debug=False)