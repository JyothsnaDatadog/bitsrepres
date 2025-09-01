FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8080
# The env vars below help tag logs/traces
ENV DD_SERVICE=demo-app DD_ENV=dev DD_VERSION=1.0.0
CMD ["ddtrace-run", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "app:app"]
