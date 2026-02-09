# Ticket System 1.0 Inventory

**Date:** 2026-02-09
**Version:** 1.0
**Git Tag:** `ticket-system-1.0` (To be created)

## Overview
The "Ticket System 1.0" is a Discord-based project initiation workflow managed by the `ProjectManager` cog within the `BAD` bot. It detects new channels named `ticket-*` and guides the user through a project planning phase.

## Components

### 1. `src/bridge/cogs/project_manager.py`
**Type:** Discord Cog
**Responsibilities:**
- Listens for `on_guild_channel_create` to detect `ticket-*` channels.
- Manages an in-memory state machine for each ticket channel:
    - `INIT`: Channel created, welcome message sent.
    - `GATHERING`: Collecting user requirements.
    - `PLANNING`: Generating a plan via `AgentBrain`.
    - `REVIEW`: Waiting for user approval.
    - `APPROVED`: Creating project structure.
- **Key Commands/Triggers:**
    - "Plan Project": Transitions from `INIT` to `GATHERING`.
    - "Generate Plan": Transitions from `GATHERING` to `PLANNING`.
    - "Approve": Transitions from `REVIEW` to `APPROVED`.
    - "Refine": Returns to `GATHERING`.

### 2. `src/bridge/bad_bot.py`
**Type:** Main Bot Runner
**Responsibilities:**
- Initializes the `discord.Bot`.
- Loads extensions (cogs) dynamically from `src/bridge/cogs/`, including `project_manager.py`.
- Provides `AgentBrain` integration via `bot.brain`.

### 3. `src/db.py`
**Type:** Database Interface
**Responsibilities:**
- Provides SQLite connection (`bad.db`).
- Currently stores "results" (job_id, file_url) but **does not persist ticket state**. Ticket state is currently ephemeral (RAM only).

## Workflow Logic (Concept)

1.  **Detection**: Bot notices a new channel starting with `ticket-`. (Note: Some latency, ~2s sleep).
2.  **Engagement**: Bot sends an embed asking if this is a new project ("Plan Project").
3.  **Gathering**: User provides details. Bot accumulates chat history in memory.
4.  **Planning**: User requests "Generate Plan". Bot uses `AgentBrain` to generate a markdown implementation plan.
5.  **Execution**: User approves. Bot creates a Discord Category named `Project-{channel-name}` with channels:
    - `discussion`
    - `tasks`
    - `docs`

## Reversion Instructions
To revert the codebase to this state, use the following command:
```bash
git checkout ticket-system-1.0
```
**Note:** Since ticket state is in-memory, reverting the code will not restore active tickets' states if the bot was restarted.
