import argparse
import pandas_ta as ta
import pandas as pd
import numpy as np

# %%
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--rate", default=1, type=int)
parser.add_argument("-sl", "--stoploss", default=-0.1, type=float)
parser.add_argument("-tp", "--takeprofit", default=6, type=float)
parser.add_argument("-ew", "--entry_window", default=1, type=int)
parser.add_argument("-xw", "--exit_window", default=0, type=int)
parser.add_argument("-L", "--leverage", default=1, type=int)
parser.add_argument("-Q", "--qty", default=1, type=float)
parser.add_argument("-S", "--symbol", default="sandusdt", type=str)
parser.add_argument("-tf", "--timeframe", default="30m", type=str)
parser.add_argument("-s", "--strategy", default=1, type=int)
args = parser.parse_args()

rate = args.rate
tp = args.takeprofit
sl = args.stoploss
leverage = args.leverage
ew = args.entry_window
xw = args.exit_window
is_real = args.is_real
qty = args.qty
symbol = args.symbol
tf = args.timeframe
strategy = args.strategy

# %%

class PullbackStrategy:
    def __init__(
        self,
        name,
        timeframe,
        take_profit,
        stoploss,
        entry_window,
        exit_window,
        macd_params={"fast": 12, "slow": 26, "signal": 9},
    ):
        self.name = name
        self.timeframe = timeframe
        self.stoploss = stoploss
        self.take_profit = take_profit
        self.entry_window = entry_window
        self.exit_window = exit_window
        self.macd_params = macd_params

    def entry_signal(self, trader):
        print((trader.data_window.close.tail(1).values[-1] <= trader.data_window.ci.tail(1).values[-1]))
        if (
            np.alltrue(trader.data_window.close.values[-1] <= trader.data_window.ci.values[-1])
            and (np.alltrue(trader.data_window.histogram.tail(self.entry_window) >= 0))
            and (ta.increasing(trader.data_window.hist_ema, length=self.entry_window))
        ):

            trader.position_type = 1
            return True
        else:
            return False

    def exit_signal(self, trader):

        condition1 = trader.current_percentual_profit >= self.take_profit

        # condition2 = np.alltrue(
        #     trader.data_window.histogram.tail(self.exit_window) > 0)
        check = condition1  # and condition2

        return check

    def stoploss_check(self, trader):

        condition1 = trader.current_percentual_profit <= self.stoploss
        # condition2 = trader.position_type == -trader.ta_handler.signal
        check = condition1 #and condition2

        return check




class ThreadedManager:
    def __init__(self, api_key, api_secret, rate=1, tf="5m"):

        self.client = Client(
            api_key=api_key, api_secret=api_secret, exchange="binance.com-futures"
        )
        self.bwsm = BinanceWebSocketApiManager(
            output_default="UnicornFy", exchange="binance.com-futures"
        )

        self.rate = rate  # debbug purposes. will be removed
        self.tf = tf
        self.traders = {}
        self.ta_handlers = {}

        self.is_monitoring = False

    def start_trader(self, strategy, symbol, leverage=1, is_real=False, qty=0.002):

        trader_name = name_trader(strategy, symbol)

        if trader_name not in self.get_traders():

            handler = ThreadedTAHandler(symbol, [self.tf], self.rate)
            self.ta_handlers[trader_name] = handler

            trader = ThreadedATrader(
                self, trader_name, strategy, symbol, leverage, is_real, qty
            )
            self.traders[trader.name] = trader
            trader.ta_handler = handler
            
            return trader
        else:
            print("Redundant trader. No new thread was created.\n")
            print("Try changing some of the strategy's parameters.\n")

    def get_traders(self):
        return list(self.traders.items())

    def get_ta_handlers(self):
        return list(self.ta_handlers.items())

    def close_traders(self, traders=None):
        """
        fecha todos os traders e todas as posições; pra emerg
        """
        if traders is None:
            # fecha todos os traders
            for name, trader in self.get_traders():
                trader.stop()
            for name, handler in self.get_ta_handlers():
                handler.stop()
                del self.ta_handlers[name]

        else:
            # fecha só os passados como argumento
            pass
        pass

    def stop(self, kill=0):
        self.close_traders()
        self.bwsm.stop_manager_with_all_streams()
        if kill == 0:
            os.sys.exit(0)

    def traders_status(self):
        status_list = [trader.status() for _, trader in self.get_traders()]
        return status_list

    def pcheck(self):
        for name, trader in self.get_traders():
            print(
                f"""
            trader: {trader.name}
            number of trades: {trader.num_trades}
            is positioned? {trader.is_positioned}
            position type: {trader.position_type}
            entry price: {trader.entry_price}
            last price: {trader.last_price}
            TV signals: {[s["RECOMMENDATION"] for s in self.ta_handlers[name].summary]}, {self.ta_handlers[name].signal}
            current percentual profit (unleveraged): {trader.current_percentual_profit}
            cummulative leveraged profit: {trader.cum_profit}
                    """
            )

    def market_overview(self):
        """
        isso aqui pode fazer bastante coisa, na verdade pode ser mais sensato
        fazer uma classe que faça as funções e seja invocada aqui.
        mas, em geral, a idéia é pegar várias métricas de várias coins, algo que
        sugira com clareza o sentimento do mercado. eventualmente, posso realmente
        usar ML ou alguma API pra pegar sentiment analysis do mercado
        """
        pass

    def _monitoring(self, sleep):
        while self.is_monitoring:
            self.pcheck()
            time.sleep(sleep)

    def start_monitoring(self, sleep=5):
        self.is_monitoring = True
        self.monitor = threading.Thread(
            target=self._monitoring,
            args=(sleep,),
        )
        self.monitor.setDaemon(True)
        self.monitor.start()
    
    def sm(self, sleep=5):
        self.start_monitoring(sleep)

    def stop_monitoring(self):
        self.is_monitoring = False