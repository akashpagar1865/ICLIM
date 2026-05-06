import yaml
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def load_config():
    config_path = os.path.join(BASE_DIR, "config", "config.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config