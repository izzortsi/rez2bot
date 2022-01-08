import time
from tradingview_ta import TA_Handler, Interval, Exchange, get_multiple_analysis

import tradingview_ta
import threading
import tradingview_ta
import time
import numpy as np
import os
from unicorn_binance_rest_api.unicorn_binance_rest_api_manager import (
    BinanceRestApiManager as Client,
)
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import (
    BinanceWebSocketApiManager,
)
from unicorn_binance_rest_api.unicorn_binance_rest_api_exceptions import *
from imports_auxs_consts import *
import pandas as pd
from symbols_formats import FORMATS

# %%
substring_check = np.frompyfunc((lambda s, array: s in array), 2, 1)


def side_from_int(self):
    if self.position_type == -1:
        return "SELL", "BUY"
    elif self.position_type == 1:
        return "BUY", "SELL"


# %%

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

tframes = ["5m", "15m", "1h"]

coins = ["eth", "ada", "bnb", "xrp", "doge", "dot", "xlm", "iota", "dash"]

symbols_tv = [f"binance:{coin}usdt" for coin in coins]

# %%


class Trader(threading.Thread):
    def __init__(self, manager):

        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.manager = manager
        self.client = self.manager.client
        self.symbols = manager.symbols
        self.qty = self.manager.qty
        self.price_formatter = self.manager.price_formatter
        self.indicators = self.manager.indicators
        self.signals = self.manager.signals
        self.tp = self.manager.tp
        self.sl = self.manager.sl

        self.is_positioned = {symbol: None for symbol in self.symbols}
        self.position_type = {symbol: None for symbol in self.symbols}
        self.position = {symbol: None for symbol in self.symbols}
        self.entry_price = {symbol: None for symbol in self.symbols}
        self.entry_time = {symbol: None for symbol in self.symbols}
        self.exit_price = {symbol: None for symbol in self.symbols}
        self.exit_time = {symbol: None for symbol in self.symbols}
        self.exec_qty = {symbol: None for symbol in self.symbols}
        self.tp_order = {symbol: None for symbol in self.symbols}
        self.trades = {symbol: [] for symbol in self.symbols}

        self.start()

    def run(self):

        while self.manager.keep_alive:
            for symbol in self.symbols:
                # print(self.manager.signals_df[symbol])
                # print(np.any("BUY" in
                #             self.manager.signals_df[symbol].to_numpy()))
                if self.is_positioned[symbol]:
                    self.tp_order[symbol] = self.client.futures_get_order(
                        symbol=symbol.upper(), orderId=self.tp_order[symbol]["orderId"]
                    )
                    if self.tp_order[symbol]["status"] == "FILLED":
                        self.exit_price[symbol] = float(
                            self.tp_order[symbol]["avgPrice"]
                        )
                        self.exec_qty[symbol] = self.tp_order[symbol]["executedQty"]
                        self.exit_time[symbol] = to_datetime_tz(
                            self.tp_order[symbol]["updateTime"], unit="ms"
                        )
                        self.trades[symbol].append(
                            {
                                "order_id": self.tp_order[symbol]["orderId"],
                                "entry_price": self.entry_price[symbol],
                                "entry_time": self.entry_time[symbol],
                                "exit_price": self.exit_price[symbol],
                                "exit_time": self.exit_time[symbol],
                            }
                        )

                        print(
                            f"""
                        deal closed:
                        {self.trades[symbol][-1]}

                        {self.tp_order[symbol]}
                        """
                        )
                        self.is_positioned[symbol] = False
                        self.position_type[symbol] = 0
                else:
                    if np.all(substring_check("BUY", self.manager.signals_df[symbol])):

                        # self.trades[symbol].append(
                        #     f"BUY {symbol}: {self.manager.signals_df[symbol]}"
                        # )
                        self.is_positioned[symbol] = True
                        self.position_type[symbol] = 1
                        self.send_orders(symbol)
                        # print(f">>>> BUY {symbol}, {self.manager.signals_df[symbol]}")

                    elif np.all(
                        substring_check("SELL", self.manager.signals_df[symbol])
                    ):

                        self.is_positioned[symbol] = True
                        self.position_type[symbol] = -1
                        self.send_orders(symbol)

                        # self.trades[symbol].append(
                        #     f"SELL {symbol}: {self.manager.signals_df[symbol]}"
                        # )
                        # print(f">>>> SELL {symbol}, {self.manager.signals_df[symbol]}")
            time.sleep(0.2)

    def send_orders(self, symbol, protect=False):

        if self.position_type[symbol] == -1:
            side = "SELL"
            counterside = "BUY"
        elif self.position_type[symbol] == 1:
            side = "BUY"
            counterside = "SELL"

        try:
            new_position = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=self.qty[symbol],
                priceProtect=protect,
                workingType="CONTRACT_PRICE",
            )

        except BinanceAPIException as error:
            print(type(error))
            print("positioning, ", error)
        else:
            self.position[symbol] = self.client.futures_position_information(
                symbol=symbol
            )[-1]
            print(self.position[symbol])
            self.entry_price[symbol] = float(self.position[symbol]["entryPrice"])
            self.entry_time[symbol] = to_datetime_tz(
                self.position[symbol]["updateTime"], unit="ms"
            )
            # self.qty = self.position[0]["positionAmt"]
            tp_price = compute_exit(
                self.entry_price[symbol], self.tp[symbol], side=side
            )
            print("tp price", tp_price)
            tp_price = self.price_formatter(tp_price, symbol)
            entry_price = self.price_formatter(float(self.entry_price[symbol]), symbol)
            print("formatted entry price", entry_price)
            print("formatted tp price", tp_price)
            try:
                self.tp_order[symbol] = self.client.futures_create_order(
                    symbol=symbol,
                    side=counterside,
                    type="LIMIT",
                    price=tp_price,
                    workingType="CONTRACT_PRICE",
                    quantity=self.qty[symbol],
                    reduceOnly=True,
                    priceProtect=protect,
                    timeInForce="GTC",
                )
            except BinanceAPIException as error:

                print("tp order, ", error)


