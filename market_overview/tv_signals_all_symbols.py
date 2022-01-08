# %%
from tradingview_ta import *
from src.symbols_formats import FORMATS

# %%
symbols = FORMATS.keys()
symbols = list(symbols)
tv_symbols = symbols.copy()

for i, symbol in enumerate(tv_symbols):
    tv_symbols[i] = "BINANCE:" + symbol

# %%

tv_symbols[1]
# %%
analysis = get_multiple_analysis(
    screener="crypto",
    interval=Interval.INTERVAL_1_HOUR,
    symbols=tv_symbols,
)

analysis
