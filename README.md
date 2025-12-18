
# ICLIM — Intelligent Cloud-Infrastructure Linux Monitor

*A Python-based system monitoring agent built around Linux, Cloud, and AI-driven automation.*

=====================================================

            ┌──────────────────────────┐
            │        Linux VM           │
            │ (Local / Azure / CentOS)  │
            └─────────────┬────────────┘
                        │
                        │  system metrics + logs
                        │
            ┌─────────────▼────────────┐
            │        Live Agent         │
            │  (CPU / MEM / DISK)       │
            └─────────────┬────────────┘
                        │
                        │  periodic snapshots
                        ▼
                snapshot_history.jsonl
                        │
                        │
            ┌─────────────▼────────────┐
            │     Anomaly Training      │
            │ (baseline behavior model) │
            └─────────────┬────────────┘
                        │
                        │  anomaly_model.pkl
                        ▼
            ┌─────────────▼────────────┐
            │  Realtime Anomaly Agent   │
            │ (detects deviations)     │
            └─────────────┬────────────┘
                        │
                        │  anomaly events
                        ▼
                anomaly_events.jsonl


            =========================================================
                            PHASE 2 — LOG INTELLIGENCE
            =========================================================

            ┌──────────────────────────┐
            │      System Logs          │
            │  (/var/log/messages,     │
            │   sshd, systemd, etc.)   │
            └─────────────┬────────────┘
                        │
                        │
                        ▼
                    clean_log_line()
            (timestamp / host / PID removal)
                        │
                        │
                        ▼
                TF-IDF Vectorization
                        │
                        │
                        ▼
            Logistic Regression Model
                        │
                        │
                        ▼
            ┌──────────────────────────┐
            │   Log Classification      │
            │  info / warning / error   │
            │        / security         │
            └─────────────┬────────────┘
                        │
                        │  summaries + alerts
                        ▼
                classification_summary


            =========================================================
                            PHASE 3 — VISUALIZATION
            =========================================================

            ┌──────────────────────────┐
            │   Dashboard Generator     │
            │ (generate_dashboard.py)  │
            └─────────────┬────────────┘
                        │
                        │  matplotlib charts
                        ▼
                PNG Charts (CPU, MEM,
                    DISK, anomalies)
                        │
                        │
                        ▼
            ┌──────────────────────────┐
            │    HTML Dashboard         │
            │     index.html            │
            │  (static, portable)      │
            └─────────────┬────────────┘
                        │
                        │
                        ▼
                    GitHub Pages /
                    Local Browser


            =========================================================
                        PHASE 4 — AUTOMATION & CLOUD
            =========================================================

            ┌──────────────────────────┐
            │     GitHub Actions        │
            │ (scheduled workflows)    │
            └─────────────┬────────────┘
                        │
                        │  run agents + analysis
                        ▼
                    Artifacts / Reports
                        │
                        │
                        ▼
            ┌──────────────────────────┐
            │        Azure Cloud        │
            │  Linux VM + Blob Storage │
            └──────────────────────────┘


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
  * Lightweight HTML dashboard with .png charts

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
AI/ML              scikit-learn (IsolationForest), TF-IDF
Analysis           pandas
Model Persistence  joblib
Dashboard          HTML + PNG charts
Cloud Integration  Azure VM (planned)

---

## 📂 System Architecture

    ICLIM/
    ├── agents/
    │   ├── live_agent.py
    │   ├── snapshot_agent.py
    │   ├── realtime_anomaly_agent.py
    │   └── history_logger.py
    │
    ├── analysis/
    │   ├── log_classifier.py
    │   ├── anomaly_training.py
    │   ├── anomaly_retrain.py
    │   ├── history_analysis.py
    │   ├── dashboard_utils.py
    │   └── generate_dashboard.py
    │
    ├── dashboard/
    │   ├── index.html
    │   └── charts/
    │
    ├── data/
    │   ├── snapshot_history.jsonl
    │   ├── anomaly_events.jsonl
    │   ├── centos_logs.txt
    │   └── simulated_logs.txt     
    │
    ├── models/
    │   ├── log_classifier.pkl
    │   └── anomaly_model.pkl
    │
    ├── requirements.txt
    ├── README.md
    └── .gitignore


---

## ▶️ Running the Current Agent - Execution Flow

Clone the repo and enter the project folder:

```bash
git clone https://github.com/akashpagar1865/ICLIM.git
cd ICLIM
```

# How to Run (Local)

1. Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  (Linux/Mac)
   .\.venv\Scripts\activate   (Windows)

2. Install dependencies
   pip install -r requirements.txt

3. Run agents
   python agents/snapshot_agent.py

4. Generate dashboard
   python analysis/generate_dashboard.py

Output:
- dashboard/index.html

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
[✓] HTML dashboard
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

