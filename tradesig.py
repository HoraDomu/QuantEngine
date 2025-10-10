import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy as sp



#this is just for checking price
user_input = input("Enter Ticker: ").upper() 
data = yf.download(user_input, period="ytd", auto_adjust = True)["Close"]
print(data)

#this will be for indicators like RSI,MACD, and moving averages

