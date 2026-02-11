#!/bin/bash

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Check if .env exists in parent directory (Repo Root) or current (BAD)
if [ -f "../.env" ]; then
    ENV_FILE="../.env"
elif [ -f ".env" ]; then
    ENV_FILE=".env"
else
    echo "❌ Error: .env file not found. Please create one from .env.example"
    exit 1
fi

echo "🚀 Building Ticket Assistant..."
docker build -t ticket-assistant .

echo "🔥 Starting Ticket Assistant..."
# Mount the .env file to /.env in the container
docker run -d \
  --name ticket-assistant \
  --restart unless-stopped \
  -v "$(pwd)/data:/app/data" \
  --env-file "$ENV_FILE" \
  ticket-assistant

echo "✅ Bot started! Logs:"
docker logs -f ticket-assistant
