import os
import json
import psutil
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger()


def history_exists(history_path):
    exists = os.path.exists(history_path)
    logger.info(f"History file exists: {exists}")
    return exists


def model_exists(model_path):
    exists = os.path.exists(model_path)
    logger.info(f"Model file exists: {exists}")
    return exists


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)
    logger.info(f"Directory ensured: {path}")

# Helper Functions
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_snapshot(cpu, mem, disk, hostname):
    return {
        "timestamp": get_timestamp(),
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "server": hostname
    }


def get_live_snapshot(hostname):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    return create_snapshot(cpu, mem, disk, hostname)


# Bootstrap Function
def bootstrap_history(history_file, hostname, samples=30):

    logger.info(f"Bootstrap history generation started. Target samples: {samples}")

    print("\nBootstrap history generation started...\n")

    with open(history_file, "w") as f:

        for i in range(samples):

            snapshot = get_live_snapshot(hostname)

            f.write(json.dumps(snapshot) + "\n")

            logger.info(
                f"Bootstrap progress: {i + 1}/{samples}"
            )

            print(
                f"[{i + 1}/{samples}] Snapshot collected"
            )

    logger.info(f"Bootstrap history generation completed. Collected {samples} samples.")

    print("\nBootstrap history completed.\n")