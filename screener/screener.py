# %%

from binance import Client, ThreadedWebsocketManager
from binance.enums import *
from threading import Thread
import numpy as np
import pandas as pd
import pandas_ta as ta
import time
import os


api_key = os.environ.get("API_KEY") 
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)


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



# def process_futures_wsklines(klines):
    
#     klines = pd.DataFrame.from_records(klines, index=[63])
#     klines = pd.DataFrame(
#         klines[["t", "T", "o", "h", "l", "c", "v"]], 
#         columns=["init_ts", "end_ts", "open", "high", "low", "close", "volume"], dtype=float,
#     )
#     # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
#     klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
#     klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
#     klines.update(klines.iloc[:, 2:].astype(float))
#     return klines


def process_futures_klines(klines):
    # klines = msg["k"]
    klines = pd.DataFrame.from_records(klines, coerce_float=True)
    klines = klines.loc[:, [0, 6, 1,2, 3, 4, 5]]
    klines.columns = ["init_ts", "end_ts", "open", "high", "low", "close", "volume"]
    # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
    klines.update(klines.iloc[:, 2:].astype(float))
    return klines
    
   
class RingBuffer:
    
    def __init__(self, window_length, granularity, data_window):
        self.window_length = window_length
        self.granularity = granularity
        self.data_window = data_window
        
    def _isfull(self):
        if len(self.data_window) >= self.window_length:
            return True

    def push(self, row):
        row.end_ts.iloc[-1] = self.data_window.end_ts.iloc[-2]+pd.Timedelta(self.granularity)
        # print(row.init_ts.iloc[-1] - self.data_window.init_ts.iloc[-2])
        if self._isfull():
            # print(row.init_ts.iloc[-1])
            # print(self.data_window.init_ts.iloc[-1])
            # print(self.data_window.init_ts.iloc[-1] - row.init_ts.iloc[-1])
            if row.init_ts.iloc[-1] - self.data_window.init_ts.iloc[-2] >= pd.Timedelta(self.granularity):
                # print(1)
                self.data_window.drop(index=[0], axis=0, inplace=True)
                # row.index[-1] = self.window_length - 1
                # print(self.data_window.iloc[-1])
                # print(row)
                self.data_window = self.data_window.append(
                    row, ignore_index=True
                        )
            else:
                timestamp = to_datetime_tz(time.time(), unit="s")
                row.init_ts.iloc[-1] = timestamp
                # print(self.data_window.iloc[-1])
                # print(row)
                
                self.data_window.update(row)
        # else:
        #     if row.init_ts.iloc[-1] - self.data_window.init_ts.iloc[-2] >= pd.Timedelta(self.granularity):
        #         # self.data_window.drop(index=[0], axis=0, inplace=True)
        #         self.data_window = self.data_window.append(
        #             row, ignore_index=True
        #                 )            


# %%


symbol = "ETHUSDT"
interval = Client.KLINE_INTERVAL_1HOUR
fromdate = "15 Dec, 2021"


window_length = 64

# %%

# klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Dec, 2021")
# klines = client.futures_historical_klines(symbol, interval, fromdate, limit=window_length)
klines = client.futures_historical_klines(symbol, interval, fromdate)
klines = process_futures_klines(klines)
# klines


# len(klines)




data_window = klines.tail(window_length)
data_window.index = range(window_length)
# data_window

buffer = RingBuffer(window_length, interval, data_window)


import pandas as pd
from datetime import datetime

df = buffer.data_window

def compute_indicators(klines, w1=12, w2=26, w3=9, w_atr = 8, step=0.4):
    # compute macd
    macd = pd.Series(klines["close"].ewm(span=w1, min_periods=w1).mean() - klines["close"].ewm(span=w2, min_periods=w2).mean())
    macd_signal = macd.ewm(span=w3, min_periods=w3).mean()
    macd_hist = macd - macd_signal
    # compute atr bands

    atr = ta.atr(klines["high"], klines["low"], klines["close"], length=w_atr)

    # sup_grid_coefs = np.array([0.618, 1.0, 1.618, 2.0, 2.618])
    sup_grid_coefs = np.array([1.0, 1.364, 1.618, 2.0, 2.364, 2.618])
    inf_grid_coefs = -1.0*sup_grid_coefs

    grid_coefs = np.concatenate((np.sort(inf_grid_coefs), sup_grid_coefs))
    close_ema = klines["close"].ewm(span=w_atr, min_periods=w_atr).mean()
    atr_grid = [close_ema + atr * coef for coef in grid_coefs]
    return macd_hist, atr, atr_grid, close_ema

w_atr = 8 # ATR window
hist, atr, atr_grid, close_ema = compute_indicators(df, w1=12, w2=26, w3=9, w_atr = w_atr, step=0.15)

# %%
# klines.update(klines.iloc[:, 2:].astype(float))


df = buffer.data_window

#generating signals
def generate_signal(df, atr_grid):
    signal = 0
    for i, atr_band in enumerate(atr_grid):

        if (
            (df.close.iloc[-1] <= atr_band.iloc[-1]) 
            and (df.hist.iloc[-1] > df.hist.iloc[-2])
            ):
            signal = 1
        elif (
            (df.close.iloc[-1] >= atr_band.iloc[-1]) 
            and (df.hist.iloc[-1] < df.hist.iloc[-2])
            ):
            signal = -1
    return signal

# %%
signal = generate_signal(df, atr_grid)

# %%
signal
# %%

#%%

#%%

#%%
