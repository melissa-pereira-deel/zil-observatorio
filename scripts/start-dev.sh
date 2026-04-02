#!/bin/bash
# Start all ZIL dev services without Docker
# Usage: bash scripts/start-dev.sh

set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"

# Start FastAPI in background
echo "▶ Starting FastAPI on :8000..."
cd "$REPO/apps/api"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Start Next.js in background
echo "▶ Starting Next.js on :3000..."
cd "$REPO/apps/web"
npm run dev &
WEB_PID=$!

echo "✓ API PID=$API_PID  Web PID=$WEB_PID"
echo "  API  → http://localhost:8000"
echo "  Web  → http://localhost:3000"

# Wait for either to exit
wait $API_PID $WEB_PID
