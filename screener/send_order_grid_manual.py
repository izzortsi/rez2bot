# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import json
import os
import numpy as np
import pandas as pd
import argparse


api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)
# is_positioned = False
# %%

# symbol = "DUSKUSDT"
# side = -1
# tp = 0.8
# leverage = 17
# qty = 1.1

# %%



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
    min_qty = float(filters["minQty"])
    step_size = float(filters["tickSize"])
    print("price_precision", price_precision, "qty_precision", qty_precision, "min_qty", min_qty, "step_size", step_size)
    minNotional = 5
    min_qty = max(minNotional/base_price, min_qty)
    print("minqty:", min_qty)
    order_size = qty * min_qty
    print("ordersize", order_size)

    return price_precision, qty_precision, min_qty, order_size, step_size

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



def send_order_grid(client, symbol, tp, side, ge, gs=0.16, protect=False, sl=None, is_positioned=False):
    
    if side == -1:
        side = "SELL"
        counterside = "BUY"
    elif side == 1:
        side = "BUY"
        counterside = "SELL"


    filters = get_filters()
    symbolFilters = filters[symbol]
    
    base_price = float(stats_24h["lowPrice"])
    price_precision, qty_precision, min_qty, order_size, step_size = apply_symbol_filters(symbolFilters, base_price, qty=qty)
    
    qty_formatter = lambda ordersize, qty_precision: f"{float(ordersize):.{qty_precision}f}"
    price_formatter = lambda price, price_precision: f"{float(price):.{price_precision}f}"
    
    formatted_order_size = qty_formatter(order_size, qty_precision)
    

    try:
        new_position = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=formatted_order_size,
            priceProtect=False,
            workingType="CONTRACT_PRICE",
        )
        print(new_position)    
    except BinanceAPIException as error:
        print("positioning, ", error)    

        
    position = client.futures_position_information(symbol=symbol)
    entry_price = float(position[0]["entryPrice"])
    mark_price = float(position[0]["markPrice"])
    position_qty = abs(float(position[0]["positionAmt"]))
    print(json.dumps(position[0], indent=2))
    #the grid
    grid_width = abs(ge - entry_price)
    print("grid_width", grid_width)
    price_step = grid_width*gs
    print("grid_width*gs", price_step)
    print("stepsize*markprice", 1.2*step_size*mark_price)
    price_step = max(price_step, 1.2*step_size*mark_price)
    print("price_step: ", price_step)
    make_grid = lambda ep, w, s, side: np.arange(start=ep, stop=ep+w, step=s) if side == "SELL" else np.arange(start=ep, stop=ep-w, step=-s)
    grid_entries = make_grid(entry_price, grid_width, price_step, side)
    # grid_entries = np.arange(start=entry_price, stop=entry_price + grid_width, step=price_step)
    exit_price = (1+tp/100)*entry_price if side == "BUY" else (1-tp/100)*entry_price
    # grid_entries = np.arange(start=1, stop=1+gs, step=gs)
    grid_orders = []
    
    print(f"""
    ge = {grid_entries}
    gw = {grid_width}
    ps = {price_step}
    exit = {exit_price}
    """)

    

    for i, entry in enumerate(grid_entries):
        if ge == 0.0:
            break
        formatted_grid_entry_price = price_formatter(entry, price_precision)
        
        formatted_grid_exit_price = price_formatter(exit_price, price_precision)
        print(formatted_grid_entry_price)
        print(formatted_grid_exit_price)
        try:
            grid_order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            price=formatted_grid_entry_price,
            workingType="CONTRACT_PRICE",
            quantity=formatted_order_size,
            reduceOnly=False,
            priceProtect=False,
            timeInForce="GTC",
            # newOrderRespType="RESULT",
            )
            grid_orders.append(grid_order)
            try:
                grid_order_tp = client.futures_create_order(
                symbol=symbol,
                side=counterside,
                type="TAKE_PROFIT",
                stopPrice = formatted_grid_exit_price,
                price=formatted_grid_exit_price,
                workingType="CONTRACT_PRICE",
                quantity=formatted_order_size,
                reduceOnly=True,
                priceProtect=False,
                timeInForce="GTC",
                # newOrderRespType="RESULT",
                )        
            except BinanceAPIException as error:
                print(f"grid order tp {i}, ", error)    
        except BinanceAPIException as error:
            print(f"grid order {i}, ", error)
    avg_entry = sum(grid_entries)/len(grid_entries)
    max_position_amount = len(grid_entries)*order_size
    formatted_max_order_size = qty_formatter(max_position_amount, qty_precision)
    grid_tp_price = price_formatter(
        compute_exit(avg_entry, tp, side=side),
        price_precision,
    )
    formatted_tp_price = price_formatter(
        compute_exit(entry_price, tp, side=side),
        price_precision,
    )
    grid_stop_price = price_formatter(
        compute_exit(avg_entry, tp*0.9, side=side),
        price_precision,
    )
    print(
        f"""price: {entry_price}
            tp_price: {grid_tp_price}
            """
    )
    print(
        f"""price: {entry_price}
            tp_price: {grid_stop_price}
            """
    )
    print(
        f"""price: {entry_price}
            grid_tp_price: {grid_tp_price}
            grid_stop_price: {grid_stop_price}
            tp_price: {formatted_tp_price}
            """
    )
    try:
        # tp_order = client.futures_create_order(
        #     symbol=symbol,
        #     side=counterside,
        #     type="TAKE_PROFIT",
        #     price=grid_tp_price,
        #     stopPrice=grid_stop_price,
        #     workingType="CONTRACT_PRICE",
        #     quantity=formatted_max_order_size,
        #     reduceOnly=True,
        #     priceProtect=False,
        #     timeInForce="GTC",
        # )
        tp_order_mkt = client.futures_create_order(
            symbol=symbol,
            side=counterside,
            type="TAKE_PROFIT_MARKET",
            stopPrice=formatted_tp_price,
            closePosition=True, 
            workingType="CONTRACT_PRICE",
            priceProtect=False,
            timeInForce="GTC",
        )    
    except BinanceAPIException as error:
        print(f"take profit order, ", error)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--symbol", type=str)
    parser.add_argument("-side", "--side", type=int)
    parser.add_argument("-ge", "--grid_end", type=float, default=0.0)
    parser.add_argument("-gs", "--grid_step", type=float, default=0.16)
    parser.add_argument("-tp", "--take_profit", type=float, default=0.33)
    parser.add_argument("-sl", "--stop_loss", type=float, default=0.33)
    parser.add_argument("-q", "--quantity", type=float, default=1.1)
    parser.add_argument("-lev", "--leverage", type=int, default=17)
    parser.add_argument("--is_positioned", type=bool)
    # parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
    # parser.add_argument("-gr", "--grid_range", nargs=2, type=float)
    # parser.add_argument("-gs", "--grid_step", type=float, default=0.12)
    args = parser.parse_args()

    side = args.side
    symbol = args.symbol
    ge = args.grid_end
    gs = args.grid_step
    tp = args.take_profit
    sl = args.stop_loss
    leverage =args.leverage
    is_positioned = args.is_positioned
    qty = args.quantity

    stats_24h = client.futures_ticker(symbol=symbol)
    print(args)
    print("is_positioned:", is_positioned)
    is_positioned = False
    send_order_grid(client, symbol, tp, side, ge, gs=gs, protect=False, sl=sl, is_positioned=is_positioned)
    