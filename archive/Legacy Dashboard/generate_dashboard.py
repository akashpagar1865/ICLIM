import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from dashboard_utils import load_snapshot
from log_classifier import load_or_train_model, classify_logs

#Charts Function
def generate_charts(df, outdir="dashboard"):
    os.makedirs(outdir, exist_ok=True)

    charts = {
        "cpu": "CPU Usage %",
        "mem": "Memory Usage %",
        "disk": "Disk Usage %"
    }

    for metric, title in charts.items():
        plt.figure(figsize=(10,4))
        plt.plot(df["timestamp"], df[metric])
        plt.title(title)
        plt.ylabel("%")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{outdir}/{metric}_history.png")
        plt.close()

    print("[INFO] Metric charts generated")

import os
import json

# Function for Alerts from classifier output
def generate_alerts(outdir="dashboard"):
    model = load_or_train_model()
    log_file = "data/centos_logs.txt"

    # CI-safe guard
    if not os.path.exists(log_file):
        print("[WARN] centos_logs.txt not found. Skipping alert generation.")
        alerts = {
            "security": 0,
            "error": 0
        }
    else:
        df = classify_logs(model, log_file)
        alerts = {
            "security": int((df["label"] == "security").sum()),
            "error": int((df["label"] == "error").sum())
        }

    os.makedirs(outdir, exist_ok=True)
    with open(f"{outdir}/alerts.json", "w") as f:
        json.dump(alerts, f, indent=2)

    print("[INFO] Alert summary generated")


#Generate static HTML dashboard
def generate_html(outdir="dashboard"):
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>ICLIM Dashboard</title>
    <style>
        body {
            font-family: Arial;
            background-color: #0e1117;
            color: #e6edf3;
            padding: 20px;
        }
        img {
            width: 90%;
            margin-bottom: 30px;
            border: 1px solid #30363d;
        }
        .alert {
            padding: 12px;
            background-color: #3b1d1d;
            border-left: 5px solid #f85149;
            margin-bottom: 20px;
        }
        h2 {
            border-bottom: 1px solid #30363d;
        }
    </style>
</head>
<body>

<h1>ICLIM — Infrastructure Monitoring Dashboard</h1>

<div id="alerts"></div>

<script>
fetch("alerts.json")
  .then(res => res.json())
  .then(data => {
    if (data.security > 0) {
        document.getElementById("alerts").innerHTML +=
        `<div class="alert">Security alerts detected: ${data.security}</div>`;
    }
    if (data.error > 0) {
        document.getElementById("alerts").innerHTML +=
        `<div class="alert">System errors detected: ${data.error}</div>`;
    }
  });
</script>

<h2>CPU Usage</h2>
<img src="cpu_history.png">

<h2>Memory Usage</h2>
<img src="mem_history.png">

<h2>Disk Usage</h2>
<img src="disk_history.png">

</body>
</html>
"""
    with open(f"{outdir}/index.html", "w") as f:
        f.write(html)

    print("[INFO] Dashboard HTML generated")

#Orchestrator (single command)
if __name__ == "__main__":
    df = load_snapshot()
    generate_charts(df)
    generate_alerts()
    generate_html()
    print("[DONE] Dashboard ready in /dashboard/")
