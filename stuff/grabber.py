##
import pandas as pd
import pandas_ta as ta

##
class Grabber:
    def __init__(self, client):
        self.client = client
        self.klines = {}
        self.ohlcvs = {}

    """
    def get_data(
    symbol="BTCUSDT", tframe="1h", limit=None, startTime=None, endTime=None
    )
    """
    def get_historical_ohlcv(
        self, symbol="BTCUSDT", tframe="1h", limit=None, startTime=None, endTime=None
    ):

        self.klines[symbol] = self.client.get_historical_klines(
            symbol,
            tframe,
            startTime,
            endTime,
        )
        self.trim_ohlcv(symbol)
        # replaced_fromdate = fromdate.replace(" ", "-")

    def trim_ohlcv(self, symbol):
      kldata = self.klines[symbol]
      df = pd.DataFrame(data=kldata)
    
      dohlcv = df.iloc[:, [0, 1, 2, 3, 4, 5]]
      dohlcv[0] = pd.to_datetime(dohlcv[0], unit="ms")
      dohlcv.columns = ["date", "open", "high", "low", "close", "volume"]
    
      ohlcv = dohlcv.iloc[:, [1, 2, 3, 4, 5]]
      ohlcv.set_index(pd.DatetimeIndex(dohlcv["date"]), inplace=True)
      ohlcv = ohlcv.astype("float64")
      self.ohlcvs[symbol] = ohlcv
      return ohlcv

    def get_realtime_data():
        raise NotImplementedError

    def compute_indicators(self, indicators=[]):

        c = self.ohlcv["close"]
        h = self.ohlcv["high"]
        l = self.ohlcv["low"]
        v = self.ohlcv["volume"]

        cs = ta.vwma(h, v, length=3)
        cs.rename("csup", inplace=True)

        cm = ta.vwma(c, v, length=3)
        cm.rename("cmed", inplace=True)

        ci = ta.vwma(l, v, length=3)
        ci.rename("cinf", inplace=True)

        macd = ta.macd(c)
        macd.rename(
            columns={
                "MACD_12_26_9": "macd",
                "MACDh_12_26_9": "histogram",
                "MACDs_12_26_9": "signal",
            },
            inplace=True,
        )

        df = pd.concat([cs, ci, c, cm, v, macd], axis=1)

        return df


class GrabberMACD(Grabber):
    def compute_indicators(self, indicators=[]):

        c = self.ohlcv["close"]
        h = self.ohlcv["high"]
        l = self.ohlcv["low"]
        v = self.ohlcv["volume"]

        macd = ta.macd(c)
        macd.rename(
            columns={
                "MACD_12_26_9": "macd",
                "MACDh_12_26_9": "histogram",
                "MACDs_12_26_9": "signal",
            },
            inplace=True,
        )

        df = pd.concat([c, macd], axis=1)

        return df


##
if __name__ == "__main__":
    from binance.client import Client

    client = Client()
    grab = GrabberMACD(client)
    grab.get_data()
    grab.ohlcv
