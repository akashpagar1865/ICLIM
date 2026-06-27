import psutil
import json
import time
from datetime import datetime
import joblib
import warnings
import os
from utils.config_loader import load_config
from utils.logger import setup_logger
from analysis.bootstrap import (
    history_exists,
    model_exists,
    bootstrap_history,
    bootstrap_model
)
logger = setup_logger()

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
def load_model(path):
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
def log_anomaly(snapshot, filename):
    with open(filename, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

#Function to update live snapshot into history
def append_snapshot_to_history(snapshot, filename):
    with open(filename, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

#Main loop — real-time anomaly detection
def main():
    config = load_config()
    logger.info(f"Configuration loaded: {config}")

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    MODEL_PATH = os.path.join(BASE_DIR, config["paths"]["model_path"])
    LOG_DIR = os.path.join(BASE_DIR, config["paths"]["logs_dir"])
    HISTORY_FILE = os.path.join(BASE_DIR, config["paths"]["history_file"])
    ANOMALY_FILE = os.path.join(BASE_DIR, config["paths"]["anomaly_file"])

    # ensure logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    logger.info("Real-time anomaly detector started")

    # Bootstrap startup validation

    if not history_exists(HISTORY_FILE):

        logger.warning(
            "History file missing. Starting bootstrap history generation."
        )

        import socket

        if config["app"]["hostname"] == "auto":
            HOSTNAME = socket.gethostname()
        else:
            HOSTNAME = config["app"]["hostname"]

        bootstrap_history(
            HISTORY_FILE,
            HOSTNAME
        )

    if not model_exists(MODEL_PATH):

        logger.warning(
            "Model file missing. Starting bootstrap model training."
        )

        bootstrap_model(HISTORY_FILE, MODEL_PATH)

    try:
        model = load_model(MODEL_PATH)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Model loading failed: {str(e)}")
        return

    interval = config["app"]["interval"]
    first_run = True
    while True:
        try:
            import socket
            if config["app"]["hostname"] == "auto":
                HOSTNAME = socket.gethostname()
            else:
                HOSTNAME = config["app"]["hostname"]

            snap = get_live_snapshot(HOSTNAME)

            anomaly = is_anomaly(model, snap)

            append_snapshot_to_history(snap, HISTORY_FILE)
            logger.info(f"Snapshot stored | CPU={snap['cpu']} MEM={snap['mem']} DISK={snap['disk']}")

            if first_run:
                logger.info(f"First snapshot collected: CPU={snap['cpu']} MEM={snap['mem']} DISK={snap['disk']}")
                first_run = False

            if anomaly:
                logger.warning(
                    f"ANOMALY DETECTED | CPU={snap['cpu']} MEM={snap['mem']} DISK={snap['disk']}"
                )
                log_anomaly(snap, ANOMALY_FILE)
            else:
                logger.info(
                    f"System Normal | CPU={snap['cpu']} MEM={snap['mem']} DISK={snap['disk']}"
                )

            time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break

        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        

if __name__ == "__main__":
    main()