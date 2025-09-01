import logging
import sys
from flask import Flask, jsonify

# --- Datadog log correlation (trace_id / span_id) ---
# If DD_LOGS_INJECTION=true is set, ddtrace will inject IDs automatically.
# We also enable it programmatically here, just in case.
try:
    from ddtrace import config  # ddtrace is installed via requirements.txt
    config.logs.injection = True
except Exception:
    # If ddtrace isn't available at import time, we just skip programmatic enablement.
    pass

# --- Logging setup ---
# Send logs to stdout so the Datadog Agent (in Docker) can tail them.
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(name)s "
        "trace_id=%(dd.trace_id)s span_id=%(dd.span_id)s "
        "%(message)s"
)
handler.setFormatter(formatter)

root_logger = logging.getLogger()
# Replace any default handlers to avoid duplicate logs
for h in list(root_logger.handlers):
    root_logger.removeHandler(h)
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger("demo-app")

# --- Flask app ---
app = Flask(__name__)

@app.route("/")
def hello():
    logger.info("Request received at '/'")
    return "Hello from Datadog demo!", 200

@app.route("/healthz")
def healthz():
    # Lightweight health endpoint for readiness checks
    return jsonify(status="ok"), 200

@app.route("/error")
def boom():
    # Demonstrates an application error with full stack trace in logs
    try:
        logger.error("Something went wrong! About to raise RuntimeError()")
        raise RuntimeError("Demo error!")
    except Exception:
        # Logs full stack trace + message; ddtrace adds trace/span IDs
        logger.exception("Unhandled error in /error")
        # Re-raise so Flask/Gunicorn returns 500 and APM marks span as error
        raise

# Optional: global error handler (catches anything not handled above)
@app.errorhandler(Exception)
def handle_any_exception(e):
    # If an exception bubbles up, log it with stack trace as well
    logger.error("Global handler caught an exception", exc_info=e)
    # Return a generic 500 response (message kept simple for demo)
    return "Internal Server Error", 500

if __name__ == "__main__":
    # In Docker we start via `ddtrace-run gunicorn ...`, but this lets you run locally too:
    app.run(host="0.0.0.0", port=8080)
