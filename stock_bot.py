# Imports
import yfinance as yf
import pandas as pd
import numpy as np
import logging
import alpaca_trade_api as tradeapi
from datetime import datetime

# Alpaca API keys
API_KEY = 'your_api_key_here'
SECRET_KEY = 'your_secret_key_here'
BASE_URL = 'https://paper-api.alpaca.markets'

# Connect to Alpaca
api = tradeapi.REST(
    API_KEY,
    SECRET_KEY,
    BASE_URL,
    api_version='v2'
)

# Download Apple stock data
data = yf.download(
    "AAPL",
    start="2022-01-01",
    end="2022-12-31"
)

# Calculate indicators
def calculate_indicators(data):

    # Short EMA
    data['EMA_12'] = data['Close'].ewm(
        span=12,
        adjust=False
    ).mean()

    # Long EMA
    data['EMA_26'] = data['Close'].ewm(
        span=26,
        adjust=False
    ).mean()

    # Price change
    delta = data['Close'].diff()

    # Avg gains
    gain = (
        delta.where(delta > 0, 0)
        .rolling(window=14)
        .mean()
    )

    # Avg losses
    loss = (
        -delta.where(delta < 0, 0)
        .rolling(window=14)
        .mean()
    )

    # RSI calculation
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    return data


# Add indicators
data = calculate_indicators(data)


# Create buy/sell signals
def generate_signals(data):

    # Default signal
    data['Signal'] = 0

    # Buy condition
    buy_signal = (
        (data['EMA_12'] > data['EMA_26']) &
        (data['RSI'] < 30)
    )

    # Sell condition
    sell_signal = (
        (data['EMA_12'] < data['EMA_26']) &
        (data['RSI'] > 70)
    )

    # Set signals
    data.loc[buy_signal, 'Signal'] = 1
    data.loc[sell_signal, 'Signal'] = -1

    # Keep last position
    data['Position'] = data['Signal'].replace(
        to_replace=0,
        method='ffill'
    )

    return data


# Generate signals
data = generate_signals(data)


# Backtesting function
def backtest(data, initial_balance=10000):

    # Starting money
    balance = initial_balance

    # Shares owned
    position = 0

    # Risk settings
    stop_loss = 0.95
    take_profit = 1.10

    # Buy price
    entry_price = 0

    # Loop through days
    for i, row in data.iterrows():

        # Buy stock
        if row['Signal'] == 1 and balance != 0:

            position = balance / row['Close']
            balance = 0
            entry_price = row['Close']

            logging.info(
                f"BUY at {row['Close']} "
                f"on {row.name.date()}"
            )

        # Sell stock
        elif row['Signal'] == -1 and position != 0:

            balance = position * row['Close']
            position = 0

            logging.info(
                f"SELL at {row['Close']} "
                f"on {row.name.date()}"
            )

            entry_price = 0

        # Risk management
        if position != 0:

            # Stop loss
            if row['Close'] <= entry_price * stop_loss:

                balance = position * row['Close']
                position = 0

                logging.info(
                    f"STOP LOSS at {row['Close']} "
                    f"on {row.name.date()}"
                )

            # Take profit
            elif row['Close'] >= entry_price * take_profit:

                balance = position * row['Close']
                position = 0

                logging.info(
                    f"TAKE PROFIT at {row['Close']} "
                    f"on {row.name.date()}"
                )

    # Sell remaining shares
    if position != 0:
        balance = position * data.iloc[-1]['Close']

    return balance


# Create log file
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Run backtest
final_balance = backtest(data)

# Print result
print(f"Final Balance: ${final_balance:.2f}")
