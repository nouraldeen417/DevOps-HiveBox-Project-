from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/version")
def version():
    return jsonify({"version": "0.0.1"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)