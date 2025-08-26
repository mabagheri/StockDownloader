import streamlit as st
import yfinance as yf
import pandas as pd
import zipfile
import os
import datetime

# Load predefined stock lists
@st.cache_data
def load_ticker_list(option):
    if option == "TSX index": 
        return ["^GSPTSE",]
    elif option == "Canadian":
        return pd.read_csv("canadian_stocks.csv")["Ticker"].dropna().unique().tolist()
    elif option == "US":
        ticker_list = ['AAPL', 'HD', 'MSFT']
        return ticker_list # pd.read_csv("us_stocks.csv")["Ticker"].dropna().unique().tolist()
    return []
    
# Function to fetch data
def fetch_data(tickers, start_date, end_date):
    data_dict = {}
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers, start=1):
        try:
            status_text.text(f"Downloading {ticker} ({i}/{len(tickers)}) ...")
            df = yf.download(ticker, start=start_date, end=end_date)
            if not df.empty:
                data_dict[ticker] = df
        
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")

        # Update progress bar
        progress_bar.progress(i / len(tickers))
        
    status_text.text("✅ Download complete!")
    return data_dict


st.title("Stock Data Downloader!")
