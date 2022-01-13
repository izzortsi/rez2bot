# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import json
import os
import time
import numpy as np
import pandas as pd
# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%
symbol = "DUSKUSDT"
side = 1
leverage = 17
tp = 0.33


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


# %%
new_position = client.futures_create_order(
        symbol=symbol,
        side="BUY",
        type="MARKET",
        quantity=formatted_order_size,
        priceProtect=False,
        workingType="CONTRACT_PRICE",
)
