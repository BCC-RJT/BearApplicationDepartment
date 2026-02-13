#!/bin/bash

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Default to "dev" if not specified, but check arguments
ENVIRONMENT=$1

if [ "$ENVIRONMENT" == "main" ]; then
    ENV_FILE=".env.main"
    CONTAINER_NAME="ticket-assistant-main"
    echo "🌍 Target Environment: MAIN"
elif [ "$ENVIRONMENT" == "dev" ]; then
    ENV_FILE=".env.dev"
    CONTAINER_NAME="ticket-assistant-dev"
    echo "🛠️ Target Environment: DEV"
else
    # Fallback / Default
    if [ -f ".env" ]; then
        ENV_FILE=".env"
        CONTAINER_NAME="ticket-assistant"
        echo "⚠️ No environment specified (or found). Defaulting to '.env' and 'ticket-assistant'."
        echo "   Usage: ./start_ticket_bot.sh [dev|main]"
    else
        echo "❌ Error: .env file not found. Please create .env, .env.dev, or .env.main"
        exit 1
    fi
fi

# Check if the specific env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Configuration file '$ENV_FILE' not found!"
    exit 1
fi

echo "🚀 Building Ticket Assistant..."
docker build -t ticket-assistant .

echo "🔥 Starting Ticket Assistant ($CONTAINER_NAME)..."

# Stop/Remove existing container if running
if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "🛑 Stopping existing container..."
    docker rm -f $CONTAINER_NAME
fi

# Mount the .env file to /.env in the container
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -v "$(pwd)/data:/app/data" \
  --env-file "$ENV_FILE" \
  ticket-assistant

echo "✅ Bot started! Logs:"
docker logs -f $CONTAINER_NAME
