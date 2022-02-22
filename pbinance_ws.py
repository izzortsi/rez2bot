# %%

import time
import os
import json
import pandas as pd
import numpy as np

from binance.streams import ThreadedWebsocketManager
from ring_buffer import RingBuffer

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")

# %%
def to_datetime_tz(arg, timedelta=-pd.Timedelta("03:00:00"), unit="ms", **kwargs):
    """
    to_datetime_tz(arg, timedelta=-pd.Timedelta("03:00:00"), unit="ms", **kwargs)

    Args:
        arg (float): epochtime
        timedelta (pd.Timedelta): timezone correction
        unit (string): unit in which `arg` is
        **kwargs: pd.to_datetime remaining kwargs
    Returns:
    pd.Timestamp: a timestamp corrected by the given timedelta
    """
    ts = pd.to_datetime(arg, unit=unit)
    return ts + timedelta
    
def process_futures_klines(klines):
    # klines = msg["k"]
    klines = pd.DataFrame.from_records(klines, coerce_float=True)
    klines = klines.loc[:, [0, 6, 1, 2, 3, 4, 5]]
    klines.columns = ["init_ts", "end_ts", "open", "high", "low", "close", "volume"]
    # df = pd.DataFrame(klines, columns=["timestamp", "open", "close", "high", "low", "transactionVol","transactionAmt"])
    klines["init_ts"] = klines["init_ts"].apply(to_datetime_tz)
    klines["end_ts"] = klines["end_ts"].apply(to_datetime_tz)
    klines.update(klines.iloc[:, 2:].astype(float))
    return klines

def main():

    symbols = ['BTCUSDT', 'ETHUSDT']
    streams = [f"{symbol.lower()}@miniTicker" for symbol in symbols]
    # streams = ["!ticker@arr"]
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()

    def callback_function(msg):
        # data = msg['data']
        # print(msg)
        data = msg['data']
        symbol = data['s']
        o = data['o']
        h = data['h']
        l = data['l']
        c = data['c']
        v = data['v']
        ohlcv = dict(o=o, h=h, l=l, c=c, v=v)

        print(symbol, json.dumps(ohlcv, indent = 4))

        # for item in msg:
            # print(item)
            # print(f"""event: {item["e"]}
                    # symbol: {item["s"]}
                    # """)
                    # data: {data}
        time.sleep(1)
        
    twm.start_futures_multiplex_socket(callback = callback_function, streams=streams)
        # print(item)

    # twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    # twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    # streams = ['ethusdt@miniTicker', 'btcusdt@miniTicker']
    # twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
    # twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
      
    twm.join()


# %%

if __name__ == "__main__":
   main()
#%%

#%%
