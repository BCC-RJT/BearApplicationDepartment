# Project Freeze: Parallel Triage Agent (The "Triage Specialist")

**Status**: FROZEN / ON HOLD
**Date**: 2026-02-10

## Goal
Design and implement a parallel process where an autonomous agent (Triage Specialist) monitors GitHub issues labeled `agent-reported`, triages them, and takes action (e.g., fixes bugs, deploys changes) without direct user intervention. This aims to create a self-healing or self-improving loop.

## Current State

### 1. GitHub Interface
-   **Script**: `scripts/github_issues.py`
-   **Capabilities**:
    -   `list`: Lists open issues.
    -   `get <id>`: Reads issue details.
    -   `comment <id> <body>`: Posts comments.
    -   `close <id>`: Closes issues.
-   **Environment**: Relies on `GITHUB_TOKEN` and `REPO_NAME` (currently `BCC-RJT/BearApplicationDepartment`).

### 2. Ticket Bot (The Subject)
-   **Path**: `src/ticket_bot/`
-   **Features**:
    -   Creates private ticket channels.
    -   Maintains a SQLite database of tickets.
    -   **New Feature**: "Discard Ticket" button added to `NewTicketView`.
-   **Deployment**:
    -   Service must be restarted for code changes to take effect.
    -   Created `scripts/restart_ticket_bot.ps1` to handle safe restarts (finding process by command line arguments).

### 3. Known Gaps & Next Steps
When picking this project back up, focus on the following:

1.  **Deployment Automation**:
    -   The `deploy_tickets.py` script exists but is not fully integrated into a CI/CD or agent workflow.
    -   Changes to the bot require a manual restart (`scripts/restart_ticket_bot.ps1`). This should be automated when the agent pushes code.

2.  **Verification Loop**:
    -   The agent currently lacks a robust way to *verify* that its changes are live and working before closing the issue.
    -   **Protocol Update**: Need to update `OPERATIONAL_PROTOCOL.md` to mandate a "Verify Deployment" step (e.g., check process status, run a test command) before marking tasks as done.

3.  **Agent Persona**:
    -   Ideally, a dedicated "Triage Agent" runs in a loop, polling for issues. Currently, this is triggered manually or by the user.

## Relevant Files
-   `scripts/github_issues.py`
-   `src/ticket_bot/main.py`
-   `src/ticket_bot/database.py`
-   `scripts/restart_ticket_bot.ps1`
-   `docs/OPERATIONAL_PROTOCOL.md`

## Resume Instructions
1.  Check `scripts/github_issues.py list` for any pending backend tasks.
2.  Review `src/ticket_bot` for latest changes.
3.  Ensure the bot is running (`tasklist /FI "IMAGENAME eq python.exe"`).
4.  Implement the **Verification Loop** identified above.
