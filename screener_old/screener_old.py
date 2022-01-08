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
    klines = klines.loc[:, [0, 6, 1, 2, 3, 4, 5]]
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
        row.end_ts.iloc[-1] = self.data_window.end_ts.iloc[-2] + pd.Timedelta(
            self.granularity
        )
        # print(row.init_ts.iloc[-1] - self.data_window.init_ts.iloc[-2])
        if self._isfull():
            # print(row.init_ts.iloc[-1])
            # print(self.data_window.init_ts.iloc[-1])
            # print(self.data_window.init_ts.iloc[-1] - row.init_ts.iloc[-1])
            if row.init_ts.iloc[-1] - self.data_window.init_ts.iloc[-2] >= pd.Timedelta(
                self.granularity
            ):
                # print(1)
                self.data_window.drop(index=[0], axis=0, inplace=True)
                # row.index[-1] = self.window_length - 1
                # print(self.data_window.iloc[-1])
                # print(row)
                self.data_window = self.data_window.append(row, ignore_index=True)
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


interval = Client.KLINE_INTERVAL_1HOUR
fromdate = "20 Dec, 2021"
window_length = 49

import pandas as pd
from datetime import datetime


def compute_indicators(klines, w1=12, w2=26, w3=9, w_atr=5, step=0.4):
    # compute macd
    macd = pd.Series(
        klines["close"].ewm(span=w1, min_periods=w1).mean()
        - klines["close"].ewm(span=w2, min_periods=w2).mean()
    )
    macd_signal = macd.ewm(span=w3, min_periods=w3).mean()
    macd_hist = macd - macd_signal
    # compute atr bands

    atr = ta.atr(klines["high"], klines["low"], klines["close"], length=w_atr)

    # sup_grid_coefs = np.array([0.618, 1.0, 1.618, 2.0, 2.618])
    # sup_grid_coefs = np.array([1.0, 1.364, 1.618, 2.0, 2.364, 2.618])
    sup_grid_coefs = np.array([1.364, 1.618, 2.0, 2.364, 2.618])
    inf_grid_coefs = -1.0 * sup_grid_coefs

    close_ema = klines["close"].ewm(span=w_atr, min_periods=w_atr).mean()

    grid_coefs = np.concatenate((np.sort(inf_grid_coefs), sup_grid_coefs))
    atr_grid = [close_ema + atr * coef for coef in grid_coefs]

    grid_coefs = sup_grid_coefs
    inf_grid = [close_ema - atr * coef for coef in grid_coefs]
    sup_grid = [close_ema + atr * coef for coef in grid_coefs]

    return macd_hist, atr, inf_grid, sup_grid, close_ema, atr_grid


# generating signals
def generate_signal(df, hist, inf_grid, sup_grid):
    signal = 0
    for inf_band, sup_band in zip(inf_grid, sup_grid):

        if (
            df.close.iloc[-1]
            <= inf_band.iloc[-1]
            # and (hist.iloc[-1] > hist.iloc[-2])
        ):
            signal = 1
        elif (
            df.close.iloc[-1]
            >= sup_band.iloc[-1]
            # and (hist.iloc[-1] < hist.iloc[-2])
        ):
            signal = -1
    return signal


# %%

all_stats = client.futures_ticker()

all_stats


# perps = [symbol_data if "USDT" in symbol_data["symbol"] else None for symbol_data in all_stats]

# %%
def process_all_stats(all_stats):
    perps = [pd.DataFrame.from_records([symbol_data]) for symbol_data in all_stats]
    return perps


# %%
perps = process_all_stats(all_stats)

# %%

len(perps)

# %%
perps[0].symbol
# %%
# compute price position and check other stuff
def filter_perps(perps):
    screened_symbols = []
    for row in perps:
        if "USDT" in row.symbol.iloc[-1] and not ("_" in row.symbol.iloc[-1]):
            # screened_symbols.append(row)
            price_position = (
                float(row.lastPrice.iloc[-1]) - float(row.lowPrice.iloc[-1])
            ) / (float(row.highPrice.iloc[-1]) - float(row.lowPrice.iloc[-1]))
            # print(price_position)
            row["pricePosition"] = price_position
            if (
                price_position <= 0.15 or price_position >= 0.85
            ):  # and float(row.priceChangePercent.iloc[-1]) >= -2.0:
                # if float(row.priceChangePercent.iloc[-1]) >= -1:
                # print(price_position)
                screened_symbols.append(row)
    return screened_symbols


# %%
perps

