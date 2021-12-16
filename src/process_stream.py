
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



def process_futures_wsklines(klines):
    
    klines = pd.DataFrame.from_records(klines, index=[63])
    klines = pd.DataFrame(
        klines[["t", "T", "o", "h", "l", "c", "v"]], 
        columns=["init_ts", "end_ts", "open", "high", "low", "close", "volume"],
    )
    # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
    
    return klines

# def process_futures_wsklines(msg):
#     klines = msg["k"]

#     print(klines)
#     klines = pd.DataFrame.from_records(klines)
#     klines = pd.DataFrame(
#         klines[["t", "T", "o","c", "h", "l", "v"]], 
#         columns=["init_ts", "end_ts", "open", "close", "high", "low", "volume"],
#     )
#     # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
#     klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
#     klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
#     print(klines)
#     return klines


def process_futures_klines(klines):
    # klines = msg["k"]
    klines = pd.DataFrame.from_records(klines)
    klines = klines.loc[:, [0, 6, 1,2, 3, 4, 5]]
    klines.columns = ["init_ts", "end_ts", "open", "high", "low", "close", "volume"]
    # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
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
                row.end_ts.iloc[-1] = row.end_ts.iloc[-1]+(timestamp - self.data_window.init_ts.iloc[-2])
                self.data_window.update(row)
        # else:
        #     if row.init_ts.iloc[-1] - self.data_window.init_ts.iloc[-2] >= pd.Timedelta(self.granularity):
        #         # self.data_window.drop(index=[0], axis=0, inplace=True)
        #         self.data_window = self.data_window.append(
        #             row, ignore_index=True
        #                 )            



symbol = "ETHUSDT"
interval = Client.KLINE_INTERVAL_1MINUTE
fromdate = "15 Dec, 2021"


window_length = 64

# klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Dec, 2021")
# klines = client.futures_historical_klines(symbol, interval, fromdate, limit=window_length)
klines = client.futures_historical_klines(symbol, interval, fromdate)
klines = process_futures_klines(klines)
# klines

# %%
# len(klines)
# %%



data_window = klines.tail(window_length)
data_window.index = range(window_length)
# data_window

buffer = RingBuffer(window_length, interval, data_window)
# buffer.data_window




# klines = client.futures_historical_klines(symbol, interval, fromdate)
# klines = process_futures_klines(klines)


# socket manager using threads
twm = ThreadedWebsocketManager()
twm.start()


# raw_data_buffer = []
# data_buffer = []
# depth cache manager using threads

def handle_socket_message(msg):

    klines = msg["k"]
    # raw_data_buffer.append(klines)
    
    klines = pd.DataFrame.from_records(klines, index=[63])
    klines = klines[["t", "T", "o","c", "h", "l", "v"]] #klines.loc[:, [0, 6, 1,2, 3, 4, 5]]
    klines.columns = ["init_ts", "end_ts", "open", "close", "high", "low", "volume"]
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)

    # data_buffer.append(klines)
    buffer.push(klines)



twm.start_kline_futures_socket(callback = handle_socket_message, symbol=symbol, interval=interval)
# %%
buffer.data_window
# %%
import plotly.graph_objects as go

import pandas as pd
from datetime import datetime

df = buffer.data_window

fig = go.Figure(data=[go.Candlestick(x=df['init_ts'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])

fig.show()

# %%

# twm.start_kline_socket(callback=handle_socket_message, symbol='ETHUSDT')



# %%


# join the threaded managers to the main thread
# twm.join()


#%%

#%%
