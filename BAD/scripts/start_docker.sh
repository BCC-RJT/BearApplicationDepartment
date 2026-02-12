#!/bin/bash
PROJECT_ROOT="/home/Headsprung/BAD"
SERVICE_NAME="bad-ticket-bot"

# 1. Stop Systemd Service (if running)
echo "🛑 Stopping systemd service..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
    sudo systemctl disable "$SERVICE_NAME"
    echo "✅ Systemd service stopped and disabled."
else
    echo "ℹ️ Systemd service not running."
fi

# 2. Check Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker Headsprung
    echo "Docker installed. You may need to relogin for group changes to take effect."
    # Temporary fix for current session
    newgrp docker
fi

# 3. Start Container
echo "🚀 Starting Docker Container..."
cd "$PROJECT_ROOT" || exit 1

# Force overwrite .env from parent (which is synced by deploy script)
if [ -f ../.env ]; then
    echo "Using .env from parent directory..."
    cp ../.env .env
else
    echo "⚠️ Parent .env not found!"
fi

# Docker Compose Up
if command -v docker-compose &> /dev/null; then
  sudo docker-compose up -d --build
else
  sudo docker compose up -d --build
fi

echo "✅ Docker Container Started."
sudo docker ps | grep bad-ticket-bot
