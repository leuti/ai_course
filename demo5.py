from ai_course import funct_lib as fl

historical_prices = fl.create_sp500_historical_prices()
list_of_momentums = [1]
total_returns = fl.computing_returns(historical_prices, list_of_momentums)
total_returns = total_returns.dropna()

cum_returns, calendar_returns = fl.compute_BM_perf(total_returns)

# Calculate RSI for eachticker separately and add to the DataFrame
total_returns["RSI"] = total_returns.groupby("Ticker")[["1_d_returns"]].transform(
    fl.calculate_rsi
)
