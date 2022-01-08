# %%

import pandas as pd
import json

from binance.client import Client
from binance.enums import *
import unicorn_binance_rest_api as ubr
import unicorn_binance_websocket_api as ubw
import unicorn_binance_rest_api.unicorn_binance_rest_api_enums as enums
from unicorn_binance_rest_api.unicorn_binance_rest_api_exceptions import *
import os
import threading
import time
import tradingview_ta as ta

# %%


# %%


api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%


info_data = client.get_exchange_info()



def f_price(price):
    return f"{price:.2f}"


# %%



# %%
# SIDE = "BUY"
S = "SELL"
B = "BUY"


# %%
def compute_exit(entry_price, target_profit, side, entry_fee=0.04, exit_fee=0.04):
    if side == "BUY":
        exit_price = (
            entry_price
            * (1 + target_profit / 100 + entry_fee / 100)
            / (1 - exit_fee / 100)
        )
    elif side == "SELL":
        exit_price = (
            entry_price
            * (1 - target_profit / 100 - entry_fee / 100)
            / (1 + exit_fee / 100)
        )
    return exit_price

class OrderMaker:
    def __init__(self, client):
        self.client = client
        self.is_positioned = False
        self.side = None
        self.counterside = None
        self.entry_price = None
        self.tp_price = None
        self.qty = None

    def send_order(self, symbol, tp, qty, side="BUY", protect=False, sl=None):
        if side == "SELL":
            self.side = "SELL"
            self.counterside = "BUY"
        elif side == "BUY":
            self.side = "BUY"
            self.counterside = "SELL"

        if not self.is_positioned:
            try:
                new_position = self.client.futures_create_order(
                    symbol=symbol,
                    side=self.side,
                    type="MARKET",
                    quantity=qty,
                    priceProtect=protect,
                    workingType="CONTRACT_PRICE",
                )
            except BinanceAPIException as error:
                print(type(error))
                print("positioning, ", error)
            else:
                self.is_positioned = True
                self.position = self.client.futures_position_information(symbol=symbol)
                self.entry_price = float(self.position[0]["entryPrice"])
                self.qty = self.position[0]["positionAmt"]
                # tp_price = f_tp_price(price, tp, lev, side=side)
                # sl_price = f_sl_price(price, sl, lev, side=side)
                self.tp_price = f_price(
                    compute_exit(self.entry_price, tp, side=self.side)
                )

                print(
                    f"""price: {self.entry_price}
                          tp_price: {self.tp_price}
                          """
                )

                try:
                    self.tp_order = self.client.futures_create_order(
                        symbol=symbol,
                        side=self.counterside,
                        type="LIMIT",
                        price=self.tp_price,
                        workingType="CONTRACT_PRICE",
                        quantity=self.qty,
                        reduceOnly=True,
                        priceProtect=protect,
                        timeInForce="GTC",
                    )
                except BinanceAPIException as error:
                    print(type(error))
                    print("tp order, ", error)
                if sl is not None:
                    self.sl_price = f_price(
                        compute_exit(self.entry_price, sl, side=self.counterside)
                    )
                    try:
                        self.sl_order = self.client.futures_create_order(
                            symbol=symbol,
                            side=self.counterside,
                            type="LIMIT",
                            price=self.sl_price,
                            workingType="CONTRACT_PRICE",
                            quantity=self.qty,
                            reduceOnly=True,
                            priceProtect=protect,
                            timeInForce="GTC",
                        )
                    except BinanceAPIException as error:
                        print(type(error))
                        print("sl order, ", error)

    def send_tp_order(self, symbol, side, tp, protect=False):
        if side == "SELL":
            counterside = "BUY"
        elif side == "BUY":
            counterside = "SELL"
        self.position = self.client.futures_position_information(symbol=symbol)
        self.entry_price = float(self.position[0]["entryPrice"])
        self.qty = self.position[0]["positionAmt"]
        # tp_price = f_tp_price(price, tp, lev, side=side)
        # sl_price = f_sl_price(price, sl, lev, side=side)
        self.tp_price = f_price(compute_exit(self.entry_price, tp, side=side))

        try:
            self.tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=counterside,
                type="LIMIT",
                price=self.tp_price,
                workingType="CONTRACT_PRICE",
                quantity=self.qty,
                reduceOnly=True,
                priceProtect=protect,
                timeInForce="GTC",
            )
        except BinanceAPIException as error:
            print(type(error))
            print("tp order, ", error)


# %%
om = OrderMaker(client)

if __name__=="__main__":
    
# %%
# omaker.send_order(symbol, 0.1, 0.02, side=B)

# %%
# omaker.send_tp_order(symbol, B, 0.04)
# %%
# ep = omaker.entry_price
# tpp = float(omaker.tp_price)
# 100 * (tpp - ep) / ep

# %%
# o = omaker.tp_order

# %%


# %%


# %%
orders
# %%

o["orderId"]
# %%
client.futures_get_order(symbol=symbol.upper(), orderId=o["orderId"])


# %%
