
# %%

from ast import Call
from subprocess import call
import time
import os

from binance.streams import ThreadedWebsocketManager

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
# client = Client(api_key, api_secret)

# %%

def main():

    symbol = 'BNBBTC'

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()

    def handle_socket_message(msg):
        print(f"message type: {msg['e']}")
        print(msg)

    twm.futures_user_socket()
    # twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    # twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    # streams = ['bnbbtc@miniTicker', 'bnbbtc@bookTicker']
    # twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

    twm.join()


# %%
twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
def handle_socket_message(msg):
    print(f"message type: {msg['e']}")
    print(msg)

# %%

twm.start_futures_socket(callback=handle_socket_message)
# %%

twm.futures_user_socket()

# %%
twm.is_alive()
# %%

if __name__ == "__main__":
   main()
#%%
