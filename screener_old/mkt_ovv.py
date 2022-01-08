# %%

import numpy as np
import pandas as pd
import pandas_ta as ta
from pandas import DataFrame as df
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()


# %%
coins_mkts = cg.get_coins_markets(vs_currency="usd", order="volume_desc", per_page=200,
                                  page=1, sparkline=True, price_change_percentage=["1h", "24h", "7d"])


# %%
coins_mkts
# %%


def get_filtered_dict(coin_dict):

    symbol = coin_dict["symbol"]

    data_dict = {}
    filtered_dict = {symbol: data_dict}

    circulating_supply = coin_dict['circulating_supply']
    total_supply = coin_dict['total_supply']

    if (total_supply is None or
            total_supply == 0):
        total_supply = circulating_supply

        if total_supply == 0:
            total_supply, circulating_supply = 1, 1

    print(circulating_supply, total_supply)

    supply_ratio = circulating_supply/total_supply

    keys = [
        "current_price",
        'market_cap',
        'market_cap_rank',
        'total_volume',
        'high_24h',
        'low_24h',
        'price_change_percentage_24h',
        'market_cap_change_percentage_24h',
        'supply_ratio',
        'ath',
        'ath_change_percentage',
        'atl',
        'atl_change_percentage',
        'price_change_percentage_1h_in_currency',
        'price_change_percentage_24h_in_currency',
        'price_change_percentage_7d_in_currency',
        'sparkline_in_7d',
    ]

    for key in keys:
        if key == 'supply_ratio':
            data_dict[key] = supply_ratio
        elif key == "sparkline_in_7d":  # sparkline returns a dict of prices
            data_dict["price"] = np.array(coin_dict[key]["price"])
        else:
            data_dict[key] = coin_dict[key]

    return filtered_dict


# %%


def process_request(response):

    coins_data = []

    for coin_dict in response:
        coins_data.append(get_filtered_dict(coin_dict))

    return coins_data


# %%
coins_data = process_request(coins_mkts)

# %%
data_array = np.array([np.array(
    [*[*coin_data.values()][0].values()], dtype=object) for coin_data in coins_data])
# %%

# %%
data_array[0]
# %%

prices_array = np.array([np.array([*coin_data.values()][0]["price"])
                         for coin_data in coins_data], dtype=object)

# %%
prices_array
#%%
