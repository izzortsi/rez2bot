# %%
import pandas as pd
import pandas_ta as ta
import pandas_bokeh
import pycoingecko as cgk
import os

from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError
from pycoingecko import CoinGeckoAPI
from pycoingecko.utils import *

from pandas import DataFrame as df

# %%


def convert_kwargs(kwargs):
    for k, v in kwargs.items():
        if type(v) is list:
            kwargs[k] = get_comma_separated_values(v)


pd.set_option("plotting.backend", "pandas_bokeh")
pandas_bokeh.output_notebook()
key = os.environ.get("cmc_key")

# %%
cg = CoinGeckoAPI()
cmc = CoinMarketCapAPI(key)

# %%

symbols = ["BTC", "ETH", "SOL"]
# %%
kwargs_cmc = {"symbol": symbols, "convert": "USD", "aux": [
    "cmc_rank", "circulating_supply", "market_cap_by_total_supply", "volume_7d", "volume_30d"]}

# %%
convert_kwargs(kwargs_cmc)
cmc_latest_quotes = cmc.cryptocurrency_quotes_latest(**kwargs_cmc)


# %%


class CMC(CoinMarketCapAPI):
    def __init__(self, key, **kwargs):
        super().__init__(self, api_key=key, **kwargs)
        pass

        # %%
        # basicamente, o que eu posso usar (e é útil):
        # globalmetrics_quotes_latest: convert =
        # cryptocurrency_listings_latest: pra várias coins
        # cryptocurrency_quotes_latest: pra uma coin
        # partners_flipsidecrypto_fcas_listings_latest
        # partners_flipsidecrypto_fcas_quotes_latest
