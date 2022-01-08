# %%
import coinmarketcap as cmc
import pycoingecko as cgk
from unicorn_binance_rest_api.unicorn_binance_rest_api_manager import (
    BinanceRestApiManager,
)
import os

# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")

# %%

client = BinanceRestApiManager(api_key, api_secret, exchange="binance.com-futures")
# get market depth
depth = client.get_order_book(symbol="BNBBTC")
print(f"{depth}")

# get all symbol prices
prices = client.get_all_tickers()
print(f"{prices}")


# %%
