
# %%
from binance.futures import Futures 
from pandas import DataFrame as DF
import os
import pandas as pd

# %%

client = Futures()
print(pd.to_datetime(client.time()["serverTime"], unit="ms"))

# %%
api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Futures(key=api_key, secret=api_secret)

# %%

print(client.account())

# %%

# Get account information

# Post a new order
params = {
    'symbol': 'BTCUSDT',
    'side': 'SELL',
    'type': 'LIMIT',
    'timeInForce': 'GTC',
    'quantity': 0.002,
    'price': 59808
}

response = client.new_order(**params)
print(response)