class Manager(threading.Thread):
    def __init__(
        self,
        api_key,
        api_secret,
        symbols,
        tframes,
        rate=1,
        qty=2,
        leverage=3,
        tp=0.03,
        sl=-0.02,
    ):

        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.client = Client(
            api_key=api_key, api_secret=api_secret, exchange="binance.com-futures"
        )

        self.symbols = symbols
        self.tframes = tframes

        self.rate = rate

        self.summaries = {
            symbol: {tf: None for tf in self.tframes} for symbol in self.symbols
        }
        self.indicators = {
            symbol: {tf: None for tf in self.tframes} for symbol in self.symbols
        }
        self.signals = {
            symbol: {tf: None for tf in self.tframes} for symbol in self.symbols
        }
        self.min_multiplier = qty
        self.qty = {symbol: None for symbol in self.symbols}
        self.tp = {symbol: tp for symbol in self.symbols}
        self.sl = {symbol: sl for symbol in self.symbols}
        self.leverage = {symbol: leverage for symbol in self.symbols}
        # self.price_formatter = {symbol: None for symbol in self.symbols}
        # self.price_formatter = lambda self, x, symbol: f"{x:.{price_precision}f}"
        self.format = {symbol: None for symbol in self.symbols}
        self.set_formats()
        self.set_leverages()

        self.signals_df = None
        self.keep_alive = True
        self.analysts = {}
        self.trader = None
        self.is_monitoring = False
        self.start()

    def make_analysts(self):

        for tf in self.tframes:
            self.analysts[tf] = Analyst(self, tf, self.rate)

    def run(self):
        self.make_analysts()
        time.sleep(5)
        self.signals_df = pd.DataFrame.from_dict(self.signals)
        time.sleep(2)
        self.trader = Trader(self)
        while self.keep_alive:
            self.signals_df = pd.DataFrame.from_dict(self.signals, dtype=str)
            if self.is_monitoring:
                self.pcheck()
            time.sleep(0.5)

    def pcheck(self):

        print(self.signals_df)

    def stop(self, q=0):
        self.keep_alive = False
        if q == 0:
            os.sys.exit()

    def price_formatter(self, x, symbol):
        precision = self.format[symbol]["tickSize"]
        return f"{x:.{precision}f}"

    def set_formats(self):
        for symbol in self.symbols:
            if symbol.upper() in FORMATS.keys():
                format = FORMATS[symbol.upper()]
                qty_precision = int(format["quantityPrecision"])
                price_precision = int(format["pricePrecision"])
                tick_size = int(format["tickSize"])
                format["quantityPrecision"] = qty_precision
                format["pricePrecision"] = price_precision
                format["tickSize"] = tick_size
                self.format[symbol] = format
                # print(qty_precision)
                # print(price_precision)
                notional = 5
                min_qty = 1 / 10 ** qty_precision

                ticker = self.client.get_symbol_ticker(symbol=symbol.upper())
                price = float(ticker["price"])
                multiplier = self.min_multiplier * np.ceil(notional / (price * min_qty))
                # f"{float(value):.{decimal_count}f}"

                self.qty[symbol] = f"{float(multiplier*min_qty):.{qty_precision}f}"
                # self.price_formatter[symbol] = lambda x: f"{x:.{price_precision}f}"
                print(
                    f"""
                {symbol}
                {min_qty}
                {qty_precision}, {price_precision}, {tick_size}
                {self.qty[symbol]}
                {self.price_formatter(price, symbol)}"""
                )

    def set_leverages(self):
        for symbol in self.symbols:
            self.client.futures_change_leverage(
                symbol=symbol, leverage=self.leverage[symbol]
            )


