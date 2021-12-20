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
interval = Client.KLINE_INTERVAL_15MINUTE
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
# buffer.data_window




# klines = client.futures_historical_klines(symbol, interval, fromdate)
# klines = process_futures_klines(klines)

# %%


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
    klines = klines[["t", "T", "o","h", "l", "c", "v"]] #klines.loc[:, [0, 6, 1,2, 3, 4, 5]]
    klines.columns = ["init_ts", "end_ts", "open", "high", "low", "close", "volume"]
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
    klines.update(klines.iloc[:, 2:].astype(float))
    # data_buffer.append(klines)
    buffer.push(klines)



twm.start_kline_futures_socket(callback = handle_socket_message, symbol=symbol, interval=interval)
buffer.data_window
# %%
import plotly.graph_objects as go

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

    sup_grid_coefs = np.arange(0.618, 2.618, step)
    inf_grid_coefs = np.arange(-0.618, -2.618, -step)

    grid_coefs = np.concatenate((np.sort(inf_grid_coefs), sup_grid_coefs))
    close_ema = klines["close"].ewm(span=w_atr, min_periods=w_atr).mean()
    atr_grid = [close_ema + atr * coef for coef in grid_coefs]
    return macd_hist, atr, atr_grid, close_ema

w_atr = 8 # ATR window
hist, atr, atr_grid, close_ema = compute_indicators(df, w1=12, w2=26, w3=9, w_atr = w_atr, step=0.15)

# %%
# klines.update(klines.iloc[:, 2:].astype(float))






# %%

from plotly.subplots import make_subplots


fig = make_subplots(rows=3, cols=4,
    specs=[[{'rowspan': 2, 'colspan': 3}, None, None, {'rowspan': 2}],
       [None, None, None, None],
       [{'colspan': 3}, None, None, {}]],
      vertical_spacing=0.075,
    horizontal_spacing=0.08,
    shared_xaxes=True)
# fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

# %%
df = buffer.data_window
kl_go = go.Candlestick(x=df['init_ts'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])


atr_go = go.Scatter(x=df.init_ts, y=atr,
                            mode="lines",
                            line=go.scatter.Line(color="gray"),
                            showlegend=False)
                            

ema_go = go.Scatter(x=df.init_ts, y=close_ema,
                            mode="lines",
                            # line=go.scatter.Line(color="blue"),
                            showlegend=True,
                            line=dict(color='royalblue', width=3),
                            opacity=0.75,
                            )



def hist_colors(hist):
    diffs = hist.diff()
    colors = diffs.apply(lambda x: "green" if x > 0 else "red")
    return colors




_hist_colors = hist_colors(hist)


hist_go = go.Scatter(x=df.init_ts, y=hist,
                            mode="lines+markers",
                            # line=go.scatter.Line(color="blue"),
                            showlegend=False,
                            line=dict(color="black", width=3),
                            opacity=1,
                            marker=dict(color=_hist_colors, size=6),
                            )


# %%

def plot_atr_grid(atr_grid, fig):
    for atr_band in atr_grid:
        atr_go = go.Scatter(x=df.init_ts, y=atr_band,
                            mode="lines",
                            # line=go.scatter.Line(color="teal"),
                            showlegend=False,
                            line=dict(color='teal', width=0.4), 
                            opacity=.8,
                            hoverinfo='skip')
        fig.add_trace(atr_go, row=1, col=1)


fig.add_trace(kl_go, row=1, col=1)
fig.update(layout_xaxis_rangeslider_visible=False)

fig.add_trace(ema_go, row=1, col=1)
fig.add_trace(hist_go, row=3, col=1)

plot_atr_grid(atr_grid, fig)

fig.update_layout(
    autosize=True,
    width=1000,
    height=600,
    margin=dict(
        l=10,
        r=10,
        b=10,
        t=10,
        pad=1
    ),
    paper_bgcolor="LightSteelBlue",
)

# %%


# fig.update_layout({'plot_bgcolor': "#21201f", 'paper_bgcolor': "#21201f", 'legend_orientation': "h"},
#                   legend=dict(y=1, x=0),
#                   font=dict(color='#dedddc'), dragmode='pan', hovermode='x',
#                   margin=dict(b=20, t=0, l=0, r=40),
#                   )
fig.update_layout({'paper_bgcolor': "#21201f", 'legend_orientation': "h"},
                  legend=dict(y=1, x=0),
                  font=dict(color='#dedddc'), dragmode='pan',
                  margin=dict(b=20, t=0, l=0, r=40),
                  )                  
# fig.update_xaxes(spikecolor="grey",spikethickness=1)
fig.update_xaxes(showgrid=True, zeroline=False, rangeslider_visible=False, showticklabels=False,
                 showspikes=True, spikemode='across', spikesnap='cursor', showline=False,
                 spikecolor="grey",spikethickness=1, spikedash='solid')
fig.update_yaxes(showspikes=True, spikedash='solid',spikemode='across', 
                spikecolor="grey",spikesnap="cursor",spikethickness=1)
# fig.update_layout(spikedistance=1000,hoverdistance=1000)
fig.update_layout(hovermode="x unified")


fig.update_traces(xaxis='x')
fig.show()



# %%
