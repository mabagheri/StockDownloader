import concurrent.futures
import streamlit as st
import yfinance as yf
import pandas as pd
import zipfile
import os
import datetime
# Load predefined stock lists
@st.cache_data
def load_ticker_list(option):
    indices = ["SPY", "QQQ", "XIC", "XLC", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLK", "XLB", "XLRE", "XLU"]
    if option == "Indices": 
        return indices # ["^GSPTSE",]
    elif option == "Canadian Stocks":
        return pd.read_csv("canadian_stocks.csv")["Ticker"].dropna().unique().tolist() + indices
    elif option == "US Stocks":
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


def fetch_data_parallel(tickers, start_date, end_date):
    status_text.text("start parallel downloading!")

    data_dict = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(tickers)

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:  # adjust workers
        futures = {executor.submit(fetch_single_ticker, ticker, start_date, end_date): ticker for ticker in tickers}
        
        for future in concurrent.futures.as_completed(futures):
            ticker = futures[future]
            result = future.result()
            if result:
                t, df = result
                if isinstance(df, str):  # error message
                    st.error(f"{t}: {df}")
                elif df is not None:
                    data_dict[t] = df

            completed += 1
            progress_bar.progress(completed / total)
            status_text.text(f"Completed {completed}/{total} ({ticker})")

    status_text.text("✅ All downloads finished!")
    return data_dict

st.title("Stock Data Downloader!")
# Let user choose the market
market_choice = st.selectbox("Select Market", ["Incides", "Canadian Stocks", "US Stocks"])
# Load tickers based on choice
tickers = load_ticker_list(market_choice)
st.write(f"Number of tickers loaded: {len(tickers)}")

# Let user pick a date range
start_date = st.date_input("Start Date", datetime.date(2010, 1, 1), min_value=datetime.date(2010, 1, 1), max_value=datetime.date.today())
end_date = st.date_input("End Date", datetime.date.today(), min_value=datetime.date(2010, 1, 1), max_value=datetime.date.today())

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
