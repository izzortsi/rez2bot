# %%

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import json
import os
import time
import numpy as np

# %%

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)

# %%

serverTimeSecs = client.get_server_time()["serverTime"]
localTimeSecs = time.time()*1000
print(serverTimeSecs) 
print(localTimeSecs)
# %%

print(serverTimeSecs - localTimeSecs)

# %%
def get_filters():
    with open("symbols_filters.json") as f:
        data = json.load(f)
    return data
filters = get_filters()    
#%%