# %%
filtered_perps = filter_perps(perps)

filtered_perps = pd.concat(filtered_perps, axis=0)
# %%
filtered_perps

# %%
# filtered_perps.pair
# signals = {symbol: 0 for symbol in filtered_perps.pair}

# %%
# signals
# %%
def do_the_data_stuff(symbols, interval, fromdate):
    # usdt_pairs = [f"{symbol}T" for symbol in symbols.pair]
    signals = {}
    for symbol in symbols.symbol:
        # print(symbol)
        # print(type(symbol))
        klines = client.futures_historical_klines(symbol, interval, fromdate)
        klines = process_futures_klines(klines)

        data_window = klines.tail(window_length)
        data_window.index = range(window_length)
        # data_window

        # buffer = RingBuffer(window_length, interval, data_window)
        # df = buffer.data_window
        df = data_window
        w_atr = 8  # ATR window

        hist, atr, inf_grid, sup_grid, close_ema, atr_grid = compute_indicators(
            df, w1=12, w2=26, w3=9, w_atr=w_atr, step=0.15
        )
        signal = generate_signal(df, hist, inf_grid, sup_grid)
        if signal != 0:
            signals[symbol] = signal
            print(symbol, ": ", signal)
        # signals[symbol] = [signal, df]
    return signals


# %%
signals = do_the_data_stuff(filtered_perps, interval, fromdate)

# %%
signals

# %%


# %%

# %%


# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#%%

# %%

fig = make_subplots(
    rows=3,
    cols=4,
    specs=[
        [{"rowspan": 2, "colspan": 3}, None, None, {"rowspan": 2}],
        [None, None, None, None],
        [{"colspan": 3}, None, None, {}],
    ],
    vertical_spacing=0.075,
    horizontal_spacing=0.08,
    shared_xaxes=True,
)
#%%
def plot_all(fig, df, hist, atr, atr_grid, close_ema):

    # fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

    # %%

    kl_go = go.Candlestick(
        x=df["init_ts"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
    )

    atr_go = go.Scatter(
        x=df.init_ts,
        y=atr,
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=False,
    )

    ema_go = go.Scatter(
        x=df.init_ts,
        y=close_ema,
        mode="lines",
        # line=go.scatter.Line(color="blue"),
        showlegend=True,
        line=dict(color="royalblue", width=3),
        opacity=0.75,
    )

    def hist_colors(hist):
        diffs = hist.diff()
        colors = diffs.apply(lambda x: "green" if x > 0 else "red")
        return colors

    _hist_colors = hist_colors(hist)

    hist_go = go.Scatter(
        x=df.init_ts,
        y=hist,
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
            atr_go = go.Scatter(
                x=df.init_ts,
                y=atr_band,
                mode="lines",
                # line=go.scatter.Line(color="teal"),
                showlegend=False,
                line=dict(color="teal", width=0.4),
                opacity=0.8,
                hoverinfo="skip",
            )
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
        margin=dict(l=10, r=10, b=10, t=10, pad=1),
        paper_bgcolor="LightSteelBlue",
    )

    # %%

    # fig.update_layout({'plot_bgcolor': "#21201f", 'paper_bgcolor': "#21201f", 'legend_orientation': "h"},
    #                   legend=dict(y=1, x=0),
    #                   font=dict(color='#dedddc'), dragmode='pan', hovermode='x',
    #                   margin=dict(b=20, t=0, l=0, r=40),
    #                   )
    fig.update_layout(
        {"paper_bgcolor": "#21201f", "legend_orientation": "h"},
        legend=dict(y=1, x=0),
        font=dict(color="#dedddc"),
        dragmode="pan",
        margin=dict(b=20, t=0, l=0, r=40),
    )
    # fig.update_xaxes(spikecolor="grey",spikethickness=1)
    fig.update_xaxes(
        showgrid=True,
        zeroline=False,
        rangeslider_visible=False,
        showticklabels=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        showline=False,
        spikecolor="grey",
        spikethickness=1,
        spikedash="solid",
    )
    fig.update_yaxes(
        showspikes=True,
        spikedash="solid",
        spikemode="across",
        spikecolor="grey",
        spikesnap="cursor",
        spikethickness=1,
    )
    # fig.update_layout(spikedistance=1000,hoverdistance=1000)
    fig.update_layout(hovermode="x unified")

    fig.update_traces(xaxis="x")
    return fig


# %%

fig = plot_all(fig, df, hist, atr, atr_grid, close_ema)
#%%
fig.show()
#%%

#%%

#%%

#%%
