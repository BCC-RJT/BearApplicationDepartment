# Protocol: End of Session (PHASE-02)

**Trigger:** Conclusion of work session or hand-off.

## 1. Artifact Verification
- [ ] **Code Review**: Ensure all changes follow standards.
- [ ] **Test Verification**: Confirm all critical paths are working.

## 2. State Persistence
- [ ] **Update Documentation**: `task.md`, `implementation_plan.md`, etc.
- [ ] **Commit Changes**:
    ```bash
    git add .
    git commit -m "feat: [Description of work done]"
    git push
    ```

## 3. Handover Note
- [ ] **Draft Summary**: Write a brief note in `task.md` or chat about what was accomplished.
- [ ] **Next Steps**: Clearly list the immediate next actions for the following session.
