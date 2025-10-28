from pathlib import Path  # pathlib.Path (Python stdlib) gives cross-platform filesystem path objects that replace raw strings.
import io  # io module (stdlib) enables treating strings/bytes as file-like streams, used for read_html parsing.

import pandas as pd  # pandas is the primary data analysis library; here we shorten the module name to pd by convention.
import requests  # requests is a third-party HTTP client (https://requests.readthedocs.io) used to download web content.
import yfinance as yf  # yfinance (https://pypi.org/project/yfinance/) wraps Yahoo Finance APIs to fetch market data.
import matplotlib.pyplot as plt  # matplotlib is the standard plotting library; pyplot module provides MATLAB-like plotting API.

USER_AGENT = "Mozilla/5.0"  # Spoof a modern browser User-Agent so Wikipedia serves the page without blocking the request.
S_AND_P_500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"  # URL where the current S&P 500 table lives.
MIN_REQUIRED_NUM_OBS_PER_TICKER = 100  # Minimum number of non-missing price observations we require for each ticker column.

def _fetch_sp500_tickers() -> list[str]:  # Leading underscore marks this helper as internal; return type lists ticker symbols.
    """Fetch the current S&P 500 ticker list from Wikipedia."""
    response = requests.get(  # requests.get issues an HTTP GET (source: requests library) and returns a Response object.
        S_AND_P_500_URL,  # Target the constant Wikipedia URL defined above.
        headers={"User-Agent": USER_AGENT},  # Send a custom header so the server treats us like a real browser.
        timeout=30,  # Fail the request if it takes longer than 30 seconds (requests' timeout parameter).
    )
    response.raise_for_status()  # Raise an HTTPError if the status code is 4xx/5xx (requests.Response API).
    sp500_tickers = pd.read_html(io.StringIO(response.text))[0]["Symbol"].tolist()  # pandas.read_html parses all tables from HTML text (wrapped in StringIO); take the first table, grab the Symbol column, convert to list of strings.
    # Drop B-class share suffix variants that often have sparse data.
    return [ticker for ticker in sp500_tickers if ".B" not in ticker]  # List comprehension filters out tickers ending with ".B" to avoid low-liquidity share classes.


def _filter_dense_tickers(prices: pd.DataFrame) -> pd.DataFrame:  # Helper expects a pandas DataFrame and returns another DataFrame.
    """Keep only tickers with sufficient observation count."""
    ticker_counts = prices.count()  # DataFrame.count() (pandas) tallies non-NA values for each column.
    valid_ticker_index = ticker_counts[ticker_counts >= MIN_REQUIRED_NUM_OBS_PER_TICKER].index  # Boolean mask keeps tickers meeting the minimum observation threshold and retrieves their column labels.
    return prices[valid_ticker_index]  # Subset the DataFrame to only those dense tickers by label selection.

def create_ticker_hist_prices(tickers, start_date: str = "2025-10-01", end_date: str = "2025-10-24") -> pd.DataFrame:  # Public API: optional ISO date strings; returns a pandas DataFrame.
    """
    Returns historical prices for requested tickers between the provided dates.

    The data is cached to `historical_prices_tickers.csv` alongside this module to avoid
    hitting the Yahoo Finance API on every invocation.
    """
    data_path = Path(__file__).with_name("historical_prices_tickers.csv")  # Path(__file__) builds a path to this file; with_name replaces the filename so cache sits next to the module.

    if data_path.exists():  # Path.exists() (pathlib) checks whether the CSV cache is already present.
        print("Loading historical prices from local CSV file.")  # Notify the user that we are using the cached dataset.
        historical_prices = pd.read_csv(data_path, index_col=0, parse_dates=True)  # pandas.read_csv loads the cached table, using the first column as the Date index and parsing to datetime objects.
    else:
        print("Downloading historical prices from Yahoo Finance.")  # Message for the slower path that hits the network.
        if tickers is None:
            tickers = _fetch_sp500_tickers()  # Reuse our helper to grab the current ticker list.
        print(f"Searching {len(tickers)} tickers")  # f-string reports how many tickers yfinance will request.

        historical_prices = yf.download(  # yfinance.download queries Yahoo's API for historical prices and returns a pandas DataFrame with a MultiIndex on columns.
            tickers,  # Provide the full ticker list to download all series at once.
            start=start_date,  # Lower bound for the historical period (yfinance accepts YYYY-MM-DD strings).
            end=end_date,  # Upper bound end date (exclusive) for the download.
            progress=True,  # Disable yfinance's progress bar so scripts/logs stay clean.
            group_by="ticker",  # Request data grouped by ticker so column index is (field, ticker).
        )

        # Retain only close prices to minimise storage and match downstream expectations.
        historical_prices = historical_prices.loc[:, historical_prices.columns.get_level_values(1) == "Close"]  # Use DataFrame.loc with a boolean mask on the top-level MultiIndex to keep only "Close" series.
        historical_prices.columns = historical_prices.columns.droplevel(1)  # Drop the top level ("Close") to leave plain ticker symbols as column labels.
        historical_prices.to_csv(data_path)  # Persist the prepared DataFrame to CSV so the next run can reuse it.

    # filtered_prices = _filter_dense_tickers(historical_prices)  # Apply the density filter regardless of cache path to ensure quality data.
    # print(filtered_prices.head())  # Uncomment for a quick preview of the filtered data during debugging.
    return historical_prices  # Return the filtered DataFrame to the caller for further processing.

