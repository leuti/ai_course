import os
import sys
import pandas as pd
import yfinance as yf
from pathlib import Path


module_dir = Path.cwd() / "ai_course"  # adjust if you start IPython elsewhere
if str(module_dir) not in sys.path:
    sys.path.append(str(module_dir))

import funct_lib as fl


# sp500_tickers = fl._fetch_sp500_tickers()  # Reuse our helper to grab the current ticker list.
tickers = ['AAPL', 'MSFT', 'GOOGL']  # Shortened list for quicker testing.

print(f"Searching {len(tickers)} tickers")  # f-string reports how many tickers yfinance will request.

historical_prices = fl.create_ticker_hist_prices(tickers, start_date="2025-10-01", end_date="2025-10-24")

print(historical_prices.head())

# historical_prices = fl.create_sp500_historical_prices()

# print(historical_prices.head())
