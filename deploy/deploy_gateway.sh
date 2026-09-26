#!/bin/bash
# Deploy srv/gateway.py as the private Cloud Run service "ai-client".
#
# Usage:
#   ./deploy/deploy_gateway.sh                 # ENV=staging (echonos-staging)
#   ENV=prod ./deploy/deploy_gateway.sh        # echonos-fa038; requires branch main or FORCE_PROD=1
#
# Resulting URL (deterministic, what callers derive from the project number):
#   https://ai-client-<PROJECT_NUMBER>.<REGION>.run.app
set -euo pipefail

ENV="${ENV:-staging}"
case "$ENV" in
    staging)
        PROJECT_ID="${PROJECT_ID:-echonos-staging}"
        MIN_INSTANCES="${MIN_INSTANCES:-0}"
        ;;
    prod)
        _branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
        if [ "$_branch" != "main" ] && [ "${FORCE_PROD:-}" != "1" ]; then
            echo "ERROR: ENV=prod requires branch main (current: $_branch). Set FORCE_PROD=1 to override." >&2
            exit 1
        fi
        PROJECT_ID="${PROJECT_ID:-echonos-fa038}"
        # Every FAL call in prod goes through this service: keep one warm.
        MIN_INSTANCES="${MIN_INSTANCES:-1}"
        ;;
    *)
        echo "ERROR: ENV must be 'staging' or 'prod' (got '$ENV')" >&2
        exit 1
        ;;
esac

REGION="${REGION:-us-central1}"
SERVICE_NAME="ai-client"
RUNTIME_SA_NAME="ai-client-gateway"
RUNTIME_SA="${RUNTIME_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
# Everything that calls FAL today runs as one of these two accounts (Cloud
# Functions / Cloud Run as firebase-adminsdk, the Vercel app and a few
# functions as cloud-run-invoker).
INVOKERS=(
    "firebase-adminsdk-fbsvc@${PROJECT_ID}.iam.gserviceaccount.com"
    "cloud-run-invoker@${PROJECT_ID}.iam.gserviceaccount.com"
)
# Secrets already exist per project; the gateway reads them, callers no longer need them.
SECRETS="FAL_KEYS=FAL_KEYS:latest"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_TAG="$(git -C "$ROOT_DIR" rev-parse --short HEAD)"
if [ -n "$(git -C "$ROOT_DIR" status --porcelain -- cli srv Dockerfile requirements-gateway.txt)" ]; then
    IMAGE_TAG="${IMAGE_TAG}-dirty"
fi
IMAGE_BASE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

echo "============================================"
echo "Deploying ${SERVICE_NAME} (${ENV})"
echo "  Project: ${PROJECT_ID} (${PROJECT_NUMBER})"
echo "  Region:  ${REGION}"
echo "  Image:   ${IMAGE_BASE}:${IMAGE_TAG}"
echo "============================================"

echo "Step 1: runtime service account + secret access..."
gcloud iam service-accounts describe "$RUNTIME_SA" --project="$PROJECT_ID" >/dev/null 2>&1 || \
    gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
        --display-name="AI client gateway runtime" --project="$PROJECT_ID"
# A just-created service account takes a few seconds to become visible to IAM.
for attempt in 1 2 3 4 5 6; do
    if gcloud secrets add-iam-policy-binding FAL_KEYS \
        --member="serviceAccount:${RUNTIME_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" --quiet >/dev/null; then
        break
    fi
    [ "$attempt" = 6 ] && exit 1
    echo "  service account not visible yet; retrying in 10s..."
    sleep 10
done

echo "Step 2: build image..."
gcloud builds submit "$ROOT_DIR" \
    --tag="${IMAGE_BASE}:${IMAGE_TAG}" \
    --project="$PROJECT_ID"
gcloud container images add-tag "${IMAGE_BASE}:${IMAGE_TAG}" "${IMAGE_BASE}:latest" \
    --project="$PROJECT_ID" --quiet

echo "Step 3: deploy..."
# --concurrency matches THREAD_LIMIT: blocking /submit calls hold a thread for
# the whole generation. --timeout covers the 600s default poll deadline.
gcloud run deploy "$SERVICE_NAME" \
    --image="${IMAGE_BASE}:${IMAGE_TAG}" \
    --region="$REGION" \
    --platform=managed \
    --no-allow-unauthenticated \
    --service-account="$RUNTIME_SA" \
    --memory=512Mi \
    --cpu=1 \
    --concurrency=80 \
    --timeout=900 \
    --min-instances="$MIN_INSTANCES" \
    --max-instances=20 \
    --set-env-vars="THREAD_LIMIT=80,POLL_TIMEOUT_SEC=600,POLL_INTERVAL_SEC=1,ECHONOS_ENV=${ENV}" \
    --set-secrets="$SECRETS" \
    --project="$PROJECT_ID"

echo "Step 4: invoker bindings..."
for member in "${INVOKERS[@]}"; do
    gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
        --region="$REGION" \
        --member="serviceAccount:${member}" \
        --role="roles/run.invoker" \
        --project="$PROJECT_ID" --quiet >/dev/null
done

echo ""
echo "Deployed: https://${SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app"
