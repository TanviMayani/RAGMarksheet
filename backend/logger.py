import logging
import sys
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("marksheet_ai")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler
file_handler = logging.FileHandler("logs/app.log")
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
