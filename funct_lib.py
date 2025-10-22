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


def computing_returns(historical_prices, list_of_momentums):
    """
    Input:  dataframe of historical prices
            list of momentums
    Output: returns dataframe with returns over the momentum list and one day forward return
    """
    
    # Initialize the forecast horizon
    forecast_horizon = 1

    # compute the forward returns by taking the percentage change of close price
    f_returns = historical_prices.pct_change(forecast_horizon)

    # print(f_returns["AAPL"].head())
    # print(f_returns.head())

    # We then shift the forward returns
    f_returns = f_returns.shift(-forecast_horizon)
    # print(f_returns.iloc[:,0:10].head())

    # Pivot the returns dataframe to have a multi-index with date and ticker
    f_returns = pd.DataFrame(f_returns.unstack())

    # Name the column based on the forecast horizon 
    name = "F_" + str(forecast_horizon) + "_d_returns"
    f_returns.rename(columns={0: name}, inplace=True)
    print(f_returns.head())

    # Initialise total_returns with forward returns
    total_returns = f_returns

    for i in list_of_momentums:
        # Compute returns for each momentum value
        feature = historical_prices.pct_change(i)
        feature = pd.DataFrame(feature.unstack())

        # Name the column based on the momentum value
        name = str(i) + "_d_returns"
        feature.rename(columns={0: name, "level_0": "Ticker"}, inplace=True)

        # Merge the computed feature returns with total_returns based on ticker and date
        total_returns = pd.merge(total_returns, feature, left_index=True, right_index=True, how='outer')

        # drop any rows with NaN values
        total_returns.dropna(axis=0, how="any", inplace=True)
        print(total_returns.head())

    return total_returns
