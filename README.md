
# ICLIM — Intelligent Cloud-Linux Infrastructure Monitor

*ICLIM is a Python-based system and log monitoring project built to reflect real-world Cloud/SRE
engineering practices — including Azure deployment, systemd services, CI/CD automation, and anomaly detection.*

## Overview

ICLIM is a self-built Linux system observability and automation project, designed to simulate real-world infrastructure monitoring workflows on cloud Linux VMs. It collects system metrics, detects anomalies using ML-based anomaly detection using IsolationForest, and produces visual insights — all built incrementally to mirror industry practices in SRE, monitoring, and cloud operations.

===================================================================================================================

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


===================================================================================================================

## Core Capabilities (Current + Upcoming)

## ☁️ Cloud Deployment

This project has been successfully deployed on an Azure Ubuntu VM, configured with secure access and persistent services using systemd. CI pipelines validate changes before deployment.

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
  * Deployed realtime anomaly agent as systemd service on CentOS
  * CI/CD pipeline validated using GitHub Actions (Python 3.9, Linux runner)
  * Deployed and managed as a **systemd service** on an **Azure Ubuntu VM**
  * CI validation with GitHub Actions
  * Persistent service startup across reboots
  * Real-world Linux troubleshooting (SELinux, service failures)
  * YAML-based configuration system
  * Structured logging with Python logging module
  * Linux log rotation using logrotate
  * Git branching workflow (dev + feature branches)
  * Runtime-configurable monitoring intervals

===================================================================================================================

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
Linux Services     Systemd
CI/CD Pipeline     GitHub Actions 
Cloud Integration  Azure VM

===================================================================================================================

## Operational Features

* systemd-managed Linux service
* Automatic service restart on failure
* Structured logging using Python logging module
* Log rotation using logrotate
* YAML-based runtime configuration
* Git branching workflow (dev + feature branches)
* Cross-environment deployment support (Windows/Linux/Azure)

===================================================================================================================

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
    │   └──log_classifier.pkl
    │
    ├── config/
    │   └── config.yaml
    │
    ├── utils/
    │   ├── config_loader.py
    │   └── logger.py
    │
    ├── requirements.txt
    ├── README.md
    └── .gitignore


===================================================================================================================

## 🚀 Getting Started - Run Instructions

This section explains how to run ICLIM locally or on a Linux VM.

✅ Prerequisites

Linux or macOS environment (tested on Ubuntu)

Python 3.9+

git

Basic familiarity with terminal commands

Note: The project is designed to mirror real Linux/cloud environments and works best on a Linux VM.

📦 Clone the Repository
git clone https://github.com/akashpagar1865/ICLIM.git
cd ICLIM

🐍 Create and Activate Virtual Environment
python3 -m venv .venv
source .venv/bin/activate   #For Linux environments
.venv\Scripts\Activate.ps1  #For Windows environments


Upgrade pip and install dependencies:
pip install --upgrade pip
pip install -r requirements.txt

Update config/config.yaml to customize intervals and runtime behavior.


🔁 Run Realtime Monitoring Agent (Continuous)

The realtime agent runs continuously and simulates a long-running production service.

python -m agents.realtime_anomaly_agent


Expected behavior:

Agent runs in a loop

Periodically collects metrics and logs

Designed to be managed via systemd in production setups


📊 Generate Dashboard

Once data is collected, generate the visualization dashboard:

python dashboard/generate_dashboard.py


This produces:

Graphs and summaries based on collected metrics

A simple visual representation of system behavior


⚙️ (Optional) Run as a systemd Service (Linux)

To simulate production-style deployment, the realtime agent can be configured as a systemd service.

High-level steps:

Create a systemd service file

Point it to the virtualenv Python binary

Enable and start the service

This allows the agent to:

Start automatically on boot

Recover after reboots or crashes

Detailed systemd configuration is documented separately.


🧪 Typical Execution Flow (Quick Reference)

For a first-time run:

Clone repo

Create virtual environment

Run realtime agent

Generate dashboard


🛑 Stopping the Agents

Press CTRL + C to stop agents running in the foreground

For systemd-managed services, use:

sudo systemctl stop iclim.service


===================================================================================================================

## 🎯 Learning Goals

This project supports my transition into:

* Linux system administration
* Cloud infrastructure operations
* Automation and monitoring
* DevOps/SRE-style tooling
* AI-assisted observability

Each component is added incrementally, with commits and documentation reflecting real engineering workflow.

👨‍💻 Why I Built This
This project was constructed to mirror infrastructure and observability work done in Cloud and SRE roles. Each commit reflects a real-world milestone: from Linux metric collection to failure handling and resilience.

===================================================================================================================

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
[✓] Linux deployment
[✓] Cloud deployment (Azure)
[✓] CI/CD automation
```

===================================================================================================================

## 🤝 Contributions & Feedback

This is a learning-first project, but feedback, suggestions, or guidance from the community are welcome — especially around Linux automation, Azure deployment, and ML-based observability.

---

## 📬 Contact

If you’d like to connect professionally or discuss cloud/infra engineering roles:

**LinkedIn:** [https://www.linkedin.com/in/akash-pagar-23316816b/](https://www.linkedin.com/in/akash-pagar-23316816b/)
**GitHub:** [https://github.com/akashpagar1865](https://github.com/akashpagar1865)

---

