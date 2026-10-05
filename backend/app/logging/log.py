import logging

from app.config import log_filepath

logger = logging.getLogger("websocket")
logger.setLevel(logging.DEBUG)

# write logs to file
file_handler = logging.FileHandler(log_filepath)

# log format
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
