
# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import json
import os
import time
import numpy as np

# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%

serverTimeSecs = client.get_server_time()["serverTime"]
localTimeSecs = time.time()*1000
print(serverTimeSecs) 
print(localTimeSecs)
# %%

print(serverTimeSecs - localTimeSecs)

# %%
def get_filters():
    with open("symbols_filters.json") as f:
        data = json.load(f)
    return data
filters = get_filters()    
# parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
# parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
# parser.add_argument("-gs", "--grid_step", type=float, default=0.12)

# %%
filters
# %%

side = side
symbol = symbol
grid_end = grid_end
grid_step = grid_step
take_profit = take_profit
qty = quantity
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

def set_price_filters(symbol, client, qty):
    
    if symbol in filters.keys():
        format = filters[symbol]
        qty_precision = int(format["quantityPrecision"])
        price_precision = int(format["pricePrecision"])
        # print(qty_precision)
        # print(price_precision)
        notional = 5
        min_qty = 1 / 10 ** qty_precision
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker["price"])
        multiplier = qty * np.ceil(notional / (price * min_qty))
        # f"{float(value):.{decimal_count}f}"
        qty = f"{float(multiplier*min_qty):.{qty_precision}f}"
        price_formatter = lambda x: f"{float(x):.{price_precision-1}f}"
        return price_formatter, qty
        print(min_qty)
        print(qty)
        print(price_formatter(price))    


def send_order_grid(symbol, tp, qty, side, ge, price_formatter, protect=False, sl=None):
    if side == -1:
        side = "SELL"
        counterside = "BUY"
    elif side == 1:
        side = "BUY"
        counterside = "SELL"
    grid_end = ge        
    # grid_coefs = np.arange(gr[0], gr[1], gs)

    position = client.futures_position_information(symbol=symbol)
    entry_price = float(position[0]["entryPrice"])
    qty = position[0]["positionAmt"]
    price_grid = np.geomspace(entry_price, grid_end, num=5, dtype=float)
    
    # tp_price = f_tp_price(price, tp, lev, side=side)
    # sl_price = f_sl_price(price, sl, lev, side=side)
    tp_price = price_formatter(
        compute_exit(entry_price, tp, side=side)
    )
    print(
        f"""price: {entry_price}
              tp_price: {tp_price}
              """
    )


if __name__ == "__main__":
    api_key = os.environ.get("API_KEY")
    api_secret = os.environ.get("API_SECRET")
    client = Client(api_key, api_secret)
    price_formatter, qty = set_price_filters(symbol, client, qty)
    send_order_grid(symbol, take_profit, qty, side, grid_end, price_formatter)
    