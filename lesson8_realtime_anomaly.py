import psutil
import json
import time
from datetime import datetime
import joblib
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

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
def load_model(path="anomaly_model.pkl"):
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
def log_anomaly(snapshot, filename = "anomaly_events.jsonl"):
    with open(filename, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

#Main loop — real-time anomaly detection
def main():
    model = load_model("anomaly_model.pkl")
    print("Real-time anomaly detector started (CTRL+C to stop)\n")

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

#Function to update live snapshot into history
HISTORY_FILE = "snapshot_history.jsonl"

def append_snapshot_to_history(snapshot, filename=HISTORY_FILE):
    #Append every live snapshot (normal or anomaly) to history file.
    with open(filename, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


if __name__ == "__main__":
    main()




