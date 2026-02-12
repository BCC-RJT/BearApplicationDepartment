# Ticket Assistant 2.0 Inventory

**Date:** 2026-02-11
**Version:** 2.0
**Deployment:** Docker Container (`bad-ticket-bot`)

## Overview
The "Ticket Assistant 2.0" is a robust, isolated bot dedicated to handling support tickets. It has been refactored to run in a Docker container for consistency across dev and prod environments.

## Architecture

### 1. `src/bridge/tickets_assistant.py` (The Bot)
**Type:** Discord Bot
**Responsibilities:**
- Manages ticket lifecycle (`OPEN`, `PROPOSE`, `CLOSE`).
- Integrates with `AgentBrain` (Gemini) for natural language understanding.
- Runs on port **45679** (Singleton Lock) to avoid conflict with `bad_bot`.

### 2. Infrastructure (Docker)
**Type:** Containerization
**Files:**
- `Dockerfile`: Python 3.11-slim base image.
- `docker-compose.yml`: Defines the service, restarts always, mounts logs.
- `requirements.txt`: Python dependencies.

### 3. Service Management (Systemd)
**Type:** Process Manager (VM)
**Service:** `bad-ticket-bot.service`
**Behavior:**
- Auto-starts on boot.
- Auto-restarts on crash.
- Logs to `/home/Headsprung/logs/ticket_bot.log`.

## Deployment

### Local Development
1. Ensure Docker is installed.
2. Run:
```bash
docker-compose up --build
```

### Production (VM)
1. Deploy code:
```bash
./deploy_to_vm.ps1
```
2. Start Docker service:
```bash
bash BAD/scripts/start_docker.sh
```

## Reversion Instructions
To revert to the pure Python script version (1.0), stop the Docker container and run the script manually:
```bash
docker-compose down
python3 src/bridge/tickets_assistant.py
```
