# ICLIM — Intelligent Cloud-Integrated Linux Monitor

ICLIM is a hands-on learning project where I’m building a monitoring/automation agent using:

- Linux system metrics
- Python scripting
- Basic AI for anomaly detection (planned)
- Cloud + automation tooling (planned)

The goal is to simulate how real-world infra/DevOps teams monitor servers and build automation around them.

---

## ✅ Current Status

**Milestones completed:**

- [x] Python basics: variables, functions, dictionaries
- [x] File handling: write/read text & JSON
- [x] First snapshot agent: save structured system data to JSON
- [x] Live system metrics using `psutil` (CPU, memory, disk)

**Upcoming work:**

- [ ] Add timestamps to snapshots
- [ ] Collect snapshots over time into a history file
- [ ] Analyze data using pandas
- [ ] Add anomaly detection (IsolationForest)
- [ ] Basic log parsing + classification
- [ ] Simple dashboard for metrics/alerts
- [ ] Package the agent to run on Linux VM (CentOS)
- [ ] Deploy and automate using cloud tools (Azure + GitHub Actions)

---

## 🧪 How to run the current demo

Clone the repo and create a virtual environment:

```bash
git clone https://github.com/akashpagar1865/ICLIM.git
cd ICLIM

python -m venv .venv
.\.venv\Scripts\activate  # on Windows
# source .venv/bin/activate  # on Linux/macOS

#Install dependencies:

pip install psutil


#Run the live snapshot agent:

python live_snapshot_agent.py


#You should see a JSON-like snapshot printed with:

CPU usage

Memory usage

Disk usage

Server name

And a file latest_live_snapshot.json will be created in the project folder.

#🛠 Tech Stack (current + planned)

Language: Python

Monitoring: psutil

Data handling: JSON, later pandas

AI (planned): scikit-learn (IsolationForest, TF-IDF + classifier)

Dashboards (planned): simple HTML + charts

Cloud (planned): Azure VM + GitHub Actions for automation

#📌 Learning Focus

This project is part of my transition into:

Linux system administration

Cloud & infra automation

DevOps / SRE-style thinking

I’m building it iteratively and documenting progress through commits and occasional LinkedIn posts.