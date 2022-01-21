
# %%

import json
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import os
import argparse


# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

def change_leverage_and_margin(leverage, margin_type="ISOLATED"):

    with open("symbols_filters.json") as f:
        filters = json.load(f)
    #%%

    symbols = list(filters.keys())
    #%%
    # symbol=symbols[0]
    # client.futures_change_leverage(symbol=symbol, leverage=30)
    # client.futures_change_margin_type(symbol=symbol, marginType="ISOLATED")
    # %%

    for symbol in symbols:

        try:
            client.futures_change_leverage(symbol=symbol, leverage=leverage)
        except BinanceAPIException as e:
            print(e)

        try:
            client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
        except BinanceAPIException as e:
            print(e)
        
        positionInfo = client.futures_position_information(symbol=symbol)[0]
        print(f"""{positionInfo['symbol']}:
        margin type: {positionInfo['marginType']}
        leverage: {positionInfo['leverage']}""") 


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-L", "--leverage", type=int, default=17)
    parser.add_argument("-mt", "--margin_type", type=str, default="ISOLATED")
    args = parser.parse_args()
    leverage = args.leverage
    margin_type = args.margin_type
    change_leverage_and_margin(leverage, margin_type = margin_type)

    
    
#%%
