Overview

The Quant Engine is a Python-based financial analysis tool designed to analyze volatility crush scenarios — situations where implied volatility drops sharply after major events such as earnings reports.

It connects to Interactive Brokers (IBKR) Trader Workstation (TWS) to fetch real-time and historical market data, calculate option straddles, and model the impact of changes in spot price and implied volatility (IV) on profit and loss (P/L).

The engine provides both a graphical interface (Tkinter GUI) and quantitative back-end for pricing, analysis, and visualization.

⚙️ Features

IBKR TWS Integration – Real-time connection for market and volatility data.

Automated Data Fetching – Historical prices and IV pulled via Interactive Brokers API or fallback to Yahoo Finance.

Black-Scholes Pricing – Calculates the fair value of call and put options.

Straddle Pricing – Combines both legs (call + put) for volatility-based trade setups.

Greek Calculations – Computes Delta, Gamma, Vega, and Theta.

Scenario Analysis – Tests how changes in IV or price affect a straddle’s P/L.

GUI Dashboard – Interactive layout built using tkinter and ttk.

📊 What is a Quant Engine?

A quantitative engine (or quant engine) is a program that applies mathematical and statistical models to financial data for:

Market forecasting

Risk analysis

Option pricing

Signal generation

This particular engine focuses on options volatility modeling — specifically volatility crush opportunities often seen around earnings or news events.

🔑 Key Terms Explained
Ticker

A ticker is a unique symbol used to represent a stock, ETF, or other traded asset.
For example:

AAPL → Apple Inc.

TSLA → Tesla, Inc.

SPY → S&P 500 ETF

In the app, you enter a ticker to fetch market and volatility data for that asset.

Spot Price

The spot price is the current market price of an asset — the price at which it can be bought or sold immediately.

Example:
If AAPL is trading at $175.50, that’s its spot price.

Strike Price

The strike price is the predetermined price at which an option can be exercised.

A call option gives the right to buy at the strike.

A put option gives the right to sell at the strike.

Implied Volatility (IV)

Implied volatility (IV) measures how much the market expects a stock’s price to move in the future.
High IV = big expected moves (more expensive options)
Low IV = calm market (cheaper options)

A volatility crush occurs when IV drops sharply — for example, right after earnings.

Straddle

A straddle is an options strategy where you buy (or sell) both a call and put at the same strike price and expiration date.
It profits from large moves in price or changes in volatility.

Long Straddle – Buy both options (expecting a big move).

Short Straddle – Sell both options (expecting little movement).

Greeks

The Greeks are measures of an option’s sensitivity to different variables.

Greek	Description	Meaning
Δ (Delta)	Sensitivity to price movement	How much the option price changes when the underlying moves $1
Γ (Gamma)	Sensitivity of Delta	How fast Delta itself changes
V (Vega)	Sensitivity to volatility	How much the option’s price changes when IV moves 1%
Θ (Theta)	Sensitivity to time decay	How much value the option loses per day as time passes
Linear Regression

Linear regression is a statistical technique used to model the relationship between two or more variables.
In quant finance, it can be used for:

Predicting asset returns based on historical data

Estimating price trends

Correlating indicators with performance

For example, a regression might predict stock returns based on market volatility or volume.

🧩 Technical Stack

Python 3.10+

Tkinter / ttk – GUI framework

Interactive Brokers API (ibapi) – Data and connection handling

yFinance – Backup data source

NumPy / SciPy – Quantitative computation

Matplotlib – Visualization and charting

Pandas – Data manipulation and structure

🚀 How It Works

Connect to IBKR TWS – Establish a data connection.

Enter a Ticker – Fetch the last 5 days of historical price and implied volatility.

Calculate Straddle – Automatically prices options using the Black-Scholes model.

Analyze Scenarios – Adjust IV or spot price to see P/L changes in real time.

Visualize – Optional plotting of price or volatility trends.

|TO RUN|
Simply copy the code from main.py into a IDE of choice, mine is Lite-XL, install the required modules from requirements by typing "python -m pip install (and copy and paste the requirements here)". Then simply save and run via terminal using "py main.py"
​

🧠 Future Additions

Backtesting engine

Trade signal generator

Linear regression predictor module

Real-time volatility surface plotting

Automatic order execution via IBKR API

🧾 License

This project is licensed under the MIT License.

👨‍💻 Author

Dom Shark
Software Engineer & Quantitative Developer
📈 Building intelligent trading systems with data-driven models.

Would you like me to make a version of this README.md formatted in Markdown (with perfect GitHub-style formatting and headers) so you can drop it straight into your repo?

*Dev Log If interested*
https://www.youtube.com/playlist?list=PL6vBecjfHtv2wSVMdiO5JoK-nWIL_Z7Bk
