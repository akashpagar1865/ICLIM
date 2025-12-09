# Function to create structured data (dictionary) from input metrics
def create_snapshot(cpu, mem, disk, name):
    return{
        "cpu" : cpu,
        "mem" : mem,
        "disk" : disk,
        "server" : name
    }

#Function to JSON snapshot file from above data

import json

def save_snapshot(snapshot, filename):
    with open(filename, "w") as f:
        json.dump(snapshot, f, indent=2)

#Inputing data from snapshot
snap = create_snapshot(30,40,30, "LinuxVM")

#Converting snapshot data to JSON
save_snapshot(snap, "Latest_snapshot.json")

#Reading latest data from JSON file

with open("Latest_snapshot.json", "r") as f:
    loaded = json.load(f)

#Printing parsed data
print("Latest snapshot:", loaded)