import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_single_atr_grid(df, atr, atr_grid, close_ema, hist):
    
    
    fig = make_subplots(rows=3, cols=4,
        specs=[[{'rowspan': 2, 'colspan': 3}, None, None, {'rowspan': 2}],
        [None, None, None, None],
        [{'colspan': 3}, None, None, {}]],
        vertical_spacing=0.075,
        horizontal_spacing=0.08,
        shared_xaxes=True)
    # fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

    # %%
    kl_go = go.Candlestick(x=df['init_ts'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'])


    atr_go = go.Scatter(x=df.init_ts, y=atr,
                                mode="lines",
                                line=go.scatter.Line(color="gray"),
                                showlegend=False)
                                

    ema_go = go.Scatter(x=df.init_ts, y=close_ema,
                                mode="lines",
                                # line=go.scatter.Line(color="blue"),
                                showlegend=True,
                                line=dict(color='royalblue', width=3),
                                opacity=0.75,
                                )

    def hist_colors(hist):
        diffs = hist.diff()
        colors = diffs.apply(lambda x: "green" if x > 0 else "red")
        return colors


    _hist_colors = hist_colors(hist)


    hist_go = go.Scatter(x=df.init_ts, y=hist,
                                mode="lines+markers",
                                # line=go.scatter.Line(color="blue"),
                                showlegend=False,
                                line=dict(color="black", width=3),
                                opacity=1,
                                marker=dict(color=_hist_colors, size=6),
                                )

    def plot_atr_grid(atr_grid, fig):
        for atr_band in atr_grid:
            if sum(atr_band) >= 1.2 * sum(close_ema):
                color = 'red'
            else:
                color = "teal"
            atr_go = go.Scatter(x=df.init_ts, y=atr_band,
                                mode="lines",
                                # line=go.scatter.Line(color="teal"),
                                showlegend=False,
                                line=dict(color=color, width=0.4), 
                                opacity=.8,
                                hoverinfo='skip')
            fig.add_trace(atr_go, row=1, col=1)


    fig.add_trace(kl_go, row=1, col=1)
    fig.update(layout_xaxis_rangeslider_visible=False)

    fig.add_trace(ema_go, row=1, col=1)
    fig.add_trace(hist_go, row=3, col=1)

    plot_atr_grid(atr_grid, fig)

    return fig


def plot_multiple_atr_grids(dfs, atrs, atr_grids, closes_emas, layout_shape=(4, 1)):
    
    nrows, ncols = layout_shape

    fig = make_subplots(rows=nrows, cols=ncols,
        vertical_spacing=0.075,
        horizontal_spacing=0.08,
        shared_xaxes=True)
    # fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
    c = 0
    for df, atr, atr_grid, close_ema in zip(dfs, atrs, atr_grids, closes_emas): 
    # %%
        row = c
        col = 1
        kl_go = go.Candlestick(x=df['init_ts'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'])


        # atr_go = go.Scatter(x=df.init_ts, y=atr,
        #                             mode="lines",
        #                             line=go.scatter.Line(color="gray"),
        #                             showlegend=False)
                                    

        ema_go = go.Scatter(x=df.init_ts, y=close_ema,
                                    mode="lines",
                                    # line=go.scatter.Line(color="blue"),
                                    showlegend=True,
                                    line=dict(color='royalblue', width=3),
                                    opacity=0.75,
                                    )


        def plot_atr_grid(atr_grid, fig, row, col):
            for atr_band in atr_grid:
                if sum(atr_band) >= 1.2 * sum(close_ema):
                    color = 'red'
                else:
                    color = "teal"
                atr_go = go.Scatter(x=df.init_ts, y=atr_band,
                                    mode="lines",
                                    # line=go.scatter.Line(color="teal"),
                                    showlegend=False,
                                    line=dict(color=color, width=0.4), 
                                    opacity=.8,
                                    hoverinfo='skip')
                fig.add_trace(atr_go, row=row, col=col)


        fig.add_trace(kl_go, row=row, col=col)
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.add_trace(ema_go, row=row, col=col)
        plot_atr_grid(atr_grid, fig, row, col)
        c += 1
    return fig
