# %%

from binance.um_futures import UMFutures as Client

from threading import Thread, local
from datetime import datetime
from plotly.subplots import make_subplots

import numpy as np
import pandas_ta as ta
import time
import os
import pandas as pd
import argparse
import plotly.graph_objects as go

# %%


parser = argparse.ArgumentParser()
parser.add_argument("-pt", "--paper_trade", type=bool, default=True)
parser.add_argument("-tf", "--timeframe", type=str, default="15m")
# parser.add_argument("-fd", "--fromdate", type=str, default="12 hour ago")
parser.add_argument("-ppl", "--price_posision_low", type=float, default=0.5)
parser.add_argument("-pph", "--price_position_high", type=float, default=0.5)
# parser.add_argument("-gs", "--grid_shape", nargs="+", default=[, "b"])
# parser.add_argument("-e", nargs=6, metavar=('a', 'b', 'c', 'd', 'e', 'f'),
#                         help="my help message", type=float,
#                         default=None)
parser.add_argument("-wl", "--window_length", type=int, default=52)
parser.add_argument("-wa", "--atr_window_length", type=int, default=7)
parser.add_argument("-e", nargs="+", help="my help message", type=float,
                        default=(0.618, 1.0, 1.618))
parser.add_argument("--debug", type=bool, default=False)
parser.add_argument("--momentum", type=bool, default=False)
parser.add_argument("-ps", "--plot_screened", type=bool, default=False)
args = parser.parse_args()

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(key = api_key, secret = api_secret)

#interval = Client.KLINE_INTERVAL_1HOUR
#fromdate = "25 Dec, 2021"
#window_length = 52
#price_position_range = [0.15, 0.85]

interval = args.timeframe
# fromdate = args.fromdate
window_length = args.window_length
ppl, pph = args.price_posision_low, args.price_position_high
price_position_range = [ppl, pph]
w_atr = args.atr_window_length
pt = args.paper_trade
coefs = np.array(args.e)
debug = args.debug
momentum = args.momentum
plot_screened = args.plot_screened

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

def compute_indicators(klines, coefs=np.array([1.0, 1.364, 1.618, 1.854, 2.0, 2.364, 2.618]), w1=12, w2=26, w3=8, w_atr=8, step=0.4):
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
    # sup_grid_coefs = np.array([0.618, 0.708, 0.764, 0.854, 1.0, 1.236, 1.326, 1.382, 1.472, 1.618, 2.0, 2.326, 2.472, 2.618])
    # sup_grid_coefs = np.array([1.0, 1.364, 1.618, 2.0, 2.364, 2.618])
    # sup_grid_coefs = np.array([1.364, 1.618, 2.0, 2.364, 2.618])
    # sup_grid_coefs = np.array([1.0, 1.618, 2.0, 2.618])
    # sup_grid_coefs = np.array([0.854, 1, 1.618, 2.0, 2.618])
    sup_grid_coefs = coefs
    inf_grid_coefs = -1.0 * coefs

    hmean = klines.high.ewm(span=w_atr).mean()
    lmean = klines.low.ewm(span=w_atr).mean()
    global_volatility = (((hmean/lmean).mean()-1)*100)
    
    close_ema = klines["close"].ewm(span=w_atr, min_periods=w_atr).mean()
    close_std = klines["close"].ewm(span=w_atr, min_periods=w_atr).std()

    local_volatility = (close_std/close_ema).mean()*100

    grid_coefs = np.concatenate((np.sort(inf_grid_coefs), sup_grid_coefs))
    atr_grid = [close_ema + atr * coef for coef in grid_coefs]

    grid_coefs = sup_grid_coefs
    inf_grid = [close_ema - atr * coef for coef in grid_coefs]
    sup_grid = [close_ema + atr * coef for coef in grid_coefs]

    return macd_hist, atr, inf_grid, sup_grid, close_ema, atr_grid, local_volatility, global_volatility


# generating signals
def generate_signal(df, coefs, hist, inf_grid, sup_grid):
    signal = 0
    bands = [0 for _ in coefs]
    for i, (inf_band, sup_band) in enumerate(zip(inf_grid, sup_grid)):
        # print(hist.iloc[-1] > hist.iloc[-2])
        if momentum:
            if (
                df.close.iloc[-1] <= inf_band.iloc[-1]
            ) and (hist.iloc[-1] > hist.iloc[-2]):
                bands[i] = coefs[i]
                signal = 1
            elif (
                df.close.iloc[-1] >= sup_band.iloc[-1]
            ) and (hist.iloc[-1] < hist.iloc[-2]):
                bands[i] = -coefs[i]
                signal = -1
        else:
            if (
                df.close.iloc[-1] <= inf_band.iloc[-1]
            ):
                bands[i] = coefs[i]
                signal = 1
            elif (
                df.close.iloc[-1] >= sup_band.iloc[-1]
            ):
                bands[i] = -coefs[i]
                signal = -1
            
    return signal, bands



