# %%

from binance import Client, ThreadedWebsocketManager
from binance.enums import *
import pandas as pd
import os
import time
from threading import Thread


api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)
symbol = "ADAUSDT"
# %%
t0=pd.to_datetime(client.futures_time()["serverTime"], unit="ms")
t1=pd.to_datetime(time.time(), unit="s")
tdelta = t0 - t1
# %%
tdelta
# %%
# client.get_account_snapshot(type='FUTURES', recvWindow=37000)
# position_info = client.futures_position_information(symbol="ADAUSDT", recvWindow=37000)
acc_info = client.futures_account()
position_info = client.futures_position_information(symbol="ADAUSDT")
# %%
print(position_info)
# %%

order = client.create_test_order(
    symbol='BNBBTC',
    side=Client.SIDE_BUY,
    type=Client.ORDER_TYPE_MARKET,
    quantity=100)
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
