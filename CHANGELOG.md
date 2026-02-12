# Changelog

## [Unreleased]

### Added
- **Secure Test Bot Environment**: Created `BAD-Tester` bot for automated testing without risk to production channels.
- **Automated Verification**: Added `BAD/scripts/test_agent.py` to verify bot connectivity and authorization.
- **Debug Tool**: Added `BAD/scripts/debug_discord.py` for direct connectivity troubleshooting.
- **Browser Intervention Protocol**: Added to `engineering-playbook/docs/WORKFLOWS.md` to handle browser-based blockers.
- **Bot Nickname Enforcement**: `bad_bot.py` now forces the nickname "BADbot" on startup.

### Changed
- **Security Guardrails**: `bad_bot.py` now implements Strict Identity Lock (Impersonation) and Channel Lock (`antigravity-vm`) for the Test Bot.
- **Bot Identity**: Renamed "BAD-Bridge-Bot" to "BADbot" in `BRIDGE_MANUAL.md`, `heartbeat.json`, and on the Discord Developer Portal.
### Added
- **Dockerized Ticket Assistant**: Created `Dockerfile` and `docker-compose.yml` for the bot.
- **Service Security**: Configured systemd `bad-ticket-bot.service` on the VM for robust reliability.
- **Bot Fix**: Resolved port conflict by moving Ticket Assistant to port 45679.
- **Run Script**: Standardized `start_docker.sh` for production deployment.
