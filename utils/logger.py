import logging
import sys
from pathlib import Path

from config import LOGS_DIR

LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "skeleton.log"

_fmt = "%(asctime)s [%(levelname)s] %(message)s"
_datefmt = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "skeleton") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # File handler -- full debug output
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_fmt, _datefmt))

    # Console handler -- INFO and above only
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(_fmt, _datefmt))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
