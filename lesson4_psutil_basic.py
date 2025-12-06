import psutil

#Read CPU usage
cpu = psutil.cpu_percent(interval=1)

#Read memory usage
mem = psutil.virtual_memory().percent

#Read disk usage
disk = psutil.disk_usage("c:\\").percent

print("CPU Usage:", cpu)
print("Memory usgae:", mem)
print("Disk usgae:", disk)


