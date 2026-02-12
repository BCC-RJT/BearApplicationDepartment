#!/bin/bash

# Configuration
SERVICE_NAME="bad-ticket-bot"
SERVICE_FILE="BAD/scripts/${SERVICE_NAME}.service"
USER="Headsprung"
HOME_DIR="/home/${USER}"

echo "🔧 Setting up ${SERVICE_NAME} on $(hostname)..."

# 1. Stop any existing instances (Clean Slate)
echo "🛑 Stopping existing processes..."
pkill -f "bridge/tickets_assistant.py" || true
pkill -f "ticket_bot/main.py" || true

# 2. Check Service File Existence
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found at $SERVICE_FILE"
    exit 1
fi

# 3. Create Log Directory
mkdir -p "${HOME_DIR}/logs"

# 4. Install Service
echo "📦 Installing systemd service..."
sudo cp "$SERVICE_FILE" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"

# 5. Start Service
echo "🚀 Starting ${SERVICE_NAME}..."
sudo systemctl restart "${SERVICE_NAME}"

# 6. Verify Status
echo "✅ Service Status:"
sudo systemctl status "${SERVICE_NAME}" --no-pager
