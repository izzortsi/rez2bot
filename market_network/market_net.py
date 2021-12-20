    """
=======================================
Visualizing the stock market structure
=======================================

This example employs several unsupervised learning techniques to extract
the stock market structure from variations in historical quotes.

The quantity that we use is the daily variation in quote price: quotes
that are linked tend to cofluctuate during a day.

.. _stock_market:

Learning a graph structure
--------------------------

We use sparse inverse covariance estimation to find which quotes are
correlated conditionally on the others. Specifically, sparse inverse
covariance gives us a graph, that is a list of connection. For each
symbol, the symbols that it is connected too are those useful to explain
its fluctuations.

Clustering
----------

We use clustering to group together quotes that behave similarly. Here,
amongst the :ref:`various clustering techniques <clustering>` available
in the scikit-learn, we use :ref:`affinity_propagation` as it does
not enforce equal-size clusters, and it can choose automatically the
number of clusters from the data.

Note that this gives us a different indication than the graph, as the
graph reflects conditional relations between variables, while the
clustering reflects marginal properties: variables clustered together can
be considered as having a similar impact at the level of the full stock
market.

Embedding in 2D space
---------------------

For visualization purposes, we need to lay out the different symbols on a
2D canvas. For this we use :ref:`manifold` techniques to retrieve 2D
embedding.


Visualization
-------------

The output of the 3 models are combined in a 2D graph where nodes
represents the stocks and edges the:

- cluster labels are used to define the color of the nodes
- the sparse covariance model is used to display the strength of the edges
- the 2D embedding is used to position the nodes in the plan

This example has a fair amount of visualization-related code, as
visualization is crucial here to display the graph. One of the challenge
is to position the labels minimizing overlap. For this we use an
heuristic based on the direction of the nearest neighbor along each
axis.
"""

# Author: Gael Varoquaux gael.varoquaux@normalesup.org
# License: BSD 3 clause

# %%

import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

import pandas as pd
from sklearn import cluster, covariance, manifold

from binance.client import Client
from symbols_formats import FORMATS
symbols = list(FORMATS.keys())


symbols
# #############################################################################
# %%
from binance.client import Client
import pandas as pd
import pandas_ta as ta

# %%


class DataGrabber:
    def __init__(self, client):
        self.client = client

    def get_data(self, symbol="BTCUSDT", timeframe="4h", fromdate="2 month ago"):
        klines = self.client.get_historical_klines(symbol, timeframe, fromdate)
        replaced_fromdate = fromdate.replace(" ", "-")
        return self.trim_data(klines)

    def trim_data(self, rdata):
        df = pd.DataFrame(data=rdata)
        DOHLCV = df.iloc[:, [0, 1, 2, 3, 4, 5]]
        DOHLCV[0] = pd.to_datetime(DOHLCV[0], unit="ms")
        DOHLCV.columns = ["date", "open", "high", "low", "close", "volume"]
        DOHLCV.ta.adjusted = "adj_close"
        OHLCV = DOHLCV.iloc[:, [1, 2, 3, 4, 5]]
        OHLCV.set_index(pd.DatetimeIndex(DOHLCV["date"]), inplace=True)
        OHLCV = OHLCV.astype("float64")
        return OHLCV

    def compute_indicators(self, ohlcv, N=2, indicators={}):

        c = ohlcv["close"]
        h = ohlcv["high"]
        l = ohlcv["low"]
        v = ohlcv["volume"]

        cs = ta.vwema(h, v, length=N)
        cs.rename("csup", inplace=True)

        cm = ta.vwema(c, v, length=N)
        cm.rename("cmed", inplace=True)

        ci = ta.vwema(l, v, length=N)
        ci.rename("cinf", inplace=True)

        mfi = ta.mfi(h, l, c, v, length=14)

        macd = ta.macd(c)

        def normalize(series):
            mean = series.mean()
            stdev = series.std()
            return (series - mean) / stdev

        # macd_mean = macd.mean()
        # macd_std = macd.std()

        macd_h = macd["MACDh_12_26_9"]

        macd = normalize(macd)

        print(macd_h.tail(3))
        print(macd.tail(3))

        D1h = macd_h.shift(1) - macd_h
        D1h = D1h.rename("D1h")
        D1h = normalize(D1h)
        D2h = D1h.shift(1) - D1h
        D2h = D2h.rename("D2h")
        D2h = normalize(D2h)
        df = pd.concat([cs, ci, c, cm, v, macd, mfi, D1h, D2h], axis=1)

        return df


# %%
# Retrieve the data from Internet


# %%

client = Client()

