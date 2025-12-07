
# ICLIM — Intelligent Cloud-Integrated Linux Monitor

*A Python-based system monitoring agent built around Linux, Cloud, and AI-driven automation.*

---

## Overview

ICLIM is a hands-on infrastructure learning project where I’m building a monitoring agent that collects system metrics, stores structured snapshots, and prepares data for cloud automation and AI-powered analysis.

The focus is on understanding how real-world sysadmin, cloud, and DevOps teams build monitoring, alerting, and lightweight automation.

This repo is updated iteratively as I progress through each milestone.

---

## Features (Current + Upcoming)

### ✅ **Completed**

* Python fundamentals (functions, data structures, modules)
* File handling (text + JSON)
* Structured system snapshots
* Live metric collection using `psutil` (CPU, memory, disk)
* JSON-based data pipeline foundation
* Timestamped metric collection
* Loaded and analyzed historical snapshots using pandas

### 🚧 **In Progress**

* AI-based anomaly detection (IsolationForest)

### 🧠 **Planned (Upcoming Milestones)**

* AI-based anomaly detection (IsolationForest)
* Basic NLP for log classification
* Lightweight HTML dashboard
* Packaging the agent for Linux (CentOS VM)
* Deployment on Azure VM
* Automation via GitHub Actions

---

## 🛠 Tech Stack

| Component            | Tools                |
| -------------------- | -------------------- |
| Language             | Python               |
| Metrics              | psutil               |
| Data Format          | JSON                 |
| AI/ML (Upcoming)     | scikit-learn, TF-IDF |
| Analysis (Upcoming)  | pandas               |
| Dashboard (Upcoming) | HTML + charts        |
| Cloud Integration    | Azure VM (planned)   |

---

## 📂 Project Structure

```
ICLIM/
│
├── Experiments/              # Learning scripts & practice exercises
│
├── live_snapshot_agent.py    # Collects real-time system metrics
├── snapshot_file_agent.py    # Creates & stores static snapshots
│
├── README.md                 # Project documentation
└── .gitignore                # Git exclusions (.venv, logs, etc.)
```

---

## ▶️ Running the Current Agent

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

```bash
pip install psutil
```

Run the live snapshot agent:

```bash
python live_snapshot_agent.py
```

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
[✓ ] Historical dataset builder
[ ] AI anomaly detector
[ ] NLP log classifier
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

