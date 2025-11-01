from ai_course import funct_lib as fl

# Manually set the path to include the parent directory
# func_lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'funct_lib'))

# sys.path.append(func_lib_path)

# import funct_lib as fl

historical_prices = fl.create_sp500_historical_prices()

list_of_momentums = [1, 2]
fl.computing_returns(historical_prices, list_of_momentums)
