import yaml
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def apply_environment_overrides(config):
    """
    Override selected configuration values using environment variables.
    YAML remains the default configuration source.
    """

    interval = os.getenv("INTERVAL")
    hostname = os.getenv("HOSTNAME")
    log_level = os.getenv("LOG_LEVEL")

    if interval:
        config["app"]["interval"] = int(interval)

    if hostname:
        config["app"]["hostname"] = hostname

    if log_level:
        config["logging"]["level"] = log_level

    return config

def load_config():
    config_path = os.path.join(BASE_DIR, "config", "config.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    config = apply_environment_overrides(config)

    return config