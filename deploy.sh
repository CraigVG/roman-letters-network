#!/bin/bash
# Deploy Roman Letters to Google Cloud Run
# Usage: ./deploy.sh [project-id]

set -e

PROJECT_ID="${1:-roman-letters}"
REGION="us-central1"
SERVICE="roman-letters"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE"

echo "=== Building and deploying Roman Letters ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE"

# Ensure gcloud is authenticated
gcloud config set project "$PROJECT_ID"

# Build the Docker image
echo "=== Building Docker image ==="
gcloud builds submit --tag "$IMAGE" .

# Deploy to Cloud Run
echo "=== Deploying to Cloud Run ==="
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 80 \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --concurrency 100

# Get the URL
URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')
echo ""
echo "=== Deployed! ==="
echo "URL: $URL"
echo ""
echo "Next steps:"
echo "  1. Register romanletters.org"
echo "  2. Map custom domain: gcloud run domain-mappings create --service $SERVICE --domain romanletters.org --region $REGION"
echo "  3. Update DNS: A record to the Cloud Run IP"
echo "  4. Submit sitemap to Google Search Console: ${URL}/sitemap-index.xml"
