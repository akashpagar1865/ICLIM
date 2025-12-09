import psutil

#Function for creating snapshot
def create_snapshot(cpu, mem, disk, name):
    return {
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "server": name
    }

#Function for creating getting live metrics
def get_live_metrics(server_name):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\").percent 
    snap = create_snapshot(cpu, mem, disk, server_name)
    return snap


snapshot = get_live_metrics("Windows_host")
print("Live snapshot", snapshot)