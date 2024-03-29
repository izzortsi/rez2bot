
# %%

import dash
from dash import dash_table
import pandas as pd

# %%

from screener import *
# %%
signals, rows = screen()
# %%

df = pd.concat(rows, axis=1).transpose()

app = dash.Dash(__name__)

app.layout = dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records'),
)

if __name__ == '__main__':
    app.run_server(debug=True)
#%%
