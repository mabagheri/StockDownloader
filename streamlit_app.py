import streamlit as st
import yfinance as yf
import pandas as pd
import zipfile
import os

# Load predefined stock lists
@st.cache_data
def load_ticker_list(option):
    if option == "Canadian Stocks":
        ticker_list = ['RY.TO', 'TD.to']
        return ticker_list # pd.read_csv("canadian_stocks.csv")["Ticker"].dropna().unique().tolist()
    elif option == "US Stocks":
        ticker_list = ['AAPL', 'HD', 'MSFT']
        return ticker_list # pd.read_csv("us_stocks.csv")["Ticker"].dropna().unique().tolist()
    return []

# Function to fetch data
def fetch_data(tickers, start_date, end_date):
    data_dict = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            if not df.empty:
                data_dict[ticker] = df
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")
    return data_dict

st.title("Stock Data Downloader")

# Let user choose the market
market_choice = st.selectbox("Select Market", ["Canadian Stocks", "US Stocks"])

# Load tickers based on choice
tickers = load_ticker_list(market_choice)

st.write(f"Number of tickers loaded: {len(tickers)}")

# Let user pick a date range
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

# Fetch Data
if st.button("Fetch Data"):
    if tickers and start_date and end_date:
        stock_data = fetch_data(tickers, start_date, end_date)
        if stock_data:
            st.session_state["stock_data"] = stock_data
            st.success("Data fetched successfully!")
        else:
            st.error("No data retrieved.")
    else:
        st.error("Missing inputs.")

# Save CSVs and offer ZIP download
if "stock_data" in st.session_state:
    if st.button("Save CSVs"):
        zip_filename = "stock_data.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for ticker, df in st.session_state["stock_data"].items():
                csv_filename = f"{ticker}.csv"
                df.to_csv(csv_filename)
                zipf.write(csv_filename)
                os.remove(csv_filename)  # Clean up

        with open(zip_filename, "rb") as file:
            st.download_button("Download All CSVs", file, zip_filename, "application/zip")

        os.remove(zip_filename)
