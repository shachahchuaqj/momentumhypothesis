import os
import sys
import pandas as pd
import yfinance as yf
from dateutil import parser as dateparser

# Set to "csv" or "xlsx" depending on preference.
OUTPUT_FORMAT = "csv"

def parse_date(date_str: str) -> str:
    """Parse a flexible date string and return it in 'YYYY-MM-DD' format."""
    try:
        return dateparser.parse(date_str).strftime("%Y-%m-%d")
    except (ValueError, OverflowError) as e:
        raise ValueError(f"Could not parse date: '{date_str}'") from e


def _save(df: pd.DataFrame, path_no_ext: str) -> str:
    """Save a dataframe as csv or xlsx depending on OUTPUT_FORMAT, return the path used."""
    if OUTPUT_FORMAT == "xlsx":
        path = f"{path_no_ext}.xlsx"
        df.to_excel(path, index=False)
    else:
        path = f"{path_no_ext}.csv"
        df.to_csv(path, index=False)
    return path


def fetch_and_save(ticker: str, start: str, end: str,
                    prices_dir: str = "rawpricesdata",
                    dividends_dir: str = "dividendsdata") -> None:
    """
    Fetch historical closing prices + volume, and dividend (ex-date) data
    for `ticker` between `start` and `end`, and save each to its own file
    in the given subfolders.
    """

    os.makedirs(prices_dir, exist_ok=True)
    os.makedirs(dividends_dir, exist_ok=True)

    stock = yf.Ticker(ticker)

    # --- Price + volume history ---
    prices = stock.history(start=start, end=end, auto_adjust=False)

    if prices.empty:
        raise RuntimeError(
            f"No price data returned for {ticker}. "
            "Check the ticker symbol, date range, or your internet connection."
        )

    prices = prices[["Close", "Volume"]].copy()
    prices.index.name = "Date"
    prices.reset_index(inplace=True)
    prices["Date"] = prices["Date"].dt.strftime("%Y-%m-%d")

    prices_path = _save(prices, os.path.join(prices_dir, f"prices_{ticker}"))
    print(f"Saved {len(prices)} price rows to {prices_path}")

    # --- Dividend history (ex-dividend dates) ---
    dividends = stock.dividends

    if dividends.empty:
        print(f"Warning: no dividend data found for {ticker}.")
    else:
        dividends = dividends.loc[start:end]
        dividends = dividends.reset_index()
        dividends.columns = ["ExDate", "Dividend"]
        dividends["ExDate"] = pd.to_datetime(dividends["ExDate"]).dt.strftime("%Y-%m-%d")

        dividends_path = _save(dividends, os.path.join(dividends_dir, f"dividends_{ticker}"))
        print(f"Saved {len(dividends)} dividend rows to {dividends_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fetch_data.py <TICKER> <START_DATE> <END_DATE>")
        print("Example: python fetch_data.py SPY 2005-03-01 2026-08-31")
        sys.exit(1)

    ticker_arg = sys.argv[1]
    start_arg = parse_date(sys.argv[2])
    end_arg = parse_date(sys.argv[3])

    fetch_and_save(ticker_arg, start_arg, end_arg)