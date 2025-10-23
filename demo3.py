import os
import sys
import pandas as pd

# Manually set the path to include the parent directory
func_lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'funct_lib'))

sys.path.append(func_lib_path)

import funct_lib as fl

historical_prices = fl.create_sp500_historical_prices()

print(historical_prices.head())

list_of_momentums = [1]
total_returns = fl.computing_returns(historical_prices, list_of_momentums)

print(total_returns.head()) 

# total_returns.index.get_level_values('Ticker').nunique  # Access the first level of the MultiIndex (dates) to verify structure.
# print(test.head())

fl.compute_BM_perf(total_returns)

