# ICLIM Technical Debt Register

## High Priority

### Startup Dependency

Current monitoring agent requires anomaly_model.pkl to exist.

Impact:

Fresh deployments fail.

Planned Fix:

Sprint 2 Bootstrap Logic.

---

## Medium Priority

### Multiple Metric Collection Scripts

Review:

- live_agent.py
- history_logger.py
- snapshot_agent.py

Determine:

- Active
- Legacy
- Archive Candidates

---

## Low Priority

### Generated Artifacts Review

Review whether the following should remain in Git:

- Dashboard PNG files
- Sample JSONL data
- Trained models