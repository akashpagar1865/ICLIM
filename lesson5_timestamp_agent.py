import json
import psutil
import time
from datetime import datetime

#Function to get current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#Function to create snapshot
def create_snapshot(cpu, mem, disk, name):
    return{
        "timestamp": get_timestamp(),
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "server": name
    }

#Function to create live snapshot
def get_live_snapshot(server_name):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    return create_snapshot(cpu, mem, disk, server_name)

#Function to apend snapshot to history file
def apend_snapshot (snapshot, filename):
    with open(filename, "a")as f:
        f.write(json.dumps(snapshot) + "\n")

#Main monitoring loop
history_file = "snapshot_history.jsonl"

print("Starting monitoring... (Press ctr+C to stop) \n")

while True:
    snap = get_live_snapshot("Windows_Host")
    apend_snapshot(snap, history_file)

    print(snap) #Show live output
    time.sleep(5) #wait 5 seconds

