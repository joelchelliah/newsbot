import logging
import os

def get_logger():
    logger = logging.getLogger("NEWSBOT")

    log_level_from_env = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_from_env, logging.INFO)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