def process_all_stats(all_stats):
    perps = [pd.DataFrame.from_records([symbol_data]) for symbol_data in all_stats]
    return perps


# compute price position and check other stuff
def filter_perps(perps, price_position_range=[0.3, 0.7]):
    screened_symbols = []
    price_positions = []
    price_change = []
    daily_volatilities =[]
    for row in perps:
        if "USDT" in row.symbol.iloc[-1] and not ("_" in row.symbol.iloc[-1]) and not ("BTCDOMUSDT" == row.symbol.iloc[-1]):
            # screened_symbols.append(row)
            price_position = (
                float(row.lastPrice.iloc[-1]) - float(row.lowPrice.iloc[-1])
            ) / (float(row.highPrice.iloc[-1]) - float(row.lowPrice.iloc[-1]))
            
            # print(price_position)
            price_positions.append(price_position)  
            row["pricePosition"] = price_position
            row["dailyVolatility"] = (float(row.highPrice.iloc[-1])/float(row.lowPrice.iloc[-1]) - 1)*100
            daily_volatilities.append(row["dailyVolatility"])
            price_change.append(float(row["priceChangePercent"]))
            
            if (
                # price_position <= 0.2 or price_position >= 0.8
                price_position >= price_position_range[0]
                or price_position <= price_position_range[1]
            ):  # and float(row.priceChangePercent.iloc[-1]) >= -2.0:
                # if float(row.priceChangePercent.iloc[-1]) >= -1:
                # print(price_position)
                screened_symbols.append(row)
    print("MARKET SUMMARY:")                
    print(f"avg price position: {sum(np.array(price_positions))/len(price_positions)}")
    print(f"avg daily volatility: {sum(np.array(daily_volatilities))/len(daily_volatilities)}")
    print(f"avg % price change: {sum(np.array(price_change))/len(price_change)}")
    return screened_symbols


def generate_market_signals(symbols, coefs, interval, limit=99, paper=False, positions={}, cpnl={}, update_positions=False):
    # usdt_pairs = [f"{symbol}T" for symbol in symbols.pair]
    signals = {}
    # df = pd.DataFrame.from_dict({})
    df = []
    data = {}
    shown_data = []
    # for symbol in symbols.symbol:
    for index, row in symbols.iterrows():
        symbol = row.symbol
        # print(symbol)
        # print(type(symbol))
        klines = client.continuous_klines(symbol, contractType="PERPETUAL", interval=interval, limit=limit)
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
        #w_atr = 5
        hist, atr, inf_grid, sup_grid, close_ema, atr_grid, local_volatility, global_volatility = compute_indicators(
            dw, coefs, w1=12, w2=26, w3=8, w_atr=w_atr, step=0.12
        )

        signal, bands = generate_signal(dw, coefs, hist, inf_grid, sup_grid)
        intensity = sum(bands)/sum(coefs)
        
        
        # print("positions:", positions[symbol])

        
        
        if debug:
            print(f"Screening {symbol}...")
            # print(f"price position: {(float(dw.iloc[-1].close)-float(dw.iloc[-1].lowPrice))/(float(dw.iloc[-1].highPrice)-float(dw.iloc[-1].lowPrice))}")
            # print(f"daily volatility: {(float(dw.iloc[-1].highPrice)/float(dw.iloc[-1].lowPrice) - 1)*100}")
            # print(f"price change: {float(dw.iloc[-1].priceChangePercent)}")
            print(f"bands: {bands}")
            print(f"signal: {signal}")
            # print(f"intensity: {intensity}")
            print(f"close_ema: {close_ema.iloc[-1]}")
            # print(f"atr: {atr.iloc[-1]}")
            # print(f"inf_grid: {inf_grid.iloc[-1]}")
            # print(f"sup_grid: {sup_grid.iloc[-1]}")
            # print(f"local_volatility: {local_volatility}")
            # print(f"global_volatility: {global_volatility}")
            # print(f"hist: {hist.iloc[-1]}")
            print(f"atr_grid: {atr_grid.iloc[-1]}")
            print(f"\n")


        data[symbol] = {
            "signals": bands,
            "intensity": intensity,
            "klines": klines,
            "data_window": data_window,
            "hist": hist,
            "atr": atr,
            "inf_grid": inf_grid,
            "sup_grid": sup_grid,
            "close_ema": close_ema,
            "atr_grid": atr_grid,
            "local_volatility": local_volatility,
            "global_volatility": global_volatility,
        }

        if signal != 0:

            print(
            f"""{symbol}:
                signal: {signal}
                bands: {bands}
                volatility: {(local_volatility + global_volatility)/2} #
            """)

            signals[symbol] = bands
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

            shown_data.append(pd.DataFrame([[symbol, signal, data[symbol]["signals"], data[symbol]["local_volatility"], data[symbol]["global_volatility"]]], columns = ["symbol", "signal", "bands", "local_volatility", "global_volatility"]))
            if plot_screened:
                plot_symboL_atr_grid(symbol, data)
                


            if paper and update_positions:
                if signal > 0:
                    positions[symbol] = [1, sum(np.array(bands) * np.array(inf_grid)[:, -1])/sum(np.array(bands)), 0]
                    # print(positions[symbol])
                elif signal < 0:
                    positions[symbol] = [-1, sum(np.array(bands) * np.array(sup_grid)[:, -1])/sum(np.array(bands)), 0]
                    # print(positions[symbol])
            if paper and not update_positions:

                direction, value, pnl = positions[symbol]

                if direction == 1:
                    if 100*(df[-1].lastPrice - value)/value >= 0.32: #TP/Leverage
                        positions[symbol] = [0, 0, 100*(df[-1].lastPrice - value)/value - 0.08] #close the position, update final pnl
                        cpnl[symbol] += positions[symbol][-1]
                        update_positions = True
                    else:
                        positions[symbol][-1] = 100*(df[-1].lastPrice - value)/value - 0.08 #update pnl

                elif direction == -1:
                    if -100*(value - df[-1].lastPrice)/value  >= 0.32:
                        positions[symbol] = [0, 0, -100*(value - df[-1].lastPrice)/value - 0.08]
                        cpnl[symbol] += positions[symbol][-1]
                        update_positions = True
                    else:
                        positions[symbol][1] = -100*(value - df[-1].lastPrice)/value - 0.08 #update pnl
                    
                    
                # print(symbol, ": ", "signal:", signal, "intensity:", intensity, "bands:", bands)
                # print("positions:", positions[symbol])


        # signals[symbol] = [signal, df]
    return signals, df, data, positions, cpnl, shown_data

