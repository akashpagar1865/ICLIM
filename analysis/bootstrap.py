import os
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