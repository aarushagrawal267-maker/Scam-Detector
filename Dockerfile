# Container for the website + API, with Tesseract OCR (English + Hindi) so
# screenshot checking works. Suitable for Render "Docker" web services or any
# Docker host.
#   docker build -t scam-checker .
#   docker run -p 8000:8000 scam-checker
FROM python:3.13-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-hin \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scam_detector ./scam_detector
COPY app ./app
COPY bot ./bot
COPY models ./models

ENV PYTHONUNBUFFERED=1 \
    SCAM_STATS_DB=/app/data/stats.db \
    PORT=8000
RUN mkdir -p /app/data && useradd --create-home appuser && chown -R appuser /app/data
USER appuser

EXPOSE 8000
# Hosts such as Render set $PORT; default to 8000 locally.
# --no-access-log: do not write visitors' IP addresses to the logs (privacy).
# --proxy-headers: behind a host's proxy, rate limiting sees the real client IP.
CMD ["sh", "-c", "uvicorn app.server:app --host 0.0.0.0 --port ${PORT} --no-access-log --proxy-headers --forwarded-allow-ips='*'"]