def get_klines_multiple_symbols(self, symbols, timeframe, fromdate="1 day ago"):
    klines = {}
    for symbol in symbols:
        symbol_df = self.get_data(symbol=symbol, timeframe=timeframe, fromdate=fromdate)
        klines["symbol"] = symbol_df
    return klines

DataGrabber.get_klines_multiple_symbols = get_klines_multiple_symbols
# %%

dg = DataGrabber(client)
# %%

klines = dg.get_klines_multiple_symbols(symbols=symbols, timeframe="1h")
# %%
type(klines)
# %%

quotes = []

for symbol in symbols:
    print('Fetching quote history for %r' % symbol, file=sys.stderr)
    url = ('https://raw.githubusercontent.com/scikit-learn/examples-data/'
           'master/financial-data/{}.csv')
    quotes.append(pd.read_csv(url.format(symbol)))

close_prices = np.vstack([q['close'] for q in quotes])
open_prices = np.vstack([q['open'] for q in quotes])

# The daily variations of the quotes are what carry most information
variation = close_prices - open_prices


# #############################################################################
# Learn a graphical structure from the correlations
edge_model = covariance.GraphicalLassoCV()

# standardize the time series: using correlations rather than covariance
# is more efficient for structure recovery
X = variation.copy().T
X /= X.std(axis=0)
edge_model.fit(X)

# #############################################################################
# Cluster using affinity propagation

_, labels = cluster.affinity_propagation(edge_model.covariance_,
                                         random_state=0)
n_labels = labels.max()

for i in range(n_labels + 1):
    print('Cluster %i: %s' % ((i + 1), ', '.join(names[labels == i])))

# #############################################################################
# Find a low-dimension embedding for visualization: find the best position of
# the nodes (the stocks) on a 2D plane

# We use a dense eigen_solver to achieve reproducibility (arpack is
# initiated with random vectors that we don't control). In addition, we
# use a large number of neighbors to capture the large-scale structure.
node_position_model = manifold.LocallyLinearEmbedding(
    n_components=2, eigen_solver='dense', n_neighbors=6)

embedding = node_position_model.fit_transform(X.T).T

# #############################################################################
# Visualization
plt.figure(1, facecolor='w', figsize=(10, 8))
plt.clf()
ax = plt.axes([0., 0., 1., 1.])
plt.axis('off')

# Display a graph of the partial correlations
partial_correlations = edge_model.precision_.copy()
d = 1 / np.sqrt(np.diag(partial_correlations))
partial_correlations *= d
partial_correlations *= d[:, np.newaxis]
non_zero = (np.abs(np.triu(partial_correlations, k=1)) > 0.02)

# Plot the nodes using the coordinates of our embedding
plt.scatter(embedding[0], embedding[1], s=100 * d ** 2, c=labels,
            cmap=plt.cm.nipy_spectral)

# Plot the edges
start_idx, end_idx = np.where(non_zero)
# a sequence of (*line0*, *line1*, *line2*), where::
#            linen = (x0, y0), (x1, y1), ... (xm, ym)
segments = [[embedding[:, start], embedding[:, stop]]
            for start, stop in zip(start_idx, end_idx)]
values = np.abs(partial_correlations[non_zero])
lc = LineCollection(segments,
                    zorder=0, cmap=plt.cm.hot_r,
                    norm=plt.Normalize(0, .7 * values.max()))
lc.set_array(values)
lc.set_linewidths(15 * values)
ax.add_collection(lc)

# %%

# Add a label to each node. The challenge here is that we want to
# position the labels to avoid overlap with other labels
for index, (name, label, (x, y)) in enumerate(
        zip(names, labels, embedding.T)):

    dx = x - embedding[0]
    dx[index] = 1
    dy = y - embedding[1]
    dy[index] = 1
    this_dx = dx[np.argmin(np.abs(dy))]
    this_dy = dy[np.argmin(np.abs(dx))]
    if this_dx > 0:
        horizontalalignment = 'left'
        x = x + .002
    else:
        horizontalalignment = 'right'
        x = x - .002
    if this_dy > 0:
        verticalalignment = 'bottom'
        y = y + .002
    else:
        verticalalignment = 'top'
        y = y - .002
    plt.text(x, y, name, size=10,
             horizontalalignment=horizontalalignment,
             verticalalignment=verticalalignment,
             bbox=dict(facecolor='w',
                       edgecolor=plt.cm.nipy_spectral(label / float(n_labels)),
                       alpha=.6))

plt.xlim(embedding[0].min() - .15 * embedding[0].ptp(),
    embedding[0].max() + .10 * embedding[0].ptp(),)
plt.ylim(embedding[1].min() - .03 * embedding[1].ptp(),
    embedding[1].max() + .03 * embedding[1].ptp())
plt.show()

# %%

import graph_tool as gt
