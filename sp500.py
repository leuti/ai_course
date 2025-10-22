import os
import sys

# Manually set the path to include the parent directory
func_lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'funct_lib'))

sys.path.append(func_lib_path)

import funct_lib as fl

historical_prices = fl.create_sp500_historical_prices()

print(historical_prices.head())