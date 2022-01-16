# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
from binance.helpers import round_step_size
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



def send_order_grid(client, symbol, inf_grid, sup_grid, tp, side, coefs, qty=1.1, sl=None, protect=False, is_positioned=False):
    # print(inf_grid)
    
    grid_entries = [band.values[-1] for band in inf_grid] if side == 1 else [band.values[-1] for band in sup_grid]

    if side == -1:
        side = "SELL"
        counterside = "BUY"
    elif side == 1:
        side = "BUY"
        counterside = "SELL"
    print(grid_entries)
    filters = get_filters()
    symbolFilters = filters[symbol]
    # inf_grid
    
    # print(inf_grid[:, -1])
    base_price = grid_entries[0]
    price_precision, qty_precision, min_qty, order_size, step_size = apply_symbol_filters(symbolFilters, base_price, qty=qty)
    
    qty_formatter = lambda ordersize, qty_precision: f"{float(ordersize):.{qty_precision}f}"
    # price_formatter = lambda price, price_precision: f"{float(price):.{price_precision}f}"
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
            
    except BinanceAPIException as error:
        
        print("positioning, ", error)    
        if error.code == -2019:
            return "stop"
    else:
        position = client.futures_position_information(symbol=symbol)
        entry_price = float(position[0]["entryPrice"])
        mark_price = float(position[0]["markPrice"])
        position_qty = abs(float(position[0]["positionAmt"]))
        print(json.dumps(position[0], indent=2))
        #the grid
        # grid_width = abs(ge - entry_price)
        # print("grid_width", grid_width)
        # price_step = grid_width*gs
        # print("grid_width*gs", price_step)
        # print("stepsize*markprice", 1.5*step_size*mark_price)
        # price_step = max(price_step, 1.5*step_size*mark_price)
        # print("price_step: ", price_step)
       
       
        # grid_entries = np.arange(start=1, stop=1+gs, step=gs)
        grid_orders = []
        
        print(f"""
        ge = {grid_entries}
        """)
        # gw = {grid_width}
        # ps = {price_step}
        
        for i, entry in enumerate(grid_entries):
            if i == 0:
                band_diff = abs(entry - entry_price) 
            else:
                band_diff = abs(entry - grid_entries[i-1]) 
            # price_step = max(band_diff, 1.1*step_size*(entry+entry_price)/2)
            # entry = max(entry, mark_price+price_step)
            entry = round_step_size(entry, step_size)
            print(entry)
            formatted_grid_entry_price = price_formatter(entry, price_precision)
            formatted_order_size = qty_formatter(order_size*coefs[i], qty_precision)
            print(formatted_grid_entry_price)
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
        
        exit_price = round_step_size(
                        compute_exit(entry_price, tp, side=side), 
                        step_size
                        )

        formatted_tp_price = price_formatter(
            exit_price,
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
                exit_price = round_step_size(
                    compute_exit(grid_entries[-1], sl, side=counterside), 
                    step_size
                )
                formatted_sl_price = price_formatter(
                    exit_price,
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
