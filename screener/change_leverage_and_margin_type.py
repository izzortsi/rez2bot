
# %%

import json
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import os

# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%
with open("symbols_filters.json") as f:
    filters = json.load(f)
#%%

symbols = list(filters.keys())
#%%
# symbol=symbols[0]
# client.futures_change_leverage(symbol=symbol, leverage=17)
# client.futures_change_margin_type(symbol=symbol, marginType="ISOLATED")
# %%

for symbol in symbols:
    client.futures_change_leverage(symbol=symbol, leverage=17)

    try:
        client.futures_change_margin_type(symbol=symbol, marginType="ISOLATED")
    except BinanceAPIException as e:
        print(e)
    
    positionInfo = client.futures_position_information(symbol=symbol)[0]
    print(f"""{positionInfo['symbol']}:
    margin type: {positionInfo['marginType']}
    leverage: {positionInfo['leverage']}""") 


    
    
#%%
