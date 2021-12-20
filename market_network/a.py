#%%

#%%
import plotly.graph_objects as go

f = go.FigureWidget()

f

# f.add_scatter(x=df.init_ts, y=df.close, mode='lines', name='close');
f.add_scatter(x=df.init_ts, y=close_ema, mode='lines', name='close ema')
f.add_trace(kl_go)

def plot_atr_grid_widget(atr_grid, fig):
    for atr_band in atr_grid:
        # atr_go = go.Scatter(x=df.init_ts, y=atr_band,
        #                     mode="lines",
        #                     # line=go.scatter.Line(color="teal"),
        #                     showlegend=False,
        #                     line=dict(color='teal', width=0.4), 
        #                     opacity=.8,
        #                     hoverinfo='skip')
        fig.add_scatter(x=df.init_ts, 
            y=atr_band, hoverinfo="skip", opacity=.8, 
            mode="lines", showlegend=False,
            line=dict(color='teal', width=0.4))

plot_atr_grid_widget(atr_grid, f)    
f.update(layout_xaxis_rangeslider_visible=False)
f.update_layout(
    autosize=True,
    width=1000,
    height=600,
    margin=dict(
        l=10,
        r=10,
        b=10,
        t=10,
        pad=1
    ),
    paper_bgcolor="LightSteelBlue",
)

f.update_xaxes(showgrid=True, zeroline=False, rangeslider_visible=False, showticklabels=False,
                 showspikes=True, spikemode='across', spikesnap='cursor', showline=False,
                 spikecolor="grey",spikethickness=1, spikedash='solid')
f.update_yaxes(showspikes=True, spikedash='solid',spikemode='across', 
                spikecolor="grey",spikesnap="cursor",spikethickness=1)
# f.update_layout(spikedistance=1000,hoverdistance=1000)
f.update_layout(hovermode="x unified")
f
# %%





fig = make_subplots(rows=3, cols=4,
    specs=[[{'rowspan': 2, 'colspan': 3}, None, None, {'rowspan': 2}],
       [None, None, None, None],
       [{'colspan': 3}, None, None, {}]],
      vertical_spacing=0.075,
    horizontal_spacing=0.08,
    shared_xaxes=True)
# fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

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
        atr_go = go.Scatter(x=df.init_ts, y=atr_band,
                            mode="lines",
                            # line=go.scatter.Line(color="teal"),
                            showlegend=False,
                            line=dict(color='teal', width=0.4), 
                            opacity=.8,
                            hoverinfo='skip')
        fig.add_trace(atr_go, row=1, col=1)


fig.add_trace(kl_go, row=1, col=1)
fig.update(layout_xaxis_rangeslider_visible=False)

fig.add_trace(ema_go, row=1, col=1)
fig.add_trace(hist_go, row=3, col=1)

plot_atr_grid(atr_grid, fig)

fig.update_layout(
    autosize=True,
    width=1000,
    height=600,
    margin=dict(
        l=10,
        r=10,
        b=10,
        t=10,
        pad=1
    ),
    paper_bgcolor="LightSteelBlue",
)


# fig.update_layout({'plot_bgcolor': "#21201f", 'paper_bgcolor': "#21201f", 'legend_orientation': "h"},
#                   legend=dict(y=1, x=0),
#                   font=dict(color='#dedddc'), dragmode='pan', hovermode='x',
#                   margin=dict(b=20, t=0, l=0, r=40),
#                   )
fig.update_layout({'paper_bgcolor': "#21201f", 'legend_orientation': "h"},
                  legend=dict(y=1, x=0),
                  font=dict(color='#dedddc'), dragmode='pan',
                  margin=dict(b=20, t=0, l=0, r=40),
                  )                  
# fig.update_xaxes(spikecolor="grey",spikethickness=1)
fig.update_xaxes(showgrid=True, zeroline=False, rangeslider_visible=False, showticklabels=False,
                 showspikes=True, spikemode='across', spikesnap='cursor', showline=False,
                 spikecolor="grey",spikethickness=1, spikedash='solid')
fig.update_yaxes(showspikes=True, spikedash='solid',spikemode='across', 
                spikecolor="grey",spikesnap="cursor",spikethickness=1)
# fig.update_layout(spikedistance=1000,hoverdistance=1000)
fig.update_layout(hovermode="x unified")


fig.update_traces(xaxis='x')
fig.show()


# %%