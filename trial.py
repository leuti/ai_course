# import os
# import sys
# import pandas as pd
# import yfinance as yf
from ai_course import funct_lib as fl

# module_dir = Path.cwd() / "ai_course"  # adjust if you start IPython elsewhere
# if str(module_dir) not in sys.path:
#    sys.path.append(str(module_dir))
#
# import funct_lib as fl

# sp500_tickers = fl._fetch_sp500_tickers()  # Reuse our helper to grab the current ticker list.
# tickers = ['AAPL', 'MSFT', 'GOOGL']  # Shortened list for quicker testing.
# historical_prices = fl.create_ticker_hist_prices(tickers, start_date="2025-10-01", end_date="2025-10-24")
# OR
historical_prices = fl.create_sp500_historical_prices()

print(historical_prices.head())

list_of_momentums = [1]
total_returns = fl.computing_returns(historical_prices, list_of_momentums)

print(total_returns.head())

fl.compute_BM_perf(total_returns)
