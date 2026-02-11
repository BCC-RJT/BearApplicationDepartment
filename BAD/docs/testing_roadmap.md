# Future Testing Roadmap

## Progressive Testing Framework
**Status**: Proposed
**Description**: A testing infrastructure where tests are executed in a strict sequence. Each step constitutes a "gate" that must be passed before the next step is attempted.

### Concept
Instead of running all tests in parallel or random order, we define a **Process Workflow** that mirrors the actual lifecycle of the feature.

1.  **Gate 1**: Unit Logic (Brain)
    -   *Script*: `tests/verify_ticket_flow.py`
    -   *Goal*: Ensure the LLM logic correctly identifies intent, urgency, and iterative updates.
    -   *Condition*: Must pass 100% to proceed.

2.  **Gate 2**: Integration (Discord Controls)
    -   *Script*: `tests/test_greeting.py` (and expanded view tests)
    -   *Goal*: Ensure UI components (Buttons, Modals) render and trigger correct callbacks.
    -   *Condition*: Must pass Mocked Discord interactions.

3.  **Gate 3**: End-to-End (Simulation)
    -   *Script*: `tests/simulate_ticket_assistant.py` (Full Bot Spin-up)
    -   *Goal*: valid full session connectivity and state management.

4.  **Gate 4: Deployment & Verification**
    -   *Action*: **RESTART BOT PROCESS** (`py src/bridge/tickets_assistant.py`)
    -   *Goal*: Ensure running service reflects the latest code.
    -   *Condition*: Old process must be terminated and new process must be running > 10s without error.
    -   *Manual Verification*: User interacts with the *real* bot in Discord only after this step.

