# Testing Ethos & Deployment Protocol

## Core Principle
**"Code changes are not real until they are running."**

It is a fundamental requirement of our testing process that any changes to bot logic, views, or persistent components MUST be accompanied by a restart of the service hosting them. Automated tests verify logic; deployment verifies reality.

## Mandatory Workflow

1.  **Develop**: Implement changes and run unit tests.
2.  **Verify Logic**: Ensure `tests/` pass.
3.  **DEPLOY (Restart)**:
    -   Terminate the running bot process.
    -   Start a fresh instance: `py src/bridge/tickets_assistant.py`
    -   Wait for "Online" confirmation.
4.  **Verify Reality**:
    -   Perform the user action (e.g., Click the button) interacting with the *newly started* bot.
    -   Confirm the outcome in the real environment (Discord).

## Failure to Follow
Failure to restart the bot before verification leads to:
-   False positives in testing.
-   User confusion/frustration.
-   Loss of data (e.g., ticket deletion instead of archiving).

## Department Policy
All agents and engineers working on `BearApplicationDepartment` must adhere to this protocol. "It works on my machine" is not enough; "It works in the running process" is the standard.
