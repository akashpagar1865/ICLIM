import psutil
import json
import time
from datetime import datetime
import joblib
import warnings
import os

warnings.filterwarnings("ignore", category=UserWarning)

# -------------------------------
# Base project paths (PRODUCTION SAFE)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "anomaly_model.pkl")
LOG_DIR = os.path.join(BASE_DIR, "logs")
HISTORY_FILE = os.path.join(LOG_DIR, "snapshot_history.jsonl")
ANOMALY_FILE = os.path.join(LOG_DIR, "anomaly_events.jsonl")

# ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

#Reuse helper functions ( getting timestamps, creating snapshot, getting live snapshot)
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_snapshot(cpu, mem, disk, name):
    return{
        "timestamp": get_timestamp(),
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "server": name
    }

def get_live_snapshot(server_name):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return create_snapshot(cpu,mem, disk, server_name)

#Load the trained model
def load_model(path=MODEL_PATH):
    model = joblib.load(path)
    return model

#Predict anomaly for a single snapshot
def is_anomaly(model, snapshot):
    features = [[
        snapshot["cpu"],
        snapshot["mem"],
        snapshot["disk"]
    ]]
    pred = model.predict(features)[0]  # 1 = normal, -1 = anomaly
    return pred == -1

#Optional: log anomalies to a file
def log_anomaly(snapshot, filename=ANOMALY_FILE):
    with open(filename, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

#Function to update live snapshot into history
def append_snapshot_to_history(snapshot, filename=HISTORY_FILE):
    with open(filename, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

#Main loop — real-time anomaly detection
def main():
    model = load_model()
    print("Real-time anomaly detector started (GitHub auto deploy test) (CTRL+C to stop)\n")

    interval = 5  #seconds

    while True:
        snap = get_live_snapshot("Windows_Host")
        anomaly = is_anomaly(model, snap)

        # always record snapshot in history
        append_snapshot_to_history(snap)

        if  anomaly:
            print(f"[ALERT] {snap['timestamp']}  CPU={snap['cpu']}  MEM={snap['mem']}  DISK={snap['disk']}")
            log_anomaly(snap)

        else: 
            print(f"[OK] {snap['timestamp']}  CPU={snap['cpu']}  MEM={snap['mem']}  DISK={snap['disk']}")

        time.sleep(interval)


if __name__ == "__main__":
    main()