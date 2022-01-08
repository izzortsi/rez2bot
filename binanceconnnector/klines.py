
# %%

import logging
from binance.futures import Futures as Client
from binance.lib.utils import config_logging

# %%

config_logging(logging, logging.DEBUG)

futures_client = Client()

# %%

logging.info(futures_client.klines("BTCUSDT", "1d", limit=10))
#%%
klines = futures_client.klines("BTCUSDT", "1d", limit=100)


#%%
import pandas as pd

def to_datetime_tz(arg, timedelta=-pd.Timedelta("03:00:00"), unit="ms", **kwargs):
    """
    to_datetime_tz(arg, timedelta=-pd.Timedelta("03:00:00"), unit="ms", **kwargs)

    Args:
        arg (float): epochtime
        timedelta (pd.Timedelta): timezone correction
        unit (string): unit in which `arg` is
        **kwargs: pd.to_datetime remaining kwargs
    Returns:
    pd.Timestamp: a timestamp corrected by the given timedelta
    """
    ts = pd.to_datetime(arg, unit=unit)
    return ts + timedelta
def process_futures_klines(klines):
    # klines = msg["k"]
    klines = pd.DataFrame.from_records(klines, coerce_float=True)
    klines = klines.loc[:, [0, 6, 1, 2, 3, 4, 5]]
    klines.columns = ["init_ts", "end_ts", "open", "high", "low", "close", "volume"]
    # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
    klines.update(klines.iloc[:, 2:].astype(float))
    return klines


# %%
pklines = process_futures_klines(klines)
#%%
pklines
#%%
