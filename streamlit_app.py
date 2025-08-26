import streamlit as st
import pandas as pd
import yfinance as yf
import zipfile
import os
import concurrent.futures
from datetime import timedelta, date

# -------------------------
# Load predefined stock lists
# -------------------------
@st.cache_data
def load_ticker_list(option):
    if option == "Canadian Stocks":
        return pd.read_csv("canadian_stocks.csv")["Ticker"].dropna().unique().tolist()
    elif option == "US Stocks":
        return pd.read_csv("us_stocks.csv")["Ticker"].dropna().unique().tolist()
    return []


# -------------------------
# Incremental download logic
# -------------------------
def update_or_download(ticker, start_date, end_date):
    filename = f"{ticker}.csv"

    try:
        if os.path.exists(filename):
            existing = pd.read_csv(filename, index_col=0, parse_dates=True)
            last_date = existing.index.max().date()

            # Only fetch new rows
            if last_date < end_date:
                new_start = last_date + timedelta(days=1)
                new_data = yf.download(ticker, start=new_start, end=end_date)
                if not new_data.empty:
                    updated = pd.concat([existing, new_data])
                    updated.to_csv(filename)
                    return updated
                else:
                    return existing
            else:
                return existing
        else:
            # Full download
            df = yf.download(ticker, start=start_date, end=end_date)
            if not df.empty:
                df.to_csv(filename)
            return df
    except Exception as e:
        return f"Error: {e}"


# -------------------------
# Parallel downloader
# -------------------------
def fetch_data_parallel(tickers, start_date, end_date):
    data_dict = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(tickers)

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(update_or_download, ticker, start_date, end_date): ticker
            for ticker in tickers
        }

        for future in concurrent.futures.as_completed(futures):
            ticker = futures[future]
            result = future.result()

            if isinstance(result, str):  # error
                st.error(f"{ticker}: {result}")
            elif result is not None and not result.empty:
                data_dict[ticker] = result

            completed += 1
            progress_bar.progress(completed / total)
            status_text.text(f"Completed {completed}/{total} ({ticker})")

    status_text.text("✅ All downloads finished!")
    return data_dict


# -------------------------
# Streamlit App
# -------------------------
st.title("📈 Stock Data Downloader")

# Market choice
market_choice = st.selectbox("Select Market", ["Canadian Stocks", "US Stocks"])
tickers = load_ticker_list(market_choice)
st.write(f"Loaded {len(tickers)} tickers.")

# Date range
start_date = st.date_input("Start Date", value=date(2000, 1, 1))
end_date = st.date_input("End Date", value=date.today())

# Fetch button
if st.button("Fetch Data"):
    if tickers and start_date and end_date:
        stock_data = fetch_data_parallel(tickers, start_date, end_date)
        if stock_data:
            st.session_state["stock_data"] = stock_data
            st.success("Data fetched and updated successfully!")
        else:
            st.error("No data retrieved.")
    else:
        st.error("Please provide valid inputs.")

# Save CSVs to ZIP
if "stock_data" in st.session_state:
    if st.button("Save CSVs"):
        zip_filename = "stock_data.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for ticker, df in st.session_state["stock_data"].items():
                csv_filename = f"{ticker}.csv"
                df.to_csv(csv_filename)
                zipf.write(csv_filename)
                os.remove(csv_filename)

        with open(zip_filename, "rb") as file:
            st.download_button("⬇️ Download All CSVs", file, zip_filename, "application/zip")

        os.remove(zip_filename)
