# %%
import pandas as pd
import pandas_ta as ta
import pandas_bokeh

from pandas import DataFrame as df
from pycoingecko import CoinGeckoAPI

# %%
pd.set_option("plotting.backend", "pandas_bokeh")
pandas_bokeh.output_notebook()
# %%

cg = CoinGeckoAPI()

# %%
# interesting functions about coins in general:

# cg.get_coins_markets()
# cg.get_coin_market_chart_by_id()
# cg.get_coin_market_chart_range_by_id()
# cg.get_coin_ohlc_by_id()

# exchanges info
# cg.get_exchanges_by_id()
# cg.get_exchanges_status_updates_by_id()
# cg.get_exchanges_volume_chart_by_id()
# cg.get_derivatives_exchanges_by_id() - futures

# cg.get_search_trending() 7 tranding coins in coingecko
# cg.get_global() some global metrics

# =======

# simple examples
# /simple/price endpoint with the required parameters
# cg.get_price(ids="bitcoin", vs_currencies="usd")


# cg.get_price(ids="bitcoin,litecoin,ethereum", vs_currencies="usd")
# OR (lists can be used for multiple-valued arguments)
# and also optional parameters can be passed as defined in the API doc (https://www.coingecko.com/api/docs/v3)
# %%


data = cg.get_price(
    ids=["bitcoin", "litecoin", "ethereum"],
    vs_currencies="usd",
    include_market_cap="true",
    include_24hr_vol="true",
    include_24hr_change="true",
    include_last_updated_at="true",
)


datadf = df.from_dict(data)

# %%

datadf.loc["last_updated_at"] = pd.to_datetime(
    datadf.loc["last_updated_at"], unit="s")
# datadf.drop("last_updated_at", inplace=True)

# %%


# %%
datadf


# %%
