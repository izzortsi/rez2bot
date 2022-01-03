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

# order = client.create_test_order(
#     symbol='BNBBTC',
#     side=Client.SIDE_BUY,
#     type=Client.ORDER_TYPE_MARKET,
#     quantity=100)
# %%
#parameters
# client
# tp
# sl
# gridstep
# last_price
# atr_bands
# %%
class OrderHandler(Thread):
    def __init__(self, *args, **kwargs):
        self.client = args[0]
        self.symbol = args[1]
        self.take_profit = args[2]
        self.stop_loss = args[3]
        self.gridstep = args[4]
        self.last_price = args[5]
        self.atr_bands = args[6]
        self.qty = args[7]
        self.logger = args[8]
        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.tp_price = None
        self.exit_price = None
        self.exit_time = None
        self.tp_order = None
        self.closing_order = None
        self.price_formatter = args[9]
        self.side = None
        self._update_(**kwargs)
    
    def send_orders(self, signal, symbol, protect=False):

            if signal == -1:
                side = "SELL"
                counterside = "BUY"
            elif signal == 1:
                side = "BUY"
                counterside = "SELL"

            try:
                new_position = client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type="MARKET",
                    quantity=self.qty,
                    priceProtect=protect,
                    workingType="CONTRACT_PRICE",
                )

            except BinanceAPIException as error:
                print(type(error))
                print("positioning, ", error)
            else:
                self.position = self.client.futures_position_information(
                    symbol=symbol
                )[-1]
                print(self.position)
                self.entry_price = float(self.position["entryPrice"])
                self.entry_time = to_datetime_tz(self.position["updateTime"], unit="ms")
                # self.qty = self.position[0]["positionAmt"]
                self.tp_price = compute_exit(self.entry_price, self.take_profit, side=side)
                self.logger.info(
                    f"ENTRY: E:{self.entry_price} at t:{self.entry_time}; type: {signal}"
                )
                tp_price = self.price_formatter(self.tp_price)
                print(tp_price)
                try:
                    self.tp_order = self.client.futures_create_order(
                        symbol=self.symbol,
                        side=counterside,
                        type="LIMIT",
                        price=tp_price,
                        workingType="CONTRACT_PRICE",
                        quantity=self.qty,
                        reduceOnly=True,
                        priceProtect=protect,
                        timeInForce="GTC",
                    )
                except BinanceAPIException as error:

                    print("tp order, ", error)

        def _close_position(self):
            _, counterside = self._side_from_int()
            self.closing_order = self.client.futures_create_order(
                symbol=self.symbol,
                side=counterside,
                type="MARKET",
                workingType="MARK_PRICE",
                quantity=self.qty,
                reduceOnly=True,
                priceProtect=False,
                newOrderRespType="RESULT",
            )
            if self.closing_order["status"] == "FILLED":
                self.exit_price = float(self.closing_order["avgPrice"])
                self.exit_time = to_datetime_tz(self.closing_order["updateTime"], unit="ms")

!!

!!

!!

!!

!!

!!

!!
