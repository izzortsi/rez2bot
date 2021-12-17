# %%
from binance import Client, ThreadedWebsocketManager
from binance.enums import *
import pandas as pd
import os
from threading import Thread


api_key = os.environ.get("API_KEY") 
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)


# %%
#parameters
client
tp
sl
gridstep
last_price
atr_bands
# %%
class OrderHandler(Thread):
    def __init__(self, *args, **kwargs):
        

