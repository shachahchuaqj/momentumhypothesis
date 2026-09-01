import os
import sys
import pandas as pd

# Number of trading days in the "12-week" volume window (12 weeks x 5 trading days).
mid_window = 60
short_window = 5
# Number of trading days in 5 years, for rolling "force" percentile window
long_window = 252 * 5

def _load_prices(ticker: str, prices_dir: str = "rawpricesdata") -> pd.DataFrame:
    '''Load and sort the raw price/volume CSV for a given ticker.'''
    path = os.path.join(prices_dir, f"prices_{ticker}.csv")

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No price data found for ticker '{ticker}'. "
            f"Expected file at: {path}"
        )

    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def _load_dividends(ticker: str, prices_dir: str = "dividendsdata") -> pd.DataFrame:
    '''Load and sort the raw dividends CSV for a given ticker.'''
    path = os.path.join(prices_dir, f"dividends_{ticker}.csv")

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No dividends data found for ticker '{ticker}'. "
            f"Expected file at: {path}"
        )

    df = pd.read_csv(path, parse_dates=["ExDate"])
    df = df.sort_values("ExDate").reset_index(drop=True)
    return df

def volume_ratio(ticker: str,
                  prices_dir: str = "rawpricesdata") -> pd.DataFrame:
    '''
    Returns a DataFrame with columns 'Date', '5d Vbar', '8w Vbar', 'Vratio'.
    If not enough data to calculate the Vbar, the cell is left empty.
    '''
    df = _load_prices(ticker, prices_dir)

    df["5d Vbar"] = df["Volume"].rolling(window=short_window).mean()
    df["8w Vbar"] = df["Volume"].rolling(window=mid_window).mean()
    df["Vratio"] = (df["5d Vbar"] / df["8w Vbar"]) * 100

    return df[["Date", "5d Vbar", "8w Vbar", "Vratio"]]


def growth_rate(ticker: str,
                 prices_dir: str = "rawpricesdata") -> pd.DataFrame:
    '''
    Returns a DataFrame with columns 'Date', 'Growth Rate'.
    If not enough data to calculate the Growth Rate, the cell is left empty.
    '''
    df = _load_prices(ticker, prices_dir)

    prior_close = df["Close"].shift(short_window)
    df["Growth Rate"] = ((df["Close"] - prior_close) / prior_close) / short_window * 100

    return df[["Date", "Growth Rate"]]


def metrics(ticker: str,
            prices_dir: str = "rawpricesdata") -> pd.DataFrame:
    '''
    Returns a DataFrame with columns 'Date', 'Close', 'Vratio', 'Growth Rate', 'Momentum', 'Force'.
    During the merging of the DataFrames, any rows with empty cells are dropped.
    '''

    pdf = _load_prices(ticker, prices_dir)[["Date", "Close"]]
    vdf = volume_ratio(ticker, prices_dir)
    rdf = growth_rate(ticker, prices_dir)

    merged = pdf.merge(vdf, on="Date", how="inner").merge(rdf, on="Date", how="inner")

    merged["Momentum"] = merged["Vratio"] * merged["Growth Rate"] / 100
    merged["Force"] = merged["Momentum"].diff()

    merged = merged[["Date", "Close", "Vratio", "Growth Rate", "Momentum", "Force"]]
    merged = merged.dropna().reset_index(drop=True)

    return merged


def metrics_pct(ticker: str,
                        prices_dir: str = "rawpricesdata") -> pd.DataFrame:
    '''
    Returns metrics() plus two additional columns:
    'Force 2.5pct' and 'Force 97.5pct' - the rolling 2.5th and 97.5th
    percentile of Force, computed using only the `long_window` (5 years)
    of Force values strictly BEFORE each row (today's own Force value is
    excluded from its own threshold, avoiding look-ahead bias).
    Rows without a full long_window of trailing history are dropped.
    '''
    df = metrics(ticker, prices_dir)

    shifted_force = df["Force"].shift(1)
    df["Force 2.5pct"] = shifted_force.rolling(window=long_window, min_periods=long_window).quantile(0.025)
    df["Force 97.5pct"] = shifted_force.rolling(window=long_window, min_periods=long_window).quantile(0.975)

    df = df.dropna().reset_index(drop=True)
    return df


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python metric_calc.py <TICKER>")
        print("Example: python metric_calc.py SPY")
        sys.exit(1)

    ticker_arg = sys.argv[1]
    result = metrics(ticker_arg)
    print(result)
