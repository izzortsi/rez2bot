import logging
import os
import time
from datetime import datetime


LOGS_DATEFORMAT = "%j-%y_%H-%M-%S"

def strf_epoch(epochtime, fmt="%j-%y_%H-%M-%S"):
    """
    returns: string
    """

    """
    epochtime to string using datetime
    signature: def strf_epoch(epochtime, fmt="%j-%y_%H-%M-%S")

    Args:
        epochtime (float): epochtime as float in seconds
        fmt (string): format for the timestamp string
    Returns:
        string: stringfied epochtime: datetime.fromtimestamp(epochtime).strftime(fmt)
    """

    return datetime.fromtimestamp(epochtime).strftime(fmt)

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

if not os.path.exists("logs"):
    os.mkdir("logs")

logs_for_this_run = os.path.join("logs", strf_epoch(time.time()))

if not os.path.exists(logs_for_this_run):
    os.mkdir(logs_for_this_run)

formatter = logging.Formatter("%(asctime)s %(message)s")

init_time = time.time()

strf_init_time = strf_epoch(init_time, fmt="%H-%M-%S")
name_for_logs = strf_init_time

logger = setup_logger(
    "logger",
    os.path.join(logs_for_this_run, f"{name_for_logs}.log"),
)
# csv_log_path = os.path.join(logs_for_this_run, f"{name_for_logs}.csv")
# csv_log_path_candles = os.path.join(
#     logs_for_this_run, f"{name_for_logs}_candles.csv"
# )