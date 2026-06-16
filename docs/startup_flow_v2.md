ICLIM Startup Flow Review (Sprint 1)

Purpose

This document describes:

# Current startup process
# Startup failure scenarios
# Root cause analysis
# Target startup architecture

# Current Startup Process:

  * Current runtime entry point:

        python -m agents.realtime_anomaly_agent

  * Current startup sequence:

        Load Configuration
        ↓
        Load Trained Model
        ↓
        Start Monitoring Loop
        ↓
        Collect Metrics
        ↓
        Append Snapshot History
        ↓
        Detect Anomalies
        ↓
        Write Events
        Startup Dependencies

  * Required:

        config/config.yaml
        models/anomaly_model.pkl

  * Automatically Created:

        logs/
        snapshot_history.jsonl
        anomaly_events.jsonl

-------------------------------------------------------------------------------------------------------------------

# Startup Failure Scenario

  * Fresh Deployment:

        Clone Repository
        ↓
        Start realtime_anomaly_agent.py
        ↓
        Model Missing
        ↓
        Model Load Failure
        ↓
        Agent Exits

   * Result:

        Monitoring does not start.

-------------------------------------------------------------------------------------------------------------------

# Root Cause Analysis

    The realtime monitoring agent assumes:

    anomaly_model.pkl

    already exists.

    This assumption is true on existing environments but false on new deployments.

   * Discovery History

        Initial deployments succeeded because:

        anomaly_model.pkl

        was stored in the repository.

        After generated artifacts were removed from Git tracking:

        models/*.pkl

        the startup dependency became visible.

-------------------------------------------------------------------------------------------------------------------

# Desired Startup Flow

    Load Config
    ↓
    Create Directories
    ↓
    Check Model
    ↓
    Model Exists?
    │
    ├── Yes
    │     ↓
    │   Start Monitoring
    │
    └── No
        ↓
    Check History
        ↓
    History Exists?
        │
        ├── Yes
        │     ↓
        │   Train Model
        │
        └── No
                ↓
        Generate Bootstrap History
                ↓
            Train Model
                ↓
        Start Monitoring

-------------------------------------------------------------------------------------------------------------------