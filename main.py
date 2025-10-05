import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from scipy.stats import norm
import pandas as pd
import numpy as np
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from datetime import datetime, timedelta
import warnings
import yfinance as yf
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connected = False
        self.market_data = {}
        self.historical_data = {}

    def error(self, reqId, errorCode, errorString, *args):
        if errorCode == 2176 and "fractional share" in str(errorString).lower():
            return
        print(f"Error {errorCode}: {errorString}")

    def nextValidId(self, orderId):
        self.connected = True
        print("Connected to IBTWS (nextValidId)")

    def historicalData(self, reqId, bar):
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append(
            {
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
        )

    def historicalDataEnd(self, reqId, start, end):
        print(f"Historical data received for reqId {reqId}")


class VolatilityCrushAnalyzer:
    def __init__(self, parent):
        self.parent = parent
        self.ib_app = IBApp()
        self.connected = False
        self.current_spot = None
        self.current_iv = None
        self.ticker = None
        self.risk_free_rate = 0.05
        self.setup_ui()

    def create_equity_contract(self, symbol):
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def setup_ui(self):
        main_frame = ttk.Frame(self.parent, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        title_label = ttk.Label(
            main_frame,
            text=f"[Volatility Crush Analyzer]\n {datetime.now().strftime('[%Y-%m-%d] [%I:%M:%S %p]')}",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)

        self.setup_connection_section(left_frame, 0)
        self.setup_market_data_section(left_frame, 1)
        self.setup_current_straddle_section(left_frame, 2)
        self.setup_current_greeks_section(left_frame, 3)

        self.setup_scenario_section(right_frame, 0)
        self.setup_pnl_section(right_frame, 1)
        self.setup_new_greeks_section(right_frame, 2)
        self.setup_status_section(right_frame, 3)

    def setup_connection_section(self, parent, row):
        conn_frame = ttk.LabelFrame(parent, text="Interactive Brokers Connection", padding="15")
        conn_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        conn_frame.columnconfigure(1, weight=1)
        conn_frame.columnconfigure(3, weight=1)

        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(conn_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=(0, 15), sticky=(tk.W, tk.E))

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=(0, 5), sticky=(tk.W, tk.E))
        self.port_var = tk.StringVar(value="7497")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=(0, 15), sticky=(tk.W, tk.E))

        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))

        self.connect_btn = ttk.Button(button_frame, text="Connect to IB", command=self.connect_ib)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect", command=self.disconnect_ib, state="disabled")
        self.disconnect_btn.pack(side=tk.LEFT)

        self.status_label = ttk.Label(conn_frame, text="Disconnected")
        self.status_label.grid(row=2, column=0, columnspan=4, pady=(5, 0))

    def setup_market_data_section(self, parent, row):
        data_frame = ttk.LabelFrame(parent, text="Market Data & Parameters", padding="10")
        data_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        data_frame.columnconfigure(1, weight=1)

        ttk.Label(data_frame, text="Ticker:").grid(row=0, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        ticker_frame = ttk.Frame(data_frame)
        ticker_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8))
        ticker_frame.columnconfigure(0, weight=1)

        self.ticker_var = tk.StringVar(value="Enter Ticker Here")
        ttk.Entry(ticker_frame, textvariable=self.ticker_var, width=16, font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.fetch_btn = ttk.Button(ticker_frame, text="Fetch Data", command=self.fetch_market_data, state="disabled")
        self.fetch_btn.pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Label(data_frame, text="Spot Price:").grid(row=1, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.spot_price_var = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.spot_price_var, width=15, font=("Arial", 10, "bold")).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 8))

        ttk.Label(data_frame, text="Strike Price:").grid(row=2, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.strike_var = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.strike_var, width=15, font=("Arial", 10, "bold")).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 8))

        ttk.Label(data_frame, text="IV (%):").grid(row=3, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.iv_var = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.iv_var, width=15, font=("Arial", 10, "bold")).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 8))

        ttk.Label(data_frame, text="Days to Expiry:").grid(row=4, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.days_var = tk.StringVar(value="30")
        ttk.Entry(data_frame, textvariable=self.days_var, width=15, font=("Arial", 10, "bold")).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(0, 8))

        self.price_btn = ttk.Button(data_frame, text="Price Straddle", command=self.price_current_straddle, state="disabled")
        self.price_btn.grid(row=5, column=0, columnspan=2, padx=(10, 0))

    def setup_current_straddle_section(self, parent, row):
        pricing_frame = ttk.LabelFrame(parent, text="Current Straddle Price", padding="10")
        pricing_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        pricing_frame.columnconfigure(1, weight=1)

        ttk.Label(pricing_frame, text="Call Price:").grid(row=0, column=0, padx=(0, 10), pady=(0, 5), sticky=tk.W)
        self.call_price_label = ttk.Label(pricing_frame, text="$0.00", font=("Arial", 11, "bold"))
        self.call_price_label.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(pricing_frame, text="Put Price:").grid(row=1, column=0, padx=(0, 10), pady=(0, 5), sticky=tk.W)
        self.put_price_label = ttk.Label(pricing_frame, text="$0.00", font=("Arial", 11, "bold"))
        self.put_price_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        separator = ttk.Separator(pricing_frame, orient="horizontal")
        separator.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)

        ttk.Label(pricing_frame, text="Straddle Price:").grid(row=3, column=0, padx=(0, 10), pady=(0, 5), sticky=tk.W)
        self.straddle_price_label = ttk.Label(pricing_frame, text="$0.00", font=("Arial", 14, "bold"))
        self.straddle_price_label.grid(row=3, column=1, sticky=tk.W, pady=(0, 5))

    def setup_current_greeks_section(self, parent, row):
        greeks_frame = ttk.LabelFrame(parent, text="Current Greeks", padding="10")
        greeks_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        greeks_frame.columnconfigure(1, weight=1)
        greeks_frame.columnconfigure(3, weight=1)

        ttk.Label(greeks_frame, text="Delta:").grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.delta_label = ttk.Label(greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.delta_label.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(greeks_frame, text="Gamma:").grid(row=0, column=2, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.gamma_label = ttk.Label(greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.gamma_label.grid(row=0, column=3, sticky=tk.W, pady=(0, 5))

        ttk.Label(greeks_frame, text="Vega:").grid(row=1, column=0, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.vega_label = ttk.Label(greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.vega_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(greeks_frame, text="Theta:").grid(row=1, column=2, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.theta_label = ttk.Label(greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.theta_label.grid(row=1, column=3, sticky=tk.W, pady=(0, 5))

    def setup_scenario_section(self, parent, row):
        scenario_frame = ttk.LabelFrame(parent, text="Scenario Analysis", padding="10")
        scenario_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        scenario_frame.columnconfigure(1, weight=1)

        ttk.Label(scenario_frame, text="New Spot Price:").grid(row=0, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.new_spot_price = tk.StringVar()
        ttk.Entry(scenario_frame, textvariable=self.new_spot_price, width=15, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8))

        ttk.Label(scenario_frame, text="New IV (%):").grid(row=1, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.new_iv_var = tk.StringVar()
        ttk.Entry(scenario_frame, textvariable=self.new_iv_var, width=15, font=("Arial", 10, "bold")).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 8))

        self.analyze_btn = ttk.Button(scenario_frame, text="Analyze Scenario", command=self.analyze_scenario, state="disabled")
        self.analyze_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    def setup_pnl_section(self, parent, row):
        pnl_frame = ttk.LabelFrame(parent, text="P/L Analysis", padding="10")
        pnl_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        pnl_frame.columnconfigure(1, weight=1)

        ttk.Label(pnl_frame, text="New Straddle Price:").grid(row=0, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.new_straddle_label = ttk.Label(pnl_frame, text="$0.00", font=("Arial", 12, "bold"))
        self.new_straddle_label.grid(row=0, column=1, sticky=tk.W, pady=(0, 8))

        separator = ttk.Separator(pnl_frame, orient="horizontal")
        separator.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)

        ttk.Label(pnl_frame, text="Long Straddle P/L:").grid(row=2, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.pnl_long_label = ttk.Label(pnl_frame, text="$0.00", font=("Arial", 12, "bold"))
        self.pnl_long_label.grid(row=2, column=1, sticky=tk.W, pady=(0, 8))

        ttk.Label(pnl_frame, text="Short Straddle P/L:").grid(row=3, column=0, padx=(0, 10), pady=(0, 8), sticky=tk.W)
        self.pnl_short_label = ttk.Label(pnl_frame, text="$0.00", font=("Arial", 12, "bold"))
        self.pnl_short_label.grid(row=3, column=1, sticky=tk.W)

    def setup_new_greeks_section(self, parent, row):
        new_greeks_frame = ttk.LabelFrame(parent, text="New Scenario Greeks", padding="10")
        new_greeks_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        new_greeks_frame.columnconfigure(1, weight=1)
        new_greeks_frame.columnconfigure(3, weight=1)

        ttk.Label(new_greeks_frame, text="Delta:").grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.new_delta_label = ttk.Label(new_greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.new_delta_label.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(new_greeks_frame, text="Gamma:").grid(row=0, column=2, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.new_gamma_label = ttk.Label(new_greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.new_gamma_label.grid(row=0, column=3, sticky=tk.W, pady=(0, 5))

        ttk.Label(new_greeks_frame, text="Vega:").grid(row=1, column=0, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.new_vega_label = ttk.Label(new_greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.new_vega_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        ttk.Label(new_greeks_frame, text="Theta:").grid(row=1, column=2, padx=(0, 5), pady=(0, 5), sticky=tk.W)
        self.new_theta_label = ttk.Label(new_greeks_frame, text="0.00", font=("Arial", 10, "bold"))
        self.new_theta_label.grid(row=1, column=3, sticky=tk.W, pady=(0, 5))

    def setup_status_section(self, parent, row):
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)

        self.status_var = tk.StringVar(value="Ready to connect to Interactive Brokers...")
        self.status_display = ttk.Label(status_frame, textvariable=self.status_var, wraplength=300, justify=tk.LEFT, font=("Arial", 9))
        self.status_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N))

    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {message}")
        self.parent.update_idletasks()

    def connect_ib(self):
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            self.update_status(f"Connecting to IB at {host}:{port}")

            def connect_thread():
                try:
                    self.ib_app.connect(host, port, 0)
                    self.ib_app.run()
                except Exception as e:
                    self.update_status(f"Connection error: {e}")

            thread = threading.Thread(target=connect_thread, daemon=True)
            thread.start()

            for i in range(50):
                if self.ib_app.connected:
                    break
                time.sleep(0.1)

            if self.ib_app.connected:
                self.connected = True
                self.connect_btn.config(state="disabled")
                self.disconnect_btn.config(state="normal")
                self.fetch_btn.config(state="normal")
                self.price_btn.config(state="normal")
                self.status_label.config(text="Connected")
                self.update_status("Successfully connected to IB TWS")
            else:
                self.update_status("Failed to connect to IB TWS (nextValidId not received)")
        except Exception as e:
            self.update_status(f"Connection Error: {e}")

    def disconnect_ib(self):
        try:
            if hasattr(self, "ib_app") and self.ib_app:
                self.ib_app.disconnect()
            self.connected = False
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.fetch_btn.config(state="disabled")
            self.price_btn.config(state="disabled")
            self.analyze_btn.config(state="disabled")
            self.status_label.config(text="Disconnected")
            self.clear_data()
            self.update_status("Disconnected from IB TWS")
        except Exception as e:
            self.update_status(f"Disconnect error {e}")

    def clear_data(self):
        self.current_spot = None
        self.current_iv = None
        self.call_price_label.config(text="$0.00")
        self.put_price_label.config(text="$0.00")
        self.straddle_price_label.config(text="$0.00")
        for lbl in [
            self.delta_label,
            self.gamma_label,
            self.vega_label,
            self.theta_label,
            self.new_straddle_label,
            self.pnl_long_label,
            self.pnl_short_label,
            self.new_delta_label,
            self.new_gamma_label,
            self.new_vega_label,
            self.new_theta_label,
        ]:
            lbl.config(text="0.00")
        self.spot_price_var.set("")
        self.strike_var.set("")
        self.iv_var.set("")
        self.new_spot_price.set("")
        self.new_iv_var.set("")
        if hasattr(self, "ib_app") and self.ib_app:
            self.ib_app.historical_data.clear()

    def fetch_market_data(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to Interactive Brokers")
            return
        self.ticker = self.ticker_var.get().upper()
        self.update_status(f"Fetching historical data for {self.ticker}...")
        self.ib_app.market_data.clear()
        self.ib_app.historical_data.clear()
        contract = self.create_equity_contract(self.ticker)
        end_date = datetime.now()
        try:
            self.ib_app.reqHistoricalData(
                reqId=1,
                contract=contract,
                endDateTime=end_date.strftime("%Y%m%d %H:%M:%S"),
                durationStr="5 D",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[],
            )
        except Exception as e:
            self.update_status(f"Error requesting price data {e}")

        try:
            self.ib_app.reqHistoricalData(
                reqId=2,
                contract=contract,
                endDateTime=end_date.strftime("%Y%m%d %H:%M:%S"),
                durationStr="5 D",
                barSizeSetting="1 day",
                whatToShow="OPTION_IMPLIED_VOLATILITY",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[],
            )
        except Exception as e:
            self.update_status(f"Error requesting IV data {e}")

        self.parent.after(3000, self.process_market_data)

    def process_market_data(self):
        if 1 in self.ib_app.historical_data and len(self.ib_app.historical_data[1]) > 0:
            price_data = self.ib_app.historical_data[1]
            latest_bar = price_data[-1]
            self.current_spot = latest_bar["close"]
            self.update_status(f"Latest closing price: ${self.current_spot:.2f}")
        else:
            self.update_status("No historical price data received")
            return

        if 2 in self.ib_app.historical_data and len(self.ib_app.historical_data[2]) > 0:
            iv_data = self.ib_app.historical_data[2]
            latest_iv = iv_data[-1]
            self.current_iv = latest_iv["close"]
            iv_display = self.current_iv * 100 if self.current_iv <= 1 else self.current_iv
            self.update_status(f"Latest IV data: {iv_display:.2f}%")
        else:
            self.update_status("No historical IV data received")
            return

        self.spot_price_var.set(f"{self.current_spot:.2f}")
        self.strike_var.set(f"{self.current_spot:.2f}")
        iv_display = self.current_iv * 100 if self.current_iv <= 1 else self.current_iv
        self.iv_var.set(f"{iv_display:.4f}")
        self.price_current_straddle()

    def price_current_straddle(self):
        try:
            spot_price = float(self.spot_price_var.get())
            strike_price = float(self.strike_var.get())
            iv_percent = float(self.iv_var.get())
            days_to_expiry = int(self.days_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for all parameters")
            return

        iv_decimal = iv_percent / 100.0
        T = days_to_expiry / 365.0
        r = self.risk_free_rate

        call_price = self.black_scholes_call(spot_price, strike_price, T, r, iv_decimal)
        put_price = self.black_scholes_put(spot_price, strike_price, T, r, iv_decimal)
        straddle_price = call_price + put_price

        delta = (
            self.calculate_delta(spot_price, strike_price, T, r, iv_decimal, "call")
            + self.calculate_delta(spot_price, strike_price, T, r, iv_decimal, "put")
        )
        gamma = self.calculate_gamma(spot_price, strike_price, T, r, iv_decimal)
        vega = self.calculate_vega(spot_price, strike_price, T, r, iv_decimal) * 2
        theta = (
            self.calculate_theta(spot_price, strike_price, T, r, iv_decimal, "call")
            + self.calculate_theta(spot_price, strike_price, T, r, iv_decimal, "put")
        )

        self.call_price_label.config(text=f"${call_price:.2f}")
        self.put_price_label.config(text=f"${put_price:.2f}")
        self.straddle_price_label.config(text=f"${straddle_price:.2f}")

        self.delta_label.config(text=f"{delta:.3f}")
        self.gamma_label.config(text=f"{gamma:.3f}")
        self.vega_label.config(text=f"{vega:.2f}")
        self.theta_label.config(text=f"{theta:.4f}")

        self.analyze_btn.config(state="normal")

        if not self.new_spot_price.get():
            self.new_spot_price.set(f"{spot_price:.2f}")
        if not self.new_iv_var.get():
            self.new_iv_var.set(f"{iv_percent:.2f}")

        self.update_status(f"Straddle priced: ${straddle_price:.2f} (Call: ${call_price:.2f} + Put: ${put_price:.2f})")

    def analyze_scenario(self):
        try:
            new_spot = float(self.new_spot_price.get())
            new_iv_percent = float(self.new_iv_var.get())
            new_iv = new_iv_percent / 100.0
        except ValueError:
            messagebox.showerror("Error", "Invalid spot price or IV values")
            return

        try:
            K = float(self.strike_var.get())
            days_to_expiry = int(self.days_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid strike price or days to expiry")
            return

        T = days_to_expiry / 365.00
        r = self.risk_free_rate

        new_call_price = self.black_scholes_call(new_spot, K, T, r, new_iv)
        new_put_price = self.black_scholes_put(new_spot, K, T, r, new_iv)
        new_straddle_price = new_call_price + new_put_price

        original_straddle_price = float(str(self.straddle_price_label.cget("text")).replace("$", ""))

        pnl_long = new_straddle_price - original_straddle_price
        pnl_short = -pnl_long

        self.new_straddle_label.config(text=f"${new_straddle_price:.2f}")

        long_color = "green" if pnl_long > 0 else "red"
        short_color = "green" if pnl_short > 0 else "red"

        self.pnl_long_label.config(text=f"{pnl_long:+.2f}", foreground=long_color)
        self.pnl_short_label.config(text=f"{pnl_short:+.2f}", foreground=short_color)

        new_delta = (
            self.calculate_delta(new_spot, K, T, r, new_iv, "call")
            + self.calculate_delta(new_spot, K, T, r, new_iv, "put")
        )
        new_gamma = self.calculate_gamma(new_spot, K, T, r, new_iv)
        new_vega = self.calculate_vega(new_spot, K, T, r, new_iv) * 2
        new_theta = (
            self.calculate_theta(new_spot, K, T, r, new_iv, "call")
            + self.calculate_theta(new_spot, K, T, r, new_iv, "put")
        )

        self.new_delta_label.config(text=f"{new_delta:.3f}")
        self.new_gamma_label.config(text=f"{new_gamma:.3f}")
        self.new_vega_label.config(text=f"{new_vega:.2f}")
        self.new_theta_label.config(text=f"{new_theta:.4f}")

        self.update_status(f"Scenario complete: New price ${new_straddle_price:.2f}")

    def black_scholes_call(self, S, K, T, r, sigma):
        if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    def black_scholes_put(self, S, K, T, r, sigma):
        if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    def calculate_delta(self, S, K, T, r, sigma, option_type="call"):
        if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        if option_type == "call":
            return norm.cdf(d1)
        else:
            return -norm.cdf(-d1)

    def calculate_gamma(self, S, K, T, r, sigma):
        if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))

    def calculate_vega(self, S, K, T, r, sigma):
        if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T)

    def calculate_theta(self, S, K, T, r, sigma, option_type="call"):
        if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type == "call":
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365.0
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365.0
        return theta


class StockScout:
    def __init__(self, parent):
        self.parent = parent
        self.label = tk.Label(parent, text="Enter Stock Ticker:", font=("Arial", 12))
        self.label.pack(pady=10)
        self.entry = tk.Entry(parent, font=("Arial", 12))
        self.entry.pack(pady=5)
        self.button = tk.Button(parent, text="Get Ticker History", command=self.get_stock_data)
        self.button.pack(pady=10)

    def get_stock_data(self):
        ticker = self.entry.get().upper()
        if not ticker:
            messagebox.showwarning("Input Error", "Please enter a stock ticker")
            return
        daily_data = yf.download(ticker, period="ytd", interval="1d")
        if daily_data.empty:
            messagebox.showerror("Data Error", f"No daily data found for {ticker}")
            return
        intraday_data = yf.download(ticker, period="1d", interval="5m")
        if intraday_data.empty:
            messagebox.showerror("Data Error", f"No intraday data found for {ticker}")
            return
        print("*Daily YTD Data*")
        print(daily_data.tail())
        print("\n**Intraday Data (Today)**")
        print(intraday_data.tail())
        plt.figure(figsize=(10, 4), facecolor = 'black')
        plt.plot(daily_data["Close"], label="YTD Daily")
        plt.title(f"{ticker} - Daily YTD Close")
        plt.legend()
        plt.show()
        plt.figure(figsize=(10, 4), facecolor = 'black')
        plt.plot(intraday_data["Close"], label="Intraday 5m")
        plt.title(f"{ticker} - Intraday Close")
        plt.legend()
        plt.show()


class Comparetwo:
    def __init__(self, parent):
        self.parent = parent
        self.label = tk.Label(parent, text="Ticker 1:", font=("Arial", 12))
        self.label.pack(pady=5)
        self.entry1 = tk.Entry(parent, font=("Arial", 12))
        self.entry1.pack(pady=5)
        self.label2 = tk.Label(parent, text="Ticker 2:", font=("Arial", 12))
        self.label2.pack(pady=5)
        self.entry2 = tk.Entry(parent, font=("Arial", 12))
        self.entry2.pack(pady=5)
        self.button = tk.Button(parent, text="Compare Two Tickers", command=self.compare_two)
        self.button.pack(pady=10)

    def compare_two(self):
        t1 = self.entry1.get().upper()
        t2 = self.entry2.get().upper()
        if not t1 or not t2:
            messagebox.showwarning("Input Error", "Please enter two tickers")
            return
        data1 = yf.download(t1, period="ytd", interval="1d")
        data2 = yf.download(t2, period="ytd", interval="1d")
        if data1.empty or data2.empty:
            messagebox.showerror("Data Error", "No data found for one or both tickers.")
            return
        plt.figure(figsize=(10, 6), facecolor = 'black')
        plt.plot(data1["Close"], label=t1)
        plt.plot(data2["Close"], label=t2)
        plt.xlabel("Date")
        plt.ylabel("Close Price")
        plt.title("Stock Closing Prices")
        plt.legend()
        plt.show()

class LineReg:
    def __init__(self, parent):
        self.parent = parent
        self.label = tk.Label(parent, text="Ticker:", font=("Arial", 12))
        self.label.pack(pady=5)
        self.entry = tk.Entry(parent, font=("Arial", 12))
        self.entry.pack(pady=5)
        self.button = tk.Button(parent, text="Run Linear Regression", command=self.run_line_reg)
        self.button.pack(pady=10)

    def run_line_reg(self):
        import sys
        from sklearn.linear_model import LinearRegression

        ticker = self.entry.get().upper()
        if not ticker:
            messagebox.showwarning("Input Error", "Please enter a ticker")
            return

        try:
            data = yf.download(ticker, period="6mo", auto_adjust=True)["Close"]
        except Exception as e:
            messagebox.showerror("Download Error", f"Error downloading data: {e}")
            return

        if data.empty:
            messagebox.showerror("Data Error", f"No data found for {ticker}")
            return

        df = pd.DataFrame(data)
        df.columns = [ticker]
        df.dropna(inplace=True)

        if df.shape[0] < 2:
            messagebox.showerror("Data Error", "Not enough data for regression")
            return

        y = df[ticker].values
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
        plt.ylabel(ticker)
        plt.xlabel("Time (days)")
        plt.title(f"{ticker} Linear Regression")
        plt.legend()
        plt.show()


    


def main():
    root = tk.Tk()
    root.title("All-in-One Trading Tool")
    root.geometry("1300x1300")

    vca_frame = ttk.Frame(root)
    vca_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    VolatilityCrushAnalyzer(vca_frame)

    scout_frame = ttk.Frame(root)
    scout_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    StockScout(scout_frame)

    compare_frame = ttk.Frame(root)
    compare_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    Comparetwo(compare_frame)

    run_line_reg_frame = ttk.Frame(root)
    run_line_reg_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    LineReg(run_line_reg_frame)

    root.mainloop()


if __name__ == "__main__":
    main()

