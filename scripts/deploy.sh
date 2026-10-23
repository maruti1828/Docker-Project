#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE="ghcr.io/maruti1828/shoppulse:latest"
HEALTH_URL="http://localhost:8000/health"

echo "==> Pulling latest ShopPulse image..."
docker compose pull api

echo "==> Recreating ShopPulse API..."
docker compose up -d --no-deps --force-recreate api

echo "==> Checking application health..."
for attempt in $(seq 1 15); do
    if curl --fail --silent "$HEALTH_URL"; then
        echo
        echo "Deployment successful."
        exit 0
    fi

    sleep 2
done

echo "ERROR: ShopPulse did not become healthy."
docker compose logs --tail=50 api
exit 1
