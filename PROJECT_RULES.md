# Project Rules

1. **Do NOT run the bot locally.** The bot should not be started via `run_command` on this machine (`ControllerPC`). The user handles execution/deployment.
2. The current environment is considered a DEV environment. We will split between DEV and MAIN/PROD later.
3. **MANDATORY ANNOUNCEMENT**: Every time a new global session is opened, the team MUST run `py BAD/src/bridge/announce_presence.py` and report status on the **Global Session Goal** (VM Connectivity).