class Analyst(threading.Thread):
    def __init__(self, manager, interval, strategy=None):

        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.manager = manager
        self.symbols = self.manager.symbols
        self.symbols_tv = [f"binance:{symbol}" for symbol in self.symbols]
        self.strategy = strategy
        self.interval = interval
        self.rate = self.manager.rate

        self.analysises = None

        # self.keep_alive = self.manager.keep_alive

        self.is_printing = False
        self.start()

    def run(self):
        while self.manager.keep_alive:
            self.analysises = get_multiple_analysis(
                screener="crypto", interval=self.interval, symbols=self.symbols_tv
            )
            # print(self.interval, self.symbols_tv)
            self.process_analysises()

            time.sleep(60 / self.rate)

    def stop(self):
        self.keep_alive = False

    def process_analysises(self):

        for symbol, analysis in self.analysises.items():
            symbol = symbol.split(":")[-1]
            # print(symbol)
            self.manager.summaries[symbol][self.interval] = analysis.summary
            # self.indicators[symbol] = {
            #     indicator: analysis.indicators[indicator]
            #     for indicator in self.strategy.indicators}

            indicators = {
                "open": analysis.indicators["open"],
                # "high": analysis.indicators["high"],
                # "low": analysis.indicators["low"],
                "close": analysis.indicators["close"],
                "volume": analysis.indicators["volume"],
                "momentum": analysis.indicators["Mom"],
                "RSI": analysis.indicators["RSI"],
                "MACD_histogram": analysis.indicators["MACD.macd"]
                - analysis.indicators["MACD.signal"],
            }

            self.manager.indicators[symbol][self.interval] = indicators
            # recommendations.append(handler_summary["RECOMMENDATION"])
            # recommendations = np.array(recommendations)

            if (
                # indicators["RSI"] <= 50
                "BUY"
                in analysis.summary["RECOMMENDATION"]
                # indicators["momentum"] >= 0
                # and indicators["MACD_histogram"] >= 0
                # and "BUY" in analysis.summary["RECOMMENDATION"]
            ):

                self.manager.signals[symbol][self.interval] = "BUY"

            elif (
                # indicators["RSI"] >= 50
                "SELL"
                in analysis.summary["RECOMMENDATION"]
                # indicators["momentum"] <= 0
                # and indicators["MACD_histogram"] <= 0
                # and "SELL" in analysis.summary["RECOMMENDATION"]
            ):

                self.manager.signals[symbol][self.interval] = "SELL"

            else:

                self.manager.signals[symbol][self.interval] = "NEUTRAL"
