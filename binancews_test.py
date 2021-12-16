
# %%

from binance import Client, ThreadedWebsocketManager
from binance.enums import *
import pandas as pd
import os

# %%

api_key = os.environ.get("API_KEY") 
api_secret = os.environ.get("API_SECRET")
client = Client(api_key, api_secret)




klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Dec, 2021")



dfkl = pd.DataFrame(klines)

dfkl
# %%

# socket manager using threads
twm = ThreadedWebsocketManager()
twm.start()

# %%
data_buffer = []
# depth cache manager using threads

def handle_socket_message(msg):
    # global data_buffer
    data_buffer.append(msg["k"])
    # df = pd.DataFrame.from_dict(msg["k"])
    # print(f"message type: {msg['e']}")
    # print(f"{type(msg['k'])}")
    # print(f"message: {msg['k']}")
    # print(f"message: {df}")


# %%

twm.start_kline_futures_socket(callback = handle_socket_message, symbol="ETHUSDT", interval=KLINE_INTERVAL_1HOUR)
# %%


# twm.start_kline_socket(callback=handle_socket_message, symbol='ETHUSDT')



# %%


# join the threaded managers to the main thread
twm.join()


#%%
