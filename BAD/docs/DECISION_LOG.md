# Decision Log & Session Analysis (02/12/2026)

## 1. Decisions Made
-   **Bot Standardization**: We definitively separated `Ticket Assistant` (Prod) from `BAD-Tester` (Dev) using distinct tokens in `.env.main` and `.env.dev`.
-   **Deployment Strategy**: Shifted from `deploy_to_vm.sh` (Bash/SSH) to `deploy_to_vm.ps1` (PowerShell/GCloud IAP) to support Windows controllers and secure tunneling.
-   **Rogue Bot Isolation**: Instead of trying to hack into the inaccessible "Headsprung" VM, we invalidated its token (`PROJECT_PLANNER_TOKEN`). This was a faster, safer resolution.
-   **Uplink Protocol**: Chosen Discord Channel (`#antigravity-net`) over raw TCP sockets for node communication to leverage existing auth/logging infrastructure.

## 2. Resources That Work
-   **GCloud IAP Tunneling**: `gcloud compute ssh --tunnel-through-iap` is the only reliable way to access VMs without public IPs.
-   **Janitor Script**: `scripts/janitor.py` (Python) proved superior to `janitor.sh` (Bash) for cross-platform maintenance on Windows Dev machines.
-   **Discord Webhooks**: Reliable for "fire-and-forget" status updates (Heartbeat) without full bot login.

## 3. Abandoned Paths ("Rabbit Trails")
-   **Direct SSH (`ssh user@100.75.180.10`)**: Abandoned due to timeout/firewall issues. *Pivot*: Uses GCloud IAP.
-   **"Headsprung" Investigation**: Spent cycles trying to locate this VM owner. *decision*: It's legacy debt; nuking the token was more effective than finding the owner immediately.
-   **`start_ticket_bot.sh`**: Abandoned for `start_ticket_bot.ps1` as the primary controller is Windows.

## 4. Future Analysis Plan
To make this analysis regular:
1.  **Weekly Retrospective**: Create a `docs/RETROSPECTIVES/` log.
2.  **Review Trigger**: At the start of every "Planning" phase, the Agent MUST read `docs/DECISION_LOG.md` to avoid repeating "Rabbit Trails".
3.  **Metric**: "Time to Deploy" should be tracked in the Heartbeat.
