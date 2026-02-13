# System Architecture

## Overview
The Bear Application Department (B.A.D.) system is a distributed bot network managing support tickets and project workflows across Discord and Google Cloud.

## Nodes
| Node ID | Hostname | IP Address | Role | Environment | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ControllerPC** | `ControllerPC` | `Localhost` | Development | `DEV` | 🟢 Online |
| **Foundation-VM** | `bad-node-01` | *Migration Pending* | Production | `PROD` | 🟡 Active (Old Context) |
| **Headsprung** | `Headsprung` | `100.75.180.10` | *Unknown* | `Unknown` | 🔴 Rogue / Isolated |

## Bots
| Bot Name | Function | Token Ref | Hosting | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Ticket Assistant** | Support Tickets | `TICKET_ASSISTANT_TOKEN` | `Foundation-VM` (Prod) | Primary interface. |
| **BADbot** | Ops / Maintenance | `BADBOT_TOKEN` | `Foundation-VM` | Background tasks. |
| **Project Planner** | *Legacy/Rogue* | `PROJECT_PLANNER_TOKEN` | `Headsprung` | **DISABLED** (Token Revoked). |

## Communication (Antigravity Uplink)
-   **Method**: Discord Channel Bridging
-   **Channel**: `#antigravity-net` (ID: `1470492715878973573`)
-   **Protocol**:
    1.  **Presence**: Nodes announce startup ("Signal").
    2.  **Heartbeat**: Nodes emit a "Breathing" signal every 5-30 mins.
    3.  **Janitor**: Maintenance reports posted via Webhook.

## Cloud Resources
-   **Current Project**: `takeoff-specialist` (Legacy)
-   **Target Project**: `BearAppDept-Prod` (Future Consolidation)
-   **Authentication**: ADC (Application Default Credentials) via `gcloud auth application-default login`.

## File Structure
-   `src/bridge/`: Core bot logic (`tickets_assistant.py`, `cogs/`).
-   `scripts/`: Automation scripts (`janitor.py`, `start_ticket_bot.ps1`).
-   `docs/`: Documentation (`PLAYBOOK.md`, `ARCHITECTURE.md`).
-   `archive/`: Deprecated assets (30-day retention).
