
# ICLIM — Intelligent Cloud-Infrastructure Linux Monitor

*A Python-based system monitoring agent built around Linux, Cloud, and AI-driven automation.*

=====================================================

                   +------------------+
                   |     Live Agent   |
                   +------------------+
                           |
                           |  CPU / MEM / DISK snapshots
                           v
                snapshot_history.jsonl
                           |
                           v
                  +--------------------+
                  |   Anomaly Training |
                  +--------------------+
                           |
                           |  model.pkl
                           v
               +--------------------------+
               | Realtime Anomaly Agent   |
               +--------------------------+

                           (Phase 2)
                           =========

                   +------------------+
                   |    Log Events    |
                   +------------------+
                           |
                           v
                clean_log_line()  →  TF-IDF → Logistic Regression
                           |
                           v
               +--------------------------+
               |   Log Classification     |
               |  (info / warning / error |
               |      / security)         |
               +--------------------------+
                           |
                           v
                  classification_summary

---

## Overview

ICLIM is a hands-on infrastructure learning project where I’m building a monitoring agent that collects system metrics, stores structured snapshots, and prepares data for cloud automation and AI-powered analysis.

The focus is on understanding how real-world sysadmin, cloud, and DevOps teams build monitoring, alerting, and lightweight automation.

This repo is updated iteratively as I progress through each milestone.

---

## Core Capabilities (Current + Upcoming)

### ✅ Completed

  * Python fundamentals (functions, data structures, modules)
  * File handling (text + JSON)
  * Structured system snapshots
  * Live metric collection using `psutil` (CPU, memory, disk)
  * JSON-based data pipeline foundation
  * Timestamped metric collection
  * Loaded and analyzed historical snapshots using pandas
  * AI-based anomaly detection using IsolationForest (model saved as `anomaly_model.pkl`)
  * Real-time anomaly detection using the trained AI model
  * Retraining pipeline that:
    * uses recent snapshots from `snapshot_history.jsonl`
    * safely skips invalid JSON lines
    * can exclude known anomalies from training
  * Log classification pipeline (TF-IDF + Logistic Regression) for INFO / WARNING / ERROR / SECURITY
  * Lightweight HTML dashboard

### 🚧 **In Progress**

* Packaging the agent for Linux (CentOS VM)

### 🧠 **Planned (Upcoming Milestones)**

* Deployment on Azure VM
* Automation via GitHub Actions

---

## 🛠 Tech Stack

Component          Tools
------------------ -------------------------------------
Language           Python
Metrics            psutil
Data Format        JSON / JSONL
AI/ML              scikit-learn (IsolationForest), future: TF-IDF
Analysis           pandas
Model Persistence  joblib
Dashboard          HTML + charts
Cloud Integration  Azure VM (planned)

---

## 📂 System Architecture

    ICLIM/
    │
    ├── Experiments/                  # Learning scripts & practice exercises
    │
    ├── live_snapshot_agent.py        # Basic real-time system metrics collector
    ├── snapshot_file_agent.py        # Creates & stores static snapshots
    ├── agents/history_logger.py      # Timestamped history builder
    ├── analysis/history_analysis.py  # pandas-based history analysis
    ├── analysis/anomaly_training.py  # Initial model training on history
    ├── agents/realtime_anomaly_agent.py  # Real-time AI anomaly detector
    ├── analysis/anomaly_retrain.py   # Retrains IsolationForest model from history
    │
    ├── data/snapshot_history.jsonl   # Growing history of snapshots
    ├── models/anomaly_model.pkl      # Saved IsolationForest model
    ├── anomaly_events.jsonl          # Logged anomaly events (if present)
    ├── known_anomalies.jsonl         # Optional: timestamps to exclude from training
    ├── analysis/log_classifier.py    # data/centos_logs.txt
    ├── analysis/generate_dashboard.py # Orchestrates the entire dashboard build process
    ├── analysis/dashboard_utils.py   # Loads snapshot data and prepares it for visualization
    ├── dashboard/index.html          # Final static dashboard output
    ├──
    ├── README.md                     # Project documentation
    └── .gitignore                    # Git exclusions (.venv, logs, etc.)

---

## ▶️ Running the Current Agent - Execution Flow

Clone the repo and enter the project folder:

```bash
git clone https://github.com/akashpagar1865/ICLIM.git
cd ICLIM
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate      # Windows
# source .venv/bin/activate   # Linux/macOS
```

Install required packages:

    pip install psutil pandas scikit-learn joblib

Run the basic live snapshot agent:

    python live_snapshot_agent.py

Run the AI-based real-time anomaly detector:

    python lesson8_realtime_anomaly.py

After collecting enough history, retrain the model on recent data:

    python retrain_anomaly_model.py


You will see live system metrics printed and saved to a JSON file, including:

* CPU usage (%)
* Memory usage (%)
* Disk usage (%)
* Server identifier

---

## 🎯 Learning Goals

This project supports my transition into:

* Linux system administration
* Cloud infrastructure operations
* Automation and monitoring
* DevOps/SRE-style tooling
* AI-assisted observability

Each component is added incrementally, with commits and documentation reflecting real engineering workflow.

---

## 📈 Roadmap Overview

```
[✓] Python fundamentals
[✓] JSON snapshot pipeline
[✓] Live metric collector
[✓] Timestamped data collection
[✓] Historical dataset builder
[✓] AI anomaly detector
[✓] Real-time anomaly detection + retraining pipeline
[✓] NLP log classifier
[ ] HTML dashboard
[ ] Linux deployment
[ ] Cloud deployment (Azure)
[ ] CI/CD automation
```

---

## 🤝 Contributions & Feedback

This is a learning-first project, but feedback, suggestions, or guidance from the community are welcome — especially around Linux automation, Azure deployment, and ML-based observability.

---

## 📬 Contact

If you’d like to connect professionally or discuss cloud/infra engineering roles:

**LinkedIn:** [https://www.linkedin.com/in/akash-pagar-7303971a2/](https://www.linkedin.com/in/akash-pagar-7303971a2/)
**GitHub:** [https://github.com/akashpagar1865](https://github.com/akashpagar1865)

---

