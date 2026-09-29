# AI client gateway (srv/gateway.py) — see deploy/deploy_gateway.sh.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements-gateway.txt .
RUN pip install --no-cache-dir -r requirements-gateway.txt

COPY cli ./cli
COPY srv ./srv

# One process: the key pools, bad-key quarantine and stats are process-local,
# so extra workers would only split them. Concurrency comes from the thread
# pool (THREAD_LIMIT), sized to Cloud Run --concurrency.
CMD exec uvicorn srv.gateway:app --host 0.0.0.0 --port "${PORT}" --workers 1 --timeout-keep-alive 75
