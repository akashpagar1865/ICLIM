import os
import json
import psutil
from datetime import datetime
from analysis.anomaly_training import train_from_history
from utils.logger import setup_logger

logger = setup_logger()


def history_exists(history_path):

    logger.info(
        f"Checking history path: {os.path.abspath(history_path)}"
    )

    exists = os.path.exists(history_path)

    logger.info(
        f"History file exists: {exists}"
    )

    return exists


def model_exists(model_path):

    logger.info(
        f"Checking model path: {os.path.abspath(model_path)}"
    )

    exists = os.path.exists(model_path)

    logger.info(
        f"Model file exists: {exists}"
    )

    return exists

# Bootstrap model creation
#
# Purpose:
# Fresh deployments may not contain a trained model.
#
# Instead of duplicating training logic here,
# we reuse the centralized training pipeline
# from anomaly_training.py.
#
# Flow:
# History File
# ↓
# Train Model
# ↓
# Save anomaly_model.pkl

def bootstrap_model(history_file):

    print(
        "\nModel file missing. Training initial model...\n"
    )

    train_from_history(history_file)

    logger.info(
        "Initial model training completed."
    )

    print(
        "\nInitial model training completed.\n"
    )


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)
    logger.info(f"Directory ensured: {path}")

# Snapshot Collection Helpers
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

# Collect current system metrics.
#
# These metrics represent the current
# health state of the machine and are
# used for both history generation and
# realtime monitoring.

def get_live_snapshot(hostname):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    return create_snapshot(cpu, mem, disk, hostname)


# Bootstrap history generation
#
# Purpose:
# A brand-new deployment has no historical data.
#
# To create an initial baseline, collect
# real CPU, memory and disk metrics from
# the current system.
#
# The collected history is later used to
# train the first anomaly detection model.

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