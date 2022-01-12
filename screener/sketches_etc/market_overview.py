
# %%
import numpy as np
import pandas as pd
import os
from pycoingecko import CoinGeckoAPI
from sklearn import preprocessing

# %%
cg = CoinGeckoAPI()

if not os.path.exists("symbols_imgs"):
    os.mkdir("symbols_imgs")

img_path = os.path.join(os.getcwd(), "symbols_imgs")
markets = cg.get_coins_markets(
    "usd", per_page=100, page=1, sparkline=True, price_change_percent="1h,24h,7d"
)
mcap_btc = 0
def process_market_data(data):
    global mcap_btc
    sd = {}
    derived_sd = {}
    rows = []
    for symbol in data:
        s = symbol["symbol"]
        if s == "btc":
            mcap_btc = symbol["market_cap"]
        img = symbol["image"]
        mcap = symbol["market_cap"]
        vol = symbol["total_volume"]
        price = symbol["current_price"]
        price_change = symbol["price_change_percentage_24h"]
        mcap_change = symbol["market_cap_change_percentage_24h"]
        high_24 = symbol["high_24h"]
        low_24 = symbol["low_24h"]
        sd[s] = [mcap, vol, price_change, mcap_change]
        derived_sd[s] = [s, mcap/mcap_btc,  100*vol / mcap, mcap_change, price_change]
        df = pd.DataFrame([[s, mcap, price, vol, 100*mcap/mcap_btc, 100*vol /mcap, mcap_change, price_change, high_24, low_24, 
        (price-low_24)/(high_24-low_24), 100*(high_24/low_24 - 1), 100*(high_24-low_24)/price]], columns=["symbol", "mcap", "price", "vol", "mcap_to_btc", "vol_mcap", "mcap_change", "price_change", "high_24", "low_24", "price_pos", "absolute_volatility", "relative_volatility"])
        rows.append(df)

    return sd, derived_sd, rows

# %%
markets


# %%

# %%
sd, derived_sd, rows = process_market_data(markets)

names = np.array(list(sd.keys()))
sdarray = np.array(list(sd.values()))
dsd = np.array(list(derived_sd.values()))
# dsd = list(derived_sd.values())

# %%
df = pd.concat(rows, axis=0)
df.reset_index(drop=True, inplace=True)

# %%
symbols = df.symbol


# %%

df

# %%

# %%
# ndf = ((df - df.mean()) / df.std())

# # ndf.symbol = symbols
# ndf = df.drop(["symbol"], axis=1)

# # %%
# ndf

# # %%

# ndf = (ndf - ndf.min()) / (ndf.max() - ndf.min())
# # ndf.drop(["symbol"], axis=1, inplace=True)
# # %%
# ndf.mcap + abs(ndf.mcap.min())
# # %%
# ndf.mcap = ndf.mcap 
# # %%
# ndf.mcap
# # %%
# ndf["symbol"] = symbols

# # %%
# ndf
# %%
# df["color"] = df.apply(lambda x: "red" if x["price_change"] < 0 else "green", axis=1)
# df["color"] = (df.price_change - df.price_change.min())/df.price_change.max()
df["minmax_price_change"] = (df.price_change - df.price_change.min())/(df.price_change.max() - df.price_change.min())

# %%
df.price_change.min()

# %%

df.price_change.max()
# %%

df.minmax_price_change
# %%

import plotly.express as px


# %%

# fig = px.scatter_3d(df, x='absolute_volatility', y='vol_mcap', z="price_pos", color="color", size='mcap_to_btc', hover_name="symbol", max_size=60, log_x = True, log_y =True, log_z=True)

# %%
fig = px.scatter(df, x='absolute_volatility', y='vol_mcap', color="minmax_price_change", size='mcap_to_btc', hover_name="symbol", hover_data=["price_change", "price_pos"], log_x = True, log_y =True)

# %%

fig.show()
#%%

#%%

#%%
df.price_change
#%%
import tradingview_ta as tv
#%%
tv.get_multiple_analysis
analysis = tv.get_multiple_analysis(screener="crypto", interval=Interval.INTERVAL_1_HOUR, symbols=["nasdaq:tsla", "nyse:docn", "nasdaq:aapl"])

