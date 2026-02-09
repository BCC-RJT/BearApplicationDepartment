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
