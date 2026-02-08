# Protocol: Beginning of Session (PHASE-01)

**Trigger:** Start of any work session.

## 1. Environment Synchronization
- [ ] **Establish Clean State**: ensuring no uncommitted changes from previous sessions.
    ```bash
    git status
    ```
- [ ] **Pull Latest Changes**: Sync with remote repository.
    ```bash
    git pull
    ```
- [ ] **Sync Playbook**: ensure operating procedures are up to date.
    ```bash
    ./BAD/scripts/sync_playbook.sh
    ```

## 2. Context Rehydration
- [ ] **Review Recent History**: Check `task.md` and recent conversation summaries.
- [ ] **Identify Blockers**: Review any open issues or "blocked" items.

## 3. Scope Definition
- [ ] **Set Session Goal**: Define clearly what success looks like for *this* session.
- [ ] **Update Task List**: Ensure `task.md` reflects the current focus.
