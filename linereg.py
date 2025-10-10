import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import sys

ticker1 = input("Enter Ticker 1: ").upper()

try:
    data1 = yf.download(ticker1, period="6mo", auto_adjust=True)["Close"]
except Exception as e:
    print("Error downloading data:", e)
    sys.exit()

if data1.empty:
    print(f"No data found for {ticker1}")
    sys.exit()

df = pd.DataFrame(data1)
df.columns = [ticker1]
df.dropna(inplace=True)

if df.shape[0] < 2:
    print("Not enough data for regression.")
    sys.exit()

print(df.head())

y = df[ticker1].values
X = np.arange(len(y)).reshape(-1, 1)

model = LinearRegression()
model.fit(X, y)

print("\n--- Linear Regression Results ---")
print(f"Intercept (β0): {model.intercept_:.2f}")
print(f"Slope (β1): {model.coef_[0]:.2f}")
print(f"R^2 score: {model.score(X, y):.4f}")

plt.figure(figsize=(8, 6), facecolor="black")
plt.scatter(X, y, alpha=0.5, label="Data points")
plt.plot(X, model.predict(X), color="red", label="Regression line")
plt.ylabel(ticker1)
plt.xlabel("Time (days)")
plt.title(f"{ticker1} Linear Regression")
plt.legend()
plt.show()
