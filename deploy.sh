#!/usr/bin/env bash
# One-time GCP setup script — run this before the first deploy.
# Prerequisites: gcloud CLI installed and authenticated (gcloud auth login).
# Usage: bash deploy.sh

set -euo pipefail

# ── Configuration — edit these ──────────────────────────────────────────────
PROJECT_ID="your-gcp-project-id"
REGION="europe-west1"
SERVICE_NAME="transcription-platform"
WHISPER_MODEL="medium"

# Your Google OAuth credentials (from console.cloud.google.com/apis/credentials)
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
# ────────────────────────────────────────────────────────────────────────────

echo "→ Setting project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "→ Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  iap.googleapis.com \
  secretmanager.googleapis.com

echo "→ Creating Artifact Registry repository"
gcloud artifacts repositories create transcription \
  --repository-format=docker \
  --location="$REGION" \
  --description="Transcription Platform images" \
  || true   # ignore if already exists

echo "→ Storing secrets in Secret Manager"
echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets create transcription-google-client-id \
  --data-file=- --replication-policy=automatic 2>/dev/null \
  || echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets versions add transcription-google-client-id --data-file=-

echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create transcription-google-client-secret \
  --data-file=- --replication-policy=automatic 2>/dev/null \
  || echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets versions add transcription-google-client-secret --data-file=-

echo "→ Granting Cloud Build access to secrets"
CB_SA="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"
gcloud secrets add-iam-policy-binding transcription-google-client-id \
  --member="serviceAccount:$CB_SA" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding transcription-google-client-secret \
  --member="serviceAccount:$CB_SA" --role="roles/secretmanager.secretAccessor"

echo "→ Running first Cloud Build deploy"
gcloud builds submit . \
  --config=cloudbuild.yaml \
  --substitutions="_REGION=$REGION,_SERVICE_NAME=$SERVICE_NAME,_WHISPER_MODEL=$WHISPER_MODEL"

echo ""
echo "✓ Initial deploy complete."
echo ""
echo "Next steps:"
echo "  1. Get your Cloud Run URL:"
echo "     gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'"
echo ""
echo "  2. Set up Cloud IAP (in GCP Console → Security → Identity-Aware Proxy):"
echo "     - Enable IAP for the Cloud Run service"
echo "     - Add your company's Google Workspace domain to the allowed principals"
echo ""
echo "  3. Add the IAP callback URL to your OAuth client's Authorized Redirect URIs"
echo "     in console.cloud.google.com/apis/credentials"
echo ""
echo "  4. Connect Cloud Build to your Git repo for automatic deploys on push:"
echo "     console.cloud.google.com/cloud-build/triggers"
