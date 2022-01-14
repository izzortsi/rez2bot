# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import json
import os
import time
import numpy as np
import pandas as pd
import argparse
# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%




parser = argparse.ArgumentParser()

parser.add_argument("-s", "--symbol", type=str)
parser.add_argument("-side", "--side", type=int)
parser.add_argument("-ge", "--grid_end", type=float, default=None)
parser.add_argument("-gs", "--grid_step", type=float, default=0.16)
parser.add_argument("-tp", "--take_profit", type=float, default=0.33)
parser.add_argument("-q", "--quantity", type=int, default=1)
parser.add_argument("-lev", "--leverage", type=int, default=20)
# parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
# parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
# parser.add_argument("-gs", "--grid_step", type=float, default=0.12)
args = parser.parse_args()
side = args.side
symbol = args.symbol
grid_end = args.grid_end
grid_step = args.grid_step
tp = args.take_profit
leverage =args.leverage
qty = args.quantity

# %%
tp*leverage

# %%
qty_formatter = lambda ordersize, qty_precision: f"{float(ordersize):.{qty_precision}f}"
price_formatter = lambda price, price_precision: f"{float(price):.{price_precision}f}"

def get_filters():
    with open("symbols_filters.json") as f:
        data = json.load(f)
    return data
def process_all_stats(all_stats):
    perps = [pd.DataFrame.from_records([symbol_data]) for symbol_data in all_stats]
    return perps

def apply_symbol_filters(filters, base_price, qty=1.1):
    
    price_precision = int(filters["pricePrecision"])    
    qty_precision = int(filters["quantityPrecision"])

    minNotional = 5
    min_qty = minNotional/base_price
    order_size = qty * min_qty

    return price_precision, qty_precision, min_qty, order_size

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

def send_order_grid(symbol, tp, side, price_formatter, protect=False, sl=None):
    if side == -1:
        side = "SELL"
        counterside = "BUY"
    elif side == 1:
        side = "BUY"
        counterside = "SELL"

    position = client.futures_position_information(symbol=symbol)
    entry_price = float(position[0]["entryPrice"])
    qty = position[0]["positionAmt"]
        
    tp_price = price_formatter(
        compute_exit(entry_price, tp, side=side)
    )
    print(
        f"""price: {entry_price}
              tp_price: {tp_price}
              """
    )

# %%

filters = get_filters()


symbolFilters = filters[symbol]
print(symbolFilters)

stats_24h = client.futures_ticker(symbol=symbol)

base_price = float(stats_24h["lowPrice"])

# %%
price_precision, qty_precision, min_qty, order_size = apply_symbol_filters(symbolFilters, base_price, qty=1.1)
# filtered_stuff = apply_symbol_filters(symbolFilters, base_price, qty=1.1)
# filtered_stuff
print(min_qty, np.ceil(min_qty))

# %%
formatted_order_size = qty_formatter(order_size, qty_precision)
formatted_order_size
# %%


#%%


# %%
position = client.futures_position_information(symbol=symbol)
entry_price = float(position[0]["entryPrice"])
position_qty = position[0]["positionAmt"]
print(json.dumps(position[0], indent=2))
# %%

if side == -1:
    side = "SELL"
    counterside = "BUY"
elif side == 1:
    side = "BUY"
    counterside = "SELL"

tp_price = price_formatter(
    compute_exit(entry_price, tp, side=side),
    price_precision,
)
print(
    f"""price: {entry_price}
          tp_price: {tp_price}
          """
)

# %%
maxQty = 11*min_qty

# %%

formatted_qty = qty_formatter(maxQty, qty_precision)
# %%
formatted_qty, tp_price
# %%



# %%
new_position = client.futures_create_order(
        symbol=symbol,
        side="BUY",
        type="MARKET",
        quantity=formatted_order_size,
        priceProtect=False,
        workingType="CONTRACT_PRICE",
)

#%%
try:
    tp_order = client.futures_create_order(
        symbol=symbol,
        side=counterside,
        type="LIMIT",
        price=tp_price,
        workingType="CONTRACT_PRICE",
        quantity=formatted_qty,
        reduceOnly=True,
        priceProtect=False,
        timeInForce="GTC",
    )
except BinanceAPIException as error:
    print("tp order, ", error)

#%%


    


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
    price_formatter, qty = set_price_formats(symbol, client, qty)
    send_order_grid(symbol, take_profit, qty, side, grid_end, price_formatter)
    