import os


def history_exists(history_path):
    return os.path.exists(history_path)


def model_exists(model_path):
    return os.path.exists(model_path)


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)