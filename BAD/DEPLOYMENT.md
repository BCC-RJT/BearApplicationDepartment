# Ticket Assistant Deployment Guide

This guide explains how to deploy the Ticket Assistant bot to a new server (PROD) while keeping the original server as DEV.

## 1. Prerequisites

- **Docker**: Installed on the target server.
- **Git**: To clone the repository.
- **Discord Bot Token**: You need a separate bot token for PROD.

## 2. Setup (Target Server)

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/BCC-RJT/BearApplicationDepartment.git
    cd BearApplicationDepartment
    ```

2.  **Configure Environment**:
    -   Copy the example config:
        ```bash
        cp .env.example .env
        ```
    -   Edit `.env` and fill in your details:
        -   `DISCORD_TOKEN`: Your **PROD** bot token.
        -   `SERVER_ID`: Set to `BAD-PROD`.
        -   `TICKET_*_ID`: Category IDs for the PROD server.
        -   `GOOGLE_API_KEY`: Your Gemini API key.

3.  **Navigate to Codebase**:
    ```bash
    cd BAD
    ```

## 3. Running the Bot

We use **Docker** to ensure the bot runs exactly the same as in development.

### Start Script
Run the helper script:
```bash
chmod +x start_ticket_bot.sh
./start_ticket_bot.sh
```

### Manual Docker Command
If you prefer running manually:
```bash
docker build -t ticket-assistant .
docker run -d --name ticket-assistant --restart unless-stopped --env-file ../.env -v $(pwd)/data:/app/data ticket-assistant
```

## 4. Feature Development Workflow

We use a **Git Branching** strategy to separate work.

### The DEV Server (Current)
-   **Branch**: `dev`
-   **Role**: Experimental features, testing.
-   **Database**: Local `data/bad.db` (contains test tickets).

### The PROD Server (Target)
-   **Branch**: `main`
-   **Role**: Stable, user-facing.
-   **Updates**:
    1.  Push changes from DEV to `dev` branch.
    2.  Merge `dev` into `main` via Pull Request.
    3.  On PROD server: `git pull origin main` and restart bot (`./start_ticket_bot.sh`).

## Notes
-   **Database**: The SQLite database (`data/bad.db`) is stored in a volume/folder. It is **NOT** synced between servers. This is intentional.
-   **Logs**: View logs with `docker logs -f ticket-assistant`.
