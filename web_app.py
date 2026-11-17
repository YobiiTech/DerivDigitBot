import os
import logging
from flask import Flask, Response, jsonify
from dashboard import build_dashboard
from cloud_collector import get_status, start_collector

app = Flask(__name__)

logger = logging.getLogger(__name__)


if os.environ.get("START_CLOUD_COLLECTOR", "").lower() == "true":
    started = start_collector()
    logger.warning("COLLECTOR START: pid=%s started=%s", os.getpid(), started)


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def home():
    page = build_dashboard()
    return Response(page, mimetype="text/html")


@app.route("/healthz")
def health():
    return jsonify({
        "status": "ok",
        "application": "Deriv Digit Intelligence"
    })


@app.route("/feed-status")
def feed_status():
    status = get_status()
    logger.warning("FEED STATUS REQUEST: pid=%s status=%s ticks=%s", os.getpid(), status["status"], status["ticks_received"])
    return jsonify(status)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 8000)),
        debug=False
    )