def create_sp500_historical_prices(start_date: str = "2000-01-01", end_date: str = "2025-10-21") -> pd.DataFrame:  # Public API: optional ISO date strings; returns a pandas DataFrame.
    """
    Return S&P 500 adjusted close prices between the provided dates.

    The data is cached to `historical_prices.csv` alongside this module to avoid
    hitting the Yahoo Finance API on every invocation.
    """
    data_path = Path(__file__).with_name("historical_prices.csv")  # Path(__file__) builds a path to this file; with_name replaces the filename so cache sits next to the module.

    if data_path.exists():  # Path.exists() (pathlib) checks whether the CSV cache is already present.
        print("Loading historical prices from local CSV file.")  # Notify the user that we are using the cached dataset.
        historical_prices = pd.read_csv(data_path, index_col=0, parse_dates=True)  # pandas.read_csv loads the cached table, using the first column as the Date index and parsing to datetime objects.
    else:
        print("Downloading historical prices from Yahoo Finance.")  # Message for the slower path that hits the network.
        sp500_tickers = _fetch_sp500_tickers()  # Reuse our helper to grab the current ticker list.
        print(f"Searching {len(sp500_tickers)} tickers")  # f-string reports how many tickers yfinance will request.

        historical_prices = yf.download(  # yfinance.download queries Yahoo's API for historical prices and returns a pandas DataFrame with a MultiIndex on columns.
            sp500_tickers,  # Provide the full ticker list to download all series at once.
            start=start_date,  # Lower bound for the historical period (yfinance accepts YYYY-MM-DD strings).
            end=end_date,  # Upper bound end date (exclusive) for the download.
            progress=False,  # Disable yfinance's progress bar so scripts/logs stay clean.
            group_by="ticker",  # Request data grouped by ticker so column index is (field, ticker).
        )

        # Retain only close prices to minimise storage and match downstream expectations.
        historical_prices = historical_prices.loc[:, historical_prices.columns.get_level_values(1) == "Close"]  # Use DataFrame.loc with a boolean mask on the top-level MultiIndex to keep only "Close" series.
        historical_prices.columns = historical_prices.columns.droplevel(1)  # Drop the top level ("Close") to leave plain ticker symbols as column labels.
        filtered_prices = _filter_dense_tickers(historical_prices)  # Apply the density filter regardless of cache path to ensure quality data.
        filtered_prices.to_csv(data_path)  # Persist the prepared DataFrame to CSV so the next run can reuse it.

    # print(filtered_prices.head())  # Uncomment for a quick preview of the filtered data during debugging.
    return filtered_prices  # Return the filtered DataFrame to the caller for further processing.

def computing_returns(historical_prices, list_of_momentums):  # Function computes forward and momentum-based returns; parameters are expected pandas objects.
    """
    Input:  dataframe of historical prices
            list of momentums
    Output: returns dataframe with returns over the momentum list and one day forward return
    """
    
    # Initialize the forecast horizon
    forecast_horizon = 1  # Use a one-day lookahead to define how far forward we compute percentage changes.

    # compute the forward returns by taking the percentage change of close price
    f_returns = historical_prices.pct_change(forecast_horizon)  # DataFrame.pct_change(n) (pandas) computes percent change over n periods along the index.

    # We then shift the forward returns
    f_returns = f_returns.shift(-forecast_horizon)  # DataFrame.shift(-n) moves data upward so each row stores the future return aligned with the current date.
    
    # Pivot the returns dataframe to have a multi-index with date and ticker
    f_returns = pd.DataFrame(f_returns.unstack())  # Series/DataFrame.unstack() (pandas) pivots columns into a MultiIndex; wrapping with DataFrame makes sure we keep a 2D structure.
    f_returns.index.set_names(["Ticker", "Date"], inplace=True)  # Assign explicit names to the MultiIndex levels for clarity downstream.

    # Name the column based on the forecast horizon 
    name = "F_" + str(forecast_horizon) + "_d_returns"  # Build a descriptive column name like 'F_1_d_returns' using string concatenation.
    f_returns.rename(columns={0: name}, inplace=True)  # DataFrame.rename lets us replace the default column label (0) with our descriptive name.
    print(f_returns.head())  # Display the top rows to validate the transformation.

    # Initialise total_returns with forward returns
    total_returns = f_returns  # Start aggregating features into total_returns, beginning with the forward returns DataFrame.

    for i in list_of_momentums:  # Iterate through each momentum window specified by the caller.
        # Compute returns for each momentum value
        feature = historical_prices.pct_change(i)  # Calculate trailing percentage change over i periods using pandas pct_change.
        feature = pd.DataFrame(feature.unstack())  # Reshape the feature the same way as before so we can merge on (Ticker, Date).
        feature.index.set_names(["Ticker", "Date"], inplace=True)  # Align index level names with forward returns for consistent merging.

        # Name the column based on the momentum value
        name = str(i) + "_d_returns"  # Produce readable names like '5_d_returns' for each momentum window.
        feature.rename(columns={0: name}, inplace=True)  # Rename the value column so each feature has an informative label.

        # Merge the computed feature returns with total_returns based on ticker and date
        total_returns = pd.merge(total_returns, feature, left_index=True, right_index=True, how='outer')  # pandas.merge with outer join preserves rows even when some features are missing, aligning on the MultiIndex indices.

        # drop any rows with NaN values
        total_returns.dropna(axis=0, how="any", inplace=True)  # Drop rows containing any NaNs so downstream models receive complete data (DataFrame.dropna API).
        # print(total_returns.head())  # Show a snapshot after each merge to monitor the incremental feature set.

    return total_returns  # Return the final feature DataFrame with forward AND momentum-based returns.

