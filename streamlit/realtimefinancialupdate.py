from requests import get
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st


def get_price(symbol):
    response = get('https://finance.yahoo.com/quote/{}/'.format(symbol))
    soup = BeautifulSoup(response.text, 'html.parser')
    return float(soup.find_all(
        attrs={'class': 'Trsdu(0.3s)'})[0].text.replace(',', ''))


symbols = ['NFLX', 'MSFT', 'AMZN', 'AAP']
prices = pd.DataFrame(columns=['datetime', 'price'])
selected_symbols = st.multiselect('Symbols', symbols, ['NFLX'])
for _symbol in selected_symbols:
    prices.loc[_symbol] = {'datetime': pd.datetime.now(),
                           'price': get_price(_symbol)}

st.header('Quotes')
st.dataframe(prices)
st.button('Update')