def prescreen():
    all_stats = client.ticker_24hr_price_change()

    perps = process_all_stats(all_stats)
    filtered_perps = filter_perps(perps, price_position_range=price_position_range)
    filtered_perps = pd.concat(filtered_perps, axis=0)
    return filtered_perps

def postscreen(filtered_perps, paper=False, positions={}, cpnl={}, update_positions=True):
    signals, rows, data, positions, cpnl, shown_data = generate_market_signals(filtered_perps, coefs, interval, limit=99, paper=paper, positions = positions, cpnl=cpnl, update_positions=update_positions)    
    return signals, rows, data, positions, cpnl, shown_data

def updatescreen(positions, cpnl):
    signals, rows, data, positions, cpnl, shown_data = generate_market_signals(filtered_perps, coefs, interval, limit=99, paper=True, positions = positions, cpnl=cpnl, update_positions=False)    
    return signals, rows, data, positions, cpnl, shown_data

def screen():
    all_stats = client.ticker_24hr_price_change()

    perps = process_all_stats(all_stats)
    filtered_perps = filter_perps(perps, price_position_range=price_position_range)
    filtered_perps = pd.concat(filtered_perps, axis=0)
    signals, rows, data, positions, shown_data = generate_market_signals(filtered_perps, coefs, interval, update_positions=True)
    return signals, rows, data, positions, shown_data



def plot_single_atr_grid(df, atr, atr_grid, close_ema, hist):
    
    
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


    fig.add_trace(kl_go, row=1, col=1)
    fig.update(layout_xaxis_rangeslider_visible=False)
    #fig.update_layout(title_text="___USDT@15m")
    fig.update()

    fig.add_trace(ema_go, row=1, col=1)
    fig.add_trace(hist_go, row=3, col=1)
    
    plot_atr_grid(atr_grid, fig)

    return fig

def plot_symboL_atr_grid(symbol, data):
    fig = plot_single_atr_grid(
        data[symbol]["data_window"], 
        data[symbol]["atr"], 
        data[symbol]["atr_grid"], 
        data[symbol]["close_ema"], 
        data[symbol]["hist"],
    )
    fig.update_layout(title_text=f"{symbol}@{interval}")
    fig.show()
    # return fig

def plot_all_screened(screened_pairs, data):
    for pair in screened_pairs:
        plot_symboL_atr_grid(pair, data)

if __name__ == "__main__":
    
    filtered_perps = prescreen()
    print(filtered_perps)
    
    signals, rows, data, positions, cpnl, shown_data = postscreen(filtered_perps, paper=pt, update_positions=True)
    
    if len(rows) > 0:
        sdata = pd.concat(shown_data, axis=0)
        sdf = pd.concat(rows, axis=1).transpose()
        spairs = list(sdf.symbol)
        # plot_all_screened(spairs, data)
        # for pair in spairs:
            # print(pair, ": ", data[pair]["atr_grid"])
        print(sdata)
        # print("positions: ", positions)
    else:
        print("Nothing found :( ")
#%%
