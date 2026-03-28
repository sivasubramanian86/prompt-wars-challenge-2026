#!/usr/bin/env bash
# setup_gcp.sh — One-time GCP project configuration for Omni-Bridge
# Run this ONCE before the first Cloud Run deploy.
# Usage: bash setup_gcp.sh

set -euo pipefail

PROJECT_ID="prompt-wars-bengaluru-2026"
REGION="us-central1"
TOPIC="omnibridge-hitl-queue"
SUBSCRIPTION="omnibridge-hitl-sub"
SA_NAME="omnibridge-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Setting active project: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"

echo "==> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

echo "==> Creating Cloud Pub/Sub topic: ${TOPIC}"
gcloud pubsub topics create "${TOPIC}" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "Topic already exists."

echo "==> Creating Pub/Sub pull subscription: ${SUBSCRIPTION}"
gcloud pubsub subscriptions create "${SUBSCRIPTION}" \
  --topic="${TOPIC}" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "Subscription already exists."

echo "==> Creating dedicated Service Account: ${SA_NAME}"
gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="Omni-Bridge Cloud Run SA" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "SA already exists."

echo "==> Granting roles (least-privilege)..."
for ROLE in "roles/aiplatform.user" "roles/pubsub.publisher" "roles/logging.logWriter"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet
done

echo ""
echo "======================================================"
echo " GCP setup complete."
echo " Service Account: ${SA_EMAIL}"
echo " Pub/Sub topic:   ${TOPIC}"
echo " Pub/Sub sub:     ${SUBSCRIPTION}"
echo "======================================================"
echo " Next: run the deploy command shown after this script."
