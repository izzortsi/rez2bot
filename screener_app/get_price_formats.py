
# %%

import json
from binance import Client
import os
from symbols_formats import FORMATS
# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%
FORMATS
#%%
