def create_snapshot(cpu, mem, disk, name):
    snapshot = {
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "server": name
    }
    return snapshot

def print_snapshot(snapshot):
    print("Snapshot for:", snapshot["server"])
    print(snapshot)

snap = create_snapshot(30, 50, 60, "Linux VM")
print_snapshot(snap)

