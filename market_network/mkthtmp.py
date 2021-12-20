
# %%

import dash
import dash_table
import pandas as pd
from collections import OrderedDict
import dash_html_components as html
import numpy as np
# wide_data = [
#     {'Firm': 'Acme', '2017': 13, '2018': 5, '2019': 10, '2020': 4},
#     {'Firm': 'Olive', '2017': 3, '2018': 3, '2019': 13, '2020': 3},
#     {'Firm': 'Barnwood', '2017': 6, '2018': 7, '2019': 3, '2020': 6},
#     {'Firm': 'Henrietta', '2017': -3, '2018': -10, '2019': -5, '2020': -6},
# ]
# df = pd.DataFrame(wide_data)

from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()


# %%
coins_mkts = cg.get_coins_markets(vs_currency="usd", order="volume_desc", per_page=200,
                                  page=1, sparkline=True, price_change_percentage=["1h", "24h", "7d"])


def get_filtered_dict(coin_dict):

    symbol = coin_dict["symbol"]

    data_dict = {}
    filtered_dict = {symbol: data_dict}

    circulating_supply = coin_dict['circulating_supply']
    total_supply = coin_dict['total_supply']

    if (total_supply is None or
            total_supply == 0):
        total_supply = circulating_supply

        if total_supply == 0:
            total_supply, circulating_supply = 1, 1

    print(circulating_supply, total_supply)

    supply_ratio = circulating_supply/total_supply

    keys = [
        "current_price",
        'market_cap',
        'market_cap_rank',
        'total_volume',
        'high_24h',
        'low_24h',
        'price_change_percentage_24h',
        'market_cap_change_percentage_24h',
        'supply_ratio',
        'ath',
        'ath_change_percentage',
        'atl',
        'atl_change_percentage',
        'price_change_percentage_1h_in_currency',
        'price_change_percentage_24h_in_currency',
        'price_change_percentage_7d_in_currency',
        'sparkline_in_7d',
    ]

    for key in keys:
        if key == 'supply_ratio':
            data_dict[key] = supply_ratio
        elif key == "sparkline_in_7d":  # sparkline returns a dict of prices
            data_dict["price"] = np.array(coin_dict[key]["price"])
        else:
            data_dict[key] = coin_dict[key]

    return filtered_dict


# %%


def process_request(response):

    coins_data = []

    for coin_dict in response:
        row = pd.DataFrame.from_dict(get_filtered_dict(coin_dict))
        coins_data.append(row)

    return coins_data


# %%
coins_data = process_request(coins_mkts)

# %%
coins_data
# %%

df = pd.concat(coins_data, axis=1)
df
# %%

app = dash.Dash(__name__)

def discrete_background_color_bins(df, n_bins=5, columns='all'):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Blues'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} >= {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': backgroundColor,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
            ])
        )

    return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))

(styles, legend) = discrete_background_color_bins(df)

app.layout = html.Div([
    html.Div(legend, style={'float': 'right'}),
    dash_table.DataTable(
        data=df.to_dict('records'),
        sort_action='native',
        columns=[{'name': i, 'id': i} for i in df.columns],
        style_data_conditional=styles
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
#%%
