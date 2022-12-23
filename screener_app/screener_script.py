# %%

from binance.um_futures import UMFutures as Client
from threading import Thread
from datetime import datetime
import numpy as np
import pandas as pd
import pandas_ta as ta
import time
import os
import pandas as pd
import argparse
import plotly.graph_objects as go
from plotly.subplots import make_subplots

parser = argparse.ArgumentParser()
parser.add_argument("-tf", "--timeframe", default="30m", type=str)
parser.add_argument("-wl", "--window_length", default=52, type=int)
parser.add_argument("-ppl", "--price_position_low", default = 0.15, type=float)
parser.add_argument("-pph", "--price_position_high", default = 0.85, type=float)
parser.add_argument("-fd", "--fromdate", default="1 Dec, 2022", type=str)
args = parser.parse_args()
# interval = Client.KLINE_INTERVAL_15MINUTE
fromdate = args.fromdate
window_length = args.window_length
price_position_range = [args.price_position_low, args.price_position_high]
interval = args.timeframe

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

def plot_single_atr_grid(symbol, df, atr, atr_grid, close_ema, hist):
    
    
    fig = make_subplots(rows=3, cols=4,
        specs=[[{'rowspan': 2, 'colspan': 3}, None, None, {'rowspan': 2}],
        [None, None, None, None],
        [{'colspan': 3}, None, None, {}]],
        vertical_spacing=0.075,
        horizontal_spacing=0.08,
        shared_xaxes=True,
        )
    # fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

    # %%
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

    def plot_atr_grid(atr_grid, fig):
        for atr_band in atr_grid:
            if sum(atr_band) >= 1.2 * sum(close_ema):
                color = 'red'
            else:
                color = "teal"
            atr_go = go.Scatter(x=df.init_ts, y=atr_band,
                                mode="lines",
                                # line=go.scatter.Line(color="teal"),
                                showlegend=False,
                                line=dict(color=color, width=0.4), 
                                opacity=.8,
                                hoverinfo='skip')
            fig.add_trace(atr_go, row=1, col=1)


    fig.update_layout(height=800, width=1200, title_text=f"{symbol}")
    fig.add_trace(kl_go, row=1, col=1)

    fig.update(layout_xaxis_rangeslider_visible=False)

    fig.add_trace(ema_go, row=1, col=1)
    fig.add_trace(hist_go, row=3, col=1)

    plot_atr_grid(atr_grid, fig)

    return fig

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

    sup_grid_coefs = np.array([0.7, 1.0, 1.364, 1.618, 2.0, 2.364, 2.618])
    # sup_grid_coefs = np.array([1.0, 1.364, 1.618, 2.0, 2.364, 2.618])
    # sup_grid_coefs = np.array([1.364, 1.618, 2.0, 2.364, 2.618])
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
        # print(hist.iloc[-1] > hist.iloc[-2])
        if (
            df.close.iloc[-1] <= inf_band.iloc[-1]
        ):  # and (hist.iloc[-1] > hist.iloc[-2]):
            signal = 1
        elif (
            df.close.iloc[-1] >= sup_band.iloc[-1]
        ):  # and (hist.iloc[-1] < hist.iloc[-2]):
            signal = -1
    return signal


def process_all_stats(all_stats):
    perps = [pd.DataFrame.from_records([symbol_data]) for symbol_data in all_stats]
    return perps


# compute price position and check other stuff
def filter_perps(perps, price_position_range=[0.3, 0.7]):
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
                # price_position <= 0.2 or price_position >= 0.8
                price_position <= price_position_range[0]
                or price_position >= price_position_range[1]
            ):  # and float(row.priceChangePercent.iloc[-1]) >= -2.0:
                # if float(row.priceChangePercent.iloc[-1]) >= -1:
                # print(price_position)
                screened_symbols.append(row)
    return screened_symbols


def generate_market_signals(symbols, interval, fromdate):
    # usdt_pairs = [f"{symbol}T" for symbol in symbols.pair]
    signals = {}
    # df = pd.DataFrame.from_dict({})
    df = []
    data = {}
    # for symbol in symbols.symbol:
    for index, row in symbols.iterrows():
        symbol = row.symbol
        # print(symbol)
        # print(type(symbol))
        klines = client.continuous_klines(symbol, "PERPETUAL", interval, startTime = fromdate)
        klines = process_futures_klines(klines)
        # print(f"len klines: {len(klines)}")
        data_window = klines.tail(window_length)
        # data_window.index = range(window_length)
        # print(f"len dw: {len(data_window)}")
        data_window.index = range(len(data_window))
        # data_window

        # buffer = RingBuffer(window_length, interval, data_window)
        # df = buffer.data_window
        dw = data_window
        w_atr = 5
        hist, atr, inf_grid, sup_grid, close_ema, atr_grid = compute_indicators(
            dw, w1=12, w2=26, w3=9, w_atr=w_atr, step=0.12
        )
        signal = generate_signal(dw, hist, inf_grid, sup_grid)

        data[symbol] = {
            "signals": signal,
            "klines": klines,
            "data_window": data_window,
            "hist": hist,
            "atr": atr,
            "inf_grid": inf_grid,
            "sup_grid": sup_grid,
            "close_ema": close_ema,
            "atr_grid": atr_grid,
        }

        if signal != 0:
            signals[symbol] = signal
            df.append(
                row.filter(
                    items=[
                        "symbol",
                        "priceChangePercent",
                        "lastPrice",
                        "weightedAvgPrice",
                        "pricePosition",
                    ]
                )
            )
            print(symbol, ": ", signal)
        # signals[symbol] = [signal, df]
    return signals, df, data

def plot_symboL_atr_grid(symbol, data):
    fig = plot_single_atr_grid(
        symbol,
        data[symbol]["data_window"], 
        data[symbol]["atr"], 
        data[symbol]["atr_grid"], 
        data[symbol]["close_ema"], 
        data[symbol]["hist"],
    )
    fig.show()

def screen():
    all_stats = client.ticker_24hr_price_change()
    perps = process_all_stats(all_stats)
    filtered_perps = filter_perps(perps, price_position_range=price_position_range)
    filtered_perps = pd.concat(filtered_perps, axis=0)
    signals, rows, data = generate_market_signals(filtered_perps, interval, fromdate)
    return signals, rows, data


def main():

# %%

    signals, rows, data = screen()

    print(signals)
    
    if len(rows) > 0:
        sdf = pd.concat(rows, axis=1).transpose()
    
    screened_pairs = list(sdf.symbol)

    for pair in screened_pairs:
        plot_symboL_atr_grid(pair, data)



    # return fig
# %%
# c1, c2 = screened_pairs


# %%


if __name__ == "__main__":
    
    api_key = os.environ.get("API_KEY")
    api_secret = os.environ.get("API_SECRET")
    client = Client(api_key, api_secret)



    main()


