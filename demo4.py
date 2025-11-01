import pandas as pd
import matplotlib.pyplot as plt
from ai_course import funct_lib as fl

historical_prices = fl.create_sp500_historical_prices()
list_of_momentums = [1]
total_returns = fl.computing_returns(historical_prices, list_of_momentums)

returns = total_returns[
    "1_d_returns"
]  # Example: using 1-day returns for RSI calculation
returns = returns[
    returns.index.get_level_values(0) == "AAPL"
]  # Filter for a specific ticker, e.g., AAPL

# window = 2

total_returns["RSI"] = total_returns.groupby("Ticker")[["1_d_returns"]].transform(
    fl.calculate_rsi
)

# Plot
histogram_plot = total_returns[["RSI"]].hist(
    bins=50, ax=plt.gca(), color="skyblue", edgecolor="black"
)

# Customize the plot with title and labels
plt.title(
    "Distribution of Relative Strenght Index (RSI)", fontsize=16, fontweight="bold"
)  # Set the plot title.
plt.xlabel("RSI", fontsize=14)  # Label the x-axis as Date.
plt.ylabel("Frequency", fontsize=14)  # Label the y-axis as Cumulative Return.
plt.grid(True)  # Enable grid lines for better readability.

plt.show()

scatter_plot = total_returns.plot.scatter(
    x="RSI",
    y="F_1_d_returns",
    ax=plt.gca(),
    alpha=0.5,
    s=0.01,
    color="blue",
    edgecolor="black",
)

# Customize the plot with title and labels
plt.title(
    "RSI vs 1-Day Forward Return", fontsize=16, fontweight="bold"
)  # Set the plot title.
plt.xlabel("RSI", fontsize=14)  # Label the x-axis as Date.
plt.ylabel(
    "1-Day Forward Return", fontsize=14
)  # Label the y-axis as Cumulative Return.
plt.grid(True)  # Enable grid lines for better readability.

plt.show()

total_returns[["RSI", "F_1_d_returns"]].corr().style.background_gradient()

feature = "RSI"
target = "F_1_d_returns"

# Specify custom bin boundaries
bin_boundaries = [
    0,
    30,
    70,
    100,
]  # Example: Oversold (<30), Neutral (30-70), Overbought (>70)

total_returns["Quantiles"] = total_returns.groupby(level="Date")[feature].transform(
    lambda x: pd.cut(x, bins=bin_boundaries, labels=False, include_lowest=True)
)

quantiles_plot = (
    total_returns.groupby("Quantiles")[[target]].mean().plot(kind="bar", legend=True)
)

# Customize the plot with title and labels
plt.title("Quantiles", fontsize=16, fontweight="bold")  # Set the plot title.
plt.xlabel("RSI", fontsize=14)  # Label the x-axis as Date.
plt.ylabel("Quantiles", fontsize=14)  # Label the y-axis as Cumulative Return.
plt.grid(True)  # Enable grid lines for better readability.

plt.show()

total_returns[total_returns["RSI"] < 30].describe()
