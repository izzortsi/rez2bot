# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
from symbols_formats import FORMATS
import os
import argparse
import numpy as np
# %%

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--symbol", type=str)
parser.add_argument("-side", "--side", type=int)
parser.add_argument("-ge", "--grid_end", type=float, default=None)

parser.add_argument("-tp", "--take_profit", type=float, default=0.33)
parser.add_argument("-q", "--quantity", type=int, default=1)
# parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
# parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
# parser.add_argument("-gs", "--grid_step", type=float, default=0.12)
args = parser.parse_args()
side = args.side
symbol = args.symbol
grid_end = args.grid_end
take_profit = args.take_profit
qty = args.quantity
# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

S = "SELL"
B = "BUY"

# %%


import time
from binance.client import Client
client = Client(api_key, api_secret)
int(time.time() * 1000) - client.get_server_time()['serverTime']

# %%
(int(time.time() * 1000) - client.get_server_time()['serverTime'])/(1000*60)


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

class GridOrderMaker:
    def __init__(self, client, symbol, grid_end=None):
        self.client = client
        self.is_positioned = False
        self.side = None
        self.counterside = None
        self.entry_price = None
        self.tp_price = None
        self.qty = None
        self.symbols = symbol.upper()
        self.grid_end = grid_end
        # self.formatters = {symbol: self.set_price_formats(symbol) for symbol in symbols}

        self.order_grid = []
    
    def set_price_formats(self):
    
        if self.symbol in FORMATS.keys():
            format = FORMATS[self.symbol]
            qty_precision = int(format["quantityPrecision"])
            price_precision = int(format["pricePrecision"])
            # print(qty_precision)
            # print(price_precision)
            notional = 5
            min_qty = 1 / 10 ** qty_precision
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            price = float(ticker["price"])
            multiplier = self.qty * np.ceil(notional / (price * min_qty))
            # f"{float(value):.{decimal_count}f}"
            self.qty = f"{float(multiplier*min_qty):.{qty_precision}f}"
            self.price_formatter = lambda x: f"{float(x):.{price_precision-1}f}"
            print(min_qty)
            print(self.qty)
            print(self.price_formatter(price))    

    def send_order_grid(self, symbol, tp, qty, side, ge, gs=0.12,  protect=False, sl=None):
        if side == "SELL":
            self.side = "SELL"
            self.counterside = "BUY"
        elif side == "BUY":
            self.side = "BUY"
            self.counterside = "SELL"

        self.grid_end = ge        
        # grid_coefs = np.arange(gr[0], gr[1], gs)

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

                self.price_grid = np.geomspace(self.entry_price, self.grid_end, num=5, dtype=float)
                
                # tp_price = f_tp_price(price, tp, lev, side=side)
                # sl_price = f_sl_price(price, sl, lev, side=side)
                self.tp_price = self.price_formatter(
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
                    self.sl_price = self.price_formatter(
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

                for i, band in enumerate(self.price_grid[1:]):
                    band_price = self.price_formatter(band)
                    
                    try:
                        grid_order = self.client.futures_create_order(
                            symbol=symbol,
                            side=self.side,
                            type="LIMIT",
                            price=band_price,
                            workingType="CONTRACT_PRICE",
                            quantity=self.qty,
                            reduceOnly=True,
                            priceProtect=protect,
                            timeInForce="GTC",
                        )
                        self.order_grid.append([band_price, grid_order])
                    except BinanceAPIException as error:
                        print(type(error))
                        print(f"grid_order {i}, ", error)




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
def main():
    gom = GridOrderMaker(client, symbol)
    gom.send_order_grid(symbol, take_profit, qty, side, grid_end)

if __name__=="__main__":
    main()    



# %%
