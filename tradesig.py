import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

user_input = input("Enter Ticker: ").upper()
data = yf.download(user_input, period="ytd", auto_adjust=True)[["Close"]].copy()

data["SMA_20"] = data["Close"].rolling(window=20).mean()
data["SMA_50"] = data["Close"].rolling(window=50).mean()

delta = data["Close"].diff().squeeze()
gain = pd.Series(np.where(delta > 0, delta, 0), index=data.index)
loss = pd.Series(np.where(delta < 0, -delta, 0), index=data.index)

avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

short_ema = data["Close"].ewm(span=12, adjust=False).mean()
long_ema = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"] = short_ema - long_ema
data["Signal_Line"] = data["MACD"].ewm(span=9, adjust=False).mean()

data["Buy_Signal"] = (data["SMA_20"] > data["SMA_50"]) & (data["SMA_20"].shift(1) <= data["SMA_50"].shift(1)) & (data["RSI"] < 40)
data["Sell_Signal"] = (data["SMA_20"] < data["SMA_50"]) & (data["SMA_20"].shift(1) >= data["SMA_50"].shift(1)) & (data["RSI"] > 60)

print("\nRecent Buy/Sell Signals:")
print(data.loc[data["Buy_Signal"] | data["Sell_Signal"], ["Close", "SMA_20", "SMA_50", "RSI", "Buy_Signal", "Sell_Signal"]].tail())

plt.figure(figsize=(12, 8))
plt.style.use('default')
ax = plt.gca()

ax.plot(data["Close"], label="Close Price", color="gray")
ax.plot(data["SMA_20"], label="SMA_20", alpha=0.8)
ax.plot(data["SMA_50"], label="SMA_50", alpha=0.8)

ax.scatter(data.index[data["Buy_Signal"]], data["Close"][data["Buy_Signal"]], marker="^", color="green", label="Buy Signal", s=100)
ax.scatter(data.index[data["Sell_Signal"]], data["Close"][data["Sell_Signal"]], marker="v", color="red", label="Sell Signal", s=100)

plt.title(f"{user_input} - Trade Signals (YTD)")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()
plt.grid(True)
plt.show()


