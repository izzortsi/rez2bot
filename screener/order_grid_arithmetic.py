# %%

from binance.um_futures import UMFutures as Client
from binance.api import *
from helpers import round_step_size
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



def send_arithmetic_order_grid(client, symbol, inf_grid, sup_grid, tp, side, qty=1.1, sl=None, ag=False, protect=False, is_positioned=False):
    # print(inf_grid)
    if ag:
        if side == 1:
            ge = inf_grid[-1].values[-1]
            base_price = inf_grid[-1].values[0]
            print(ge)
            
        elif side == -1:
            ge = sup_grid[-1].values[-1]
            base_price = sup_grid[-1].values[0]
            print(ge)
    else:
        grid_entries = [band.values[-1] for band in inf_grid] if side == 1 else [band.values[-1] for band in sup_grid]
        base_price = grid_entries[0]

    if side == -1:
        side = "SELL"
        counterside = "BUY"
    elif side == 1:
        side = "BUY"
        counterside = "SELL"
    
    filters = get_filters()
    symbolFilters = filters[symbol]
    # inf_grid
    
    # print(inf_grid[:, -1])
    
    price_precision, qty_precision, min_qty, order_size, step_size = apply_symbol_filters(symbolFilters, base_price, qty=qty)
    
    qty_formatter = lambda ordersize, qty_precision: f"{float(ordersize):.{qty_precision}f}"
    price_formatter = lambda price, price_precision: f"{float(price):.{price_precision}f}"
    
    formatted_order_size = qty_formatter(order_size, qty_precision)
    print(formatted_order_size)

    try:
        new_position = client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=formatted_order_size,
            priceProtect=False,
            workingType="CONTRACT_PRICE",
        )
            
    except BinanceAPIException as error:
        print("positioning, ", error)    
    else:
        position = client.futures_position_information(symbol=symbol)
        entry_price = float(position[0]["entryPrice"])
        mark_price = float(position[0]["markPrice"])
        position_qty = abs(float(position[0]["positionAmt"]))
        print(json.dumps(position[0], indent=2))
        #the grid
        if ag:
            grid_width = abs(ge - entry_price)
            print("grid_width", grid_width)
            price_step = grid_width*0.1
            print("grid_width*gs", price_step)
            print("stepsize*markprice", 1.5*step_size*mark_price)
            price_step = max(price_step, 1.1*step_size*mark_price)
            print("price_step: ", price_step)
            make_grid = lambda ep, w, s, side: np.arange(start=ep, stop=ep+w, step=s) if side == "SELL" else np.arange(start=ep, stop=ep-w, step=-s)
            grid_entries = make_grid(entry_price, grid_width, price_step, side)
            # grid_entries = np.arange(start=entry_price, stop=entry_price + grid_width, step=price_step)
        
        # print(grid_entries)
        grid_orders = []
        
        print(f"""
        grid_entries = {grid_entries}
        """)
        # gw = {grid_width}
        # ps = {price_step}
        
        for i, entry in enumerate(grid_entries):
            if i == 0:
                band_diff = abs(entry - entry_price) 
            else:
                band_diff = abs(entry - grid_entries[i-1]) 
            price_step = max(band_diff, 1.1*step_size*(entry+entry_price)/2)
            entry = min(entry, mark_price+price_step)
            formatted_grid_entry_price = price_formatter(entry, price_precision)

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
            except BinanceAPIException as error:
                print(f"grid order {i}, ", error)

        formatted_tp_price = price_formatter(
            compute_exit(entry_price, tp, side=side),
            price_precision,
        )


        print(
            f"""price: {entry_price}

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
        finally:
            if sl is not None:
                formatted_sl_price = price_formatter(
                    compute_exit(entry_price, sl, side=counterside),
                    price_precision,
                )
                print(formatted_sl_price)
                try:
                    sl_order_mkt = client.futures_create_order(
                        symbol=symbol,
                        side=counterside,
                        type="STOP_MARKET",
                        stopPrice=formatted_sl_price,
                        closePosition=True, 
                        workingType="CONTRACT_PRICE",
                        priceProtect=False,
                        timeInForce="GTC",
                    )    
                except BinanceAPIException as error:
                    print(f"stop loss order, ", error)

#%%
