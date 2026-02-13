# Bear Application Department (B.A.D.) Playbook

## 1. Core Principles (Lessons Learned)

### ☁️ Cloud Hygiene
-   **Consolidation**: Avoid "Cloud Sprawl". All resources must reside in a single, authoritative project (e.g., `BearAppDept-Prod`).
-   **Resource Tracking**: Every provisioned resource (VM, static IP, bucket) MUST be documented in `docs/INFRASTRUCTURE.md` immediately upon creation.
    -   *Lesson*: We lost track of `100.75.180.10` ("Headsprung") because it was in a disparate project (`takeoff-specialist`) without central documentation.
-   **Naming Convention**: Names are immutable references. If a hostname changes (e.g., `bad-node-01` -> `headsprung`), code refactoring must happen **immediately**.

### 🤖 Bot Identity & Security
-   **Token Isolation**: NEVER share tokens between environments.
    -   `DEV`: Uses `BAD-Tester` (or similar Dev bot).
    -   `PROD`: Uses `Ticket Assistant`.
-   **Local vs. Hosted**:
    -   Production bots (`Ticket Assistant`) must **NEVER** run locally on developer workstations (`ControllerPC`).
    -   Use `start_ticket_bot.ps1 -Local` ONLY for development bots.
-   **Loop Prevention**: All bots must explicitly ignore messages from other bots (check `message.author.bot`) to prevent infinite chaos loops.

### 📢 Communication (Antigravity Uplink)
-   **Presence**: All nodes must announce their status to `#antigravity-net` upon startup.
-   **Heartbeat**: Systems must "breathe" (emit a heartbeat signal) every 5-30 minutes to prove liveness.
-   **Webhooks**: Use secure webhooks for cross-environment signaling where full bot login isn't possible.

## 2. Retrospective: The "Rogue Bot" Incident
**Incident**: A "Project Planner" bot was active on an unknown VM, intercepting ticket messages and causing confusion.
**Root Cause**:
1.  Legacy VM (`100.75.180.10`) was left running in an unmonitored project.
2.  Bot token was reused or not rotated.
3.  Lack of "who is running where" documentation.
**Resolution**:
1.  Identified VM via legacy scripts (`deploy_to_vm.sh`).
2.  Isolated bot by disabling its token in `.env`.
3.  Implemented `Uplink` to visualize active nodes.

## 3. Strategic Forgetting Policy
We maintain an `archive/` directory for deprecated assets.
-   **Rule**: Items in `archive/` are deleted if not accessed for **30 days**.
-   **Process**: When a script or doc is superseded, move it to `archive/` instead of deleting immediately.
-   **Recovery**: Check `archive/` first when looking for "old ways of doing things".
