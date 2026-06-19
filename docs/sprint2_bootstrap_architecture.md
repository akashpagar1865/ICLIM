# Sprint 2 – Bootstrap Architecture

## Objective

The goal of Sprint 2 was to make ICLIM capable of starting successfully on a fresh deployment without requiring manual preparation steps.

---

## Problem Identified

During testing of the new Git workflow (`main → dev → feature/*`), a deployment failure was discovered.

The monitoring agent depended on a trained anomaly detection model:

```text
snapshot_history.jsonl
↓
anomaly_training.py
↓
anomaly_model.pkl
↓
realtime_anomaly_agent.py
```

If either the history file or model file was missing:

```text
History Missing
↓
Training Fails
↓
Model Missing
↓
Agent Fails
```

This issue became visible when testing from development branches because generated artifacts were no longer present.

---

## Root Cause

The monitoring platform assumed that required artifacts already existed.

Required startup dependencies:

* snapshot_history.jsonl
* anomaly_model.pkl

No validation or recovery process existed.

---

## Solution

A bootstrap layer was introduced before model loading.

The bootstrap process validates required resources and automatically creates missing dependencies.

### Startup Flow

```text
Load Config
↓
Create Directories
↓
History Exists?
│
├─ Yes
│
└─ No
     ↓
     Bootstrap History
     ↓
     Collect 30 Real Snapshots

Model Exists?
│
├─ Yes
│
└─ No
     ↓
     Bootstrap Model
     ↓
     Train Isolation Forest

Load Model
↓
Start Monitoring
```

---

## Components Added

### bootstrap.py

Responsibilities:

* Validate startup dependencies
* Generate bootstrap history
* Trigger model training
* Prepare platform for monitoring

Key functions:

```python
history_exists()
model_exists()
ensure_directory()

bootstrap_history()
bootstrap_model()
```

---

### anomaly_training.py Refactor

The training script was refactored into a reusable function:

```python
train_from_history()
```

Benefits:

* Reusable by bootstrap process
* Avoids duplicated training logic
* Supports both manual and automatic training

---

## Bootstrap History Generation

When no historical data exists:

1. Collect 30 real system snapshots
2. Store snapshots in `snapshot_history.jsonl`
3. Display collection progress
4. Use collected data for model training

Example:

```text
[1/30] Snapshot collected
...
[30/30] Snapshot collected
```

---

## Testing Performed

### Test 1

Existing history and model:

```text
History Exists = True
Model Exists = True
```

Result:

```text
Monitoring started successfully
```

PASS

---

### Test 2

History exists, model removed:

```text
History Exists = True
Model Exists = False
```

Result:

```text
Model automatically retrained
Monitoring started successfully
```

PASS

---

### Test 3

History removed and model removed:

```text
History Exists = False
Model Exists = False
```

Result:

```text
Bootstrap history generated
Model automatically trained
Monitoring started successfully
```

PASS

---

## Key Learning

A monitoring platform should not assume that runtime artifacts already exist.

Startup validation and recovery mechanisms improve deployment reliability and reduce manual operational work.

---

## Interview Talking Points

* Identified a deployment dependency issue during testing.
* Introduced startup validation through a bootstrap layer.
* Automated history generation and model creation.
* Refactored training logic into reusable functions.
* Tested multiple deployment scenarios to verify recovery behavior.
* Improved reliability without introducing additional infrastructure or orchestration tools.

## Technical Debt Identified

During Linux validation, legacy references to
data/snapshot_history.jsonl were discovered in
dashboard utilities.

Current monitoring pipeline uses:

logs/snapshot_history.jsonl
logs/anomaly_events.jsonl

Future cleanup task:
standardize all components on logs/ storage paths.