def compute_BM_perf(total_returns):
    """
    Purpose: Compute benchmark performance for investment universe and return cumulative calendar returns.
    Input:  dataframe of total returns with forward and momentum returns
    """

    total_returns = total_returns.sort_index() # Ensure the DataFrame is sorted by the MultiIndex (Ticker, Date) for consistent processing.

    # Compute the daily mean of all stocks. This will be our equal weighted benchmark return.
    # daily_mean = pd.DataFrame(total_returns.loc[:"F_1_d_returns"].groupby(level="Date").mean())  # Group by Date level of the MultiIndex and average the forward return column across tickers for each date.
    daily_mean = pd.DataFrame(total_returns.loc[:, "F_1_d_returns"].groupby(level="Date").mean()) # Group by Date level of the MultiIndex and average the forward return column across tickers for each date.
    
    daily_mean.rename(columns={"F_1_d_returns": "S&P500"}, inplace=True)  # Rename the column to indicate these are benchmark daily returns.

    # Convert daily returns to cumulative returns
    cum_return = pd.DataFrame((daily_mean[["S&P500"]]+1).cumprod())  # Cumulative product of (1 + daily return) yields the value of a $1 investment through time.

    # Plot cumulative returns
    cum_return.plot()  # Use DataFrame.plot to visualize cumulative returns with a title.
    # Customize the plot with title and labels
    plt.title("Cumulative Returns over time", fontsize=16, fontweight="bold")  # Set the plot title.
    plt.xlabel("Date", fontsize=14)  # Label the x-axis as Date.
    plt.ylabel("Cumulative Return", fontsize=14)  # Label the y-axis as Cumulative Return.
    plt.grid(True)  # Enable grid lines for better readability.     
    plt.xticks(rotation=45)  # Rotate x-axis labels so overlapping dates remain readable.
    plt.legend(title_fontsize=13, fontsize=12)  # Set legend font size for clarity.

    # Calulate the number of years in the dataset
    number_of_years = len(daily_mean) / 252  # Assuming 252 trading days per year to convert total return to annualized return.

    ending_value = cum_return["S&P500"].iloc[-1]  # Get the final cumulative return value for the benchmark.
    beginning_value = cum_return["S&P500"].iloc[1]  # Use the first non-NaN cumulative value as the starting point for CAGR.

    # Compute the Compounded Annual Growth Rate (CAGR)
    ratio = ending_value / beginning_value  # Calculate the ratio of ending to beginning value.
    cagr = round((ratio ** (1 / number_of_years) - 1)*100,2)  # CAGR formula to annualize the return over the number of years.
    print(f"The CAGR of the S&P500 benchmark over the period is {cagr} %")

    # Compute the Sharpe Ratio
    average_daily_return = daily_mean[["S&P500"]].describe().iloc[1,:] * 252  # Annualize the mean of daily returns (describe row index 1).
    standard_dev_daily_return = daily_mean[["S&P500"]].describe().iloc[2,:] * pow(252, 1/2)  # Annualize the standard deviation (describe row index 2) using sqrt(252).
    
    sharp = average_daily_return / standard_dev_daily_return  # Sharpe ratio calculation.
    print(f"The Sharpe Ratio of the S&P500 benchmark over the period is {round(sharp.iloc[0],2)}")

    ann_returns = (pd.DataFrame((daily_mean[["S&P500"]]+1).groupby(daily_mean.index.get_level_values(0).year).cumprod())-1)*100  # Convert each year's cumulative growth into percentage returns.
    calendar_returns = pd.DataFrame(ann_returns["S&P500"].groupby(daily_mean.index.get_level_values(0).year).last())  # Extract last value of each year to get calendar-year returns.

    calendar_returns.plot.bar(rot=30, legend="top_left")  # Plot annual returns as a bar chart with rotated labels for readability.
    plt.show()  # Display the plot to the user.

    return cum_return  # Return the cumulative benchmark series (calendar returns kept for potential future use).
