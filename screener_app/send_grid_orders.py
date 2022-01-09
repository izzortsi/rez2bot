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

def set_price_formats(symbol, client, qty):
    
    if symbol in FORMATS.keys():
        format = FORMATS[symbol]
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
    if side == "SELL":
        side = "SELL"
        counterside = "BUY"
    elif side == "BUY":
        side = "BUY"
        counterside = "SELL"
    grid_end = ge        
    # grid_coefs = np.arange(gr[0], gr[1], gs)
    
    try:
        new_position = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty,
            priceProtect=protect,
            workingType="CONTRACT_PRICE",
        )
    except BinanceAPIException as error:
        print(type(error))
        print("positioning, ", error)
    else:
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
    