from pathlib import Path
import io

import pandas as pd
import requests
import yfinance as yf

USER_AGENT = "Mozilla/5.0"
S_AND_P_500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
MIN_REQUIRED_NUM_OBS_PER_TICKER = 100


def _fetch_sp500_tickers() -> list[str]:
    """Fetch the current S&P 500 ticker list from Wikipedia."""
    response = requests.get(
        S_AND_P_500_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    sp500_tickers = pd.read_html(io.StringIO(response.text))[0]["Symbol"].tolist()
    # Drop B-class share suffix variants that often have sparse data.
    return [ticker for ticker in sp500_tickers if ".B" not in ticker]


def _filter_dense_tickers(prices: pd.DataFrame) -> pd.DataFrame:
    """Keep only tickers with sufficient observation count."""
    ticker_counts = prices.count()
    valid_ticker_index = ticker_counts[ticker_counts >= MIN_REQUIRED_NUM_OBS_PER_TICKER].index
    return prices[valid_ticker_index]


def create_sp500_historical_prices(start_date: str = "2000-01-01", end_date: str = "2025-10-21") -> pd.DataFrame:
    """
    Return S&P 500 adjusted close prices between the provided dates.

    The data is cached to `historical_prices.csv` alongside this module to avoid
    hitting the Yahoo Finance API on every invocation.
    """
    data_path = Path(__file__).with_name("historical_prices.csv")

    if data_path.exists():
        print("Loading historical prices from local CSV file.")
        historical_prices = pd.read_csv(data_path, index_col=0, parse_dates=True)
    else:
        print("Downloading historical prices from Yahoo Finance.")
        sp500_tickers = _fetch_sp500_tickers()
        print(f"Searching {len(sp500_tickers)} tickers")

        historical_prices = yf.download(
            sp500_tickers,
            start=start_date,
            end=end_date,
            progress=False,
            group_by="ticker",
        )

        # Retain only close prices to minimise storage and match downstream expectations.
        historical_prices = historical_prices.loc[:, historical_prices.columns.get_level_values(0) == "Close"]
        historical_prices.columns = historical_prices.columns.droplevel(0)
        historical_prices.to_csv(data_path)

    filtered_prices = _filter_dense_tickers(historical_prices)
    print(filtered_prices.head())
    return filtered_prices
