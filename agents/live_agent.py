import json
import psutil  

#Function to create snapshot by adding structured data (Dictionary)
def create_snapshot(cpu, mem, disk, name):
    return{
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "server": name
    }

#Function to create a live snapshot agent by pulling values using psutil and creating snapshot using those values
def get_live_snapshot(server_name):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent  # change to "/" on Linux later
    snapshot = create_snapshot(cpu, mem, disk, server_name) 
    return snapshot

#Function for saving snapshot to a file
def save_snapshot(snapshot, filename):
    with open(filename, "w") as f:
        json.dump(snapshot, f, indent=2)

# --- main logic ---
snap = get_live_snapshot("Windows_Host")
save_snapshot(snap, "latest_live_snapshot.json")

with open("latest_live_snapshot.json", "r") as f:
    loaded = json.load(f)

print("Loaded live snapshot", loaded)