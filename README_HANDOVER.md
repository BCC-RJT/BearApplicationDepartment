# Handover Protocol

## Ongoing Work
- **Discord Integration**: We have established a dedicated communication channel `#antigravity-net` for cross-environment coordination.
  - **Channel ID**: `1470492715878973573`
  - **Webhook**: See `.env` (`ANTIGRAVITY_WEBHOOK_URL`)
  - **Action Required**: When starting a session in a new environment (e.g. cloud VM), please verify connectivity by sending a "Hello" message to this channel using the webhook. Documentation is in `BAD/docs/ANTIGRAVITY_COMMS.md`.

## Environment Setup
1. Clone the repo.
2. Ensure you have the `.env` file populated.
   - You MUST add `ANTIGRAVITY_WEBHOOK_URL` to your local `.env`. 
   - Ask the Controller for the secure URL if it's not in the repo secrets.
3. Install dependencies: `pip install -r requirements.txt`

- **Session Start**: Run `!open` in Discord (via `bad_bot`).
- **Antigravity Comms**: Use the `src/bridge/setup_antigravity_comms.py` script to verify or repair the channel if needed.

## Ticket System (Custom)
We have replaced external ticket bots with a native system in `Architect Bot`.
1.  **Start Bot**: `py src/bridge/architect_bot.py`
2.  **Setup Panel**: In `#tickets`, run `?setup_tickets`.
3.  **Workflow**:
    - Users click "📩 Open Ticket".
    - Staff manage with `?ticket [active|block|close]`.
    - Closing generates a transcript and moves to Archive.

---

## Session 2 Summary: Natural Language Interface & Session Management
- **Goal**: Enable natural language interaction for managing Discord bot conversations (`!open`, `!kickoff`).
- **Status**: Partially Complete / MVP Implemented.
- **Key Actions**:
    1.  **Manager Mode**: Implemented logic in `bad_bot.py` and `brain.py` to guide users based on environment sync status.
    2.  **Commands**: Added `!kickoff` (starts interactive agent), `!dashboard` (manager view), and `!close` (session wrap-up).
    3.  **Deployment**: Updated `deploy_to_vm.ps1` to include `google-generativeai`.
    4.  **Fixes**: Resolved duplicate command definitions and library import issues (`google.generativeai` vs `google.genai`).

### Known Issues / Remaining Work
1.  **Interactive Agent Limitations**: The current `src/agent/interactive.py` is a minimal implementation. It loops `brain.think` but lacks advanced agency (e.g., tool use is limited to what `brain.py` supports, which might need expansion).
2.  **Natural Language Robustness**: The "Manager Agent" logic in `brain.py` relies on a specific prompt. It may need tuning to handle edge cases or less structured user input gracefully.
3.  **Dependency Management**: `deploy_to_vm.ps1` manually installs dependencies. A more robust `requirements.txt` based installation on the VM is recommended for future scalability.
4.  **Model Availability**: The code currently hardcodes `gemini-2.5-flash`. Ensure this model remains available or update `brain.py` to be configurable via env vars.

### Next Steps (Immediate)
- **Refine Interactive Agent**: Enhance `src/agent/interactive.py` to support more complex actions or autonomous loops.
- **User Testing**: Conduct broader user testing with the Natural Language Interface to identify unique friction points.

---

## Session 3 Summary: Testing & Quality Assurance Infrastructure
- **Goal**: Build a robust testing suite for the AI-Discord Ticketing System to verify logic without real API keys and simulate failures.
- **Status**: Complete & Verified.
- **Key Actions**:
    1.  **Architecture**: Implemented a `unittest`-based test suite compatible with `pytest`.
    2.  **Mocks**: Created centralized mocks (`conftest.py`) for Discord Context, Google Gemini, and Google Drive.
    3.  **Test Coverage**:
        -   **Logic**: Verified interview flow (Complete/Incomplete status) and state transitions.
        -   **Permissions**: Implemented RBAC checks and prompt injection sanitization tests.
        -   **Chaos**: Simulated API failures (Drive 500 scenarios) and rate limits.
    4.  **Verification**: Validated all 7 tests pass successfully using `python tests/run_tests.py`.

### Next Steps
- **Integrate Tests**: Run these tests in CI/CD or before every deployment.
- **Expand Coverage**: Add tests for the actual `src/agent/interactive.py` once it is refined.

---

## Session 4 Summary: BADbot Persistence Fix & Ticket Assistant Deployment
- **Goal**: Fix BADbot automatically joining/greeting new tickets and deploy "Ticket Assistant".
- **Status**: Complete & Verified.
- **Key Actions**:
    1.  **BADbot Fix**: Identified active bot instance on remote VM (`100.75.180.10`). Deployed code to remove `on_guild_channel_create` listener and restarted service.
    2.  **Ticket Assistant**: Renamed "Receptionist Bot" to "Ticket Assistant" (in `src/ticket_bot/main.py`), fixed startup bugs, and deployed to VM.
    3.  **Verification**: Verified BADbot is silent in new tickets and Ticket Assistant is online/named correctly.

### Current Bot State on VM (`100.75.180.10`)
- **BADbot**: Active process (`python3 BAD/src/bridge/bad_bot.py`). Passive in tickets.
- **Ticket Assistant**: Active process (`python3 BAD/src/ticket_bot/main.py`). Passive listener (waiting for intent/commands).

### Deployment
- To update either bot, use `BAD/scripts/deploy_to_vm.ps1` and restart the respective python process on the VM via SSH.

---

## Session 5 Summary: Service Account Blocker Resolution & Production Deployment
- **Goal**: Resolve `disableServiceAccountKeyCreation` policy blocker and deploy Ticket Bot with Google Drive integration.
- **Status**: Complete & Verified.
- **Key Actions**:
    1.  **Authentication Strategy**: Shifted from Service Account Keys to **Application Default Credentials (ADC)** to bypass Org Policy.
    2.  **VM Provisioning**: Implemented **VNC-based Authentication Protocol** to resolve headless `gcloud` login failures.
    3.  **Deployment**: Packaged and deployed `Ticket Bot` to `bad-node-01` (`100.75.180.10`).
    4.  **Integration**: Verified end-to-end flow from Discord Ticket -> AI Interview -> Google Drive Archive.

### Next Steps
- **Operations**: Monitor `bad-node-01` for stability.
- **Expansion**: Add "Manager Ping" feature to notify specific roles on new ticket creation.

---

## Session 6 Summary: Ticket Workflow Consolidation
- **Goal**: Consolidate ticket workflows into a single agent (`tickets_assistant.py`) and deprecate `architect_bot.py` ticket functions.
- **Status**: Complete & Verified.
- **Key Actions**:
    1.  **Unified Bot**: `tickets_assistant.py` (v2.0) now handles the entire lifecycle: Panel Check -> Ticket Creation -> AI Interview -> Proposal -> Handover.
    2.  **Singleton Lock**: Added socket-based locking to prevent duplicate bot instances.
    3.  **UI/UX Improvements**: Implemented `ProposalView` for one-click ticket approval and submission to Manager Inbox.
    4.  **Architect Bot**: Stripped of ticket setup responsibilities; now focuses solely on Planning/Workflow generation.
- **Current State**: 
    - `tickets_assistant.py` is the primary running service.
    - AI Agent proposes tickets with Title/Urgency/Description before finding them.
- **Next Steps**:
    - Verify if manual ticket management commands (`?ticket active/block`) are needed in `tickets_assistant.py` or if the AI/UI flow suffices.

