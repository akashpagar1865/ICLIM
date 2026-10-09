import logging
import os

class ICLIMFormatter(logging.Formatter):

    def format(self, record):
        original_level = record.levelname

        if record.levelno == logging.INFO:
            record.levelname = "SYSTEM"

        message = super().format(record)

        record.levelname = original_level

        return message

def setup_logger():
    log_dir = "logs"
    log_file = "iclim.log"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger("ICLIM")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path)
        console_handler = logging.StreamHandler()

        formatter = ICLIMFormatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger