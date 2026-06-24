# ICLIM Technical Debt Register

# Technical Debt Identified post Sprint 1.

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

---

## Technical Debt Identified post Sprint 2.

During Linux validation, legacy references to
data/snapshot_history.jsonl were discovered in
dashboard utilities.

Current monitoring pipeline uses:

logs/snapshot_history.jsonl
logs/anomaly_events.jsonl

Future cleanup task:
standardize all components on logs/ storage paths.

# Technical Debt identified after second review of artifacts
Future Enhancement:
Periodic model retraining using historical snapshots.

Current Status:
Not required for current architecture.

Reason:
Bootstrap architecture already guarantees model availability.
Retraining will be revisited after Docker, Terraform, and Grafana.