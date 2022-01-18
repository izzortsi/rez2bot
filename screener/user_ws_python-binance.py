
# %%

import time

from binance.streams import ThreadedWebsocketManager
from binance.streams import BinanceSocketManager
from auxiliary_functions import api_key, api_secret, client


#%%
def user_ws_callback(msg):
    print(msg["e"])
    if msg["e"] == "ORDER_TRADE_UPDATE":

        order_data = msg["o"]

        symbol = order_data["s"]
        order_type = order_data["ot"]

        order_status = order_data["X"]

        # position_amount = order_data["p"]
        if (order_status == 'PARTIALLY_FILLED'
            or order_status == 'FILLED'):
            print(symbol, order_status)
    elif msg["e"] == "ACCOUNT_UPDATE":
        if msg["a"]["m"] == "ORDER":
            msg_data = msg["a"]
            positions_data = msg_data["P"]
            for position_data in positions_data:
                print(f"""{position_data["s"]}
                    amount: {position_data["pa"]}
                    entry price: {position_data["ep"]}""")
        else:
            print(msg["a"]["m"])
            # symbol = order_data["s"]
        # symbol = order_data["S"]

# %%

twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
twm.start()

# twm.start_futures_socket(callback=lambda msg: print("twm's got a message:", msg))
twm.start_futures_socket(callback=user_ws_callback)

#%%
