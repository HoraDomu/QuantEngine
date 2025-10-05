import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy as sp
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score


class StockGraph:

    def __init__(self):
        pass

    def get_stock_data(self):
        ticker = input("Please Enter First Stock Ticker: ").upper()
        ticker2 = input("Please Enter Second Stock Ticker: ").upper()
        data = yf.download(ticker, period="ytd")
        data2 = yf.download(ticker2, period="ytd")

        if data.empty or data2.empty:
            print("No data found for one or both tickers.")
            return None, None, None, None

        print(data)
        print(data2)
        return data, data2, ticker, ticker2

    def show_data_on_graph(self, data, data2, ticker, ticker2):
        plt.figure(figsize=(10, 6), facecolor="black")
        plt.plot(data["Close"], color="red", label=ticker)
        plt.plot(data2["Close"], color="blue", label=ticker2)
        plt.xlabel("Date")
        plt.ylabel("Close Price")
        plt.title("Stock Closing Prices")
        plt.legend()
        plt.show()


if __name__ == "__main__":
    sg = StockGraph()
    data, data2, ticker, ticker2 = sg.get_stock_data()
    if data is not None and data2 is not None:
        sg.show_data_on_graph(data, data2, ticker, ticker2)
