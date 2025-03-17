import yfinance as yf
import pandas as pd
import talib
import streamlit as st
from datetime import datetime, time as dt_time
import telegram
import time


# Telegram bot setup
TELEGRAM_TOKEN = '8126579938:AAHG-BLo99VDR-qbWKVKHC7fRGY5GfJ3I6U'
TELEGRAM_CHAT_ID = '-1002461680012'
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Market trading hours
MARKET_OPEN_TIME = dt_time(9, 15)  # 9:15 AM IST
MARKET_CLOSE_TIME = dt_time(15, 30)  # 3:30 PM IST

# Streamlit page configuration
st.set_page_config(page_title="RSI, SMA, TSI & MACD Crossover Dashboard", layout="wide")

# Title of the dashboard
st.title("RSI, SMA, TSI & MACD Crossover Dashboard")

# Initialize session state variables if not already done
if 'last_rsi_crossovers' not in st.session_state:
    st.session_state.last_rsi_crossovers = {'1m': None, '5m': None, '15m': None}  # RSI crossovers
if 'last_sma_crossovers' not in st.session_state:
    st.session_state.last_sma_crossovers = {'1m': None, '5m': None, '15m': None}  # SMA crossovers
if 'last_tsi_crossovers' not in st.session_state:
    st.session_state.last_tsi_crossovers = {'1m': None, '5m': None, '15m': None}  # TSI crossovers
if 'last_macd_crossovers' not in st.session_state:
    st.session_state.last_macd_crossovers = {'1m': None, '5m': None, '15m': None}  # MACD crossovers


# Function to fetch NIFTY data for different time intervals
def fetch_nifty_data(interval):
    try:
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d", interval=interval, actions=False, auto_adjust=False)
        data.reset_index(inplace=True)
        data['Datetime'] = data['Datetime'].dt.tz_localize(None)  # Remove timezone
        return data
    except Exception as e:
        st.error(f"Error fetching data for {interval}: {e}")
        return None


# Function to calculate RSI and RSI-MA
def calculate_rsi(data, period=14, ma_period=9):
    data['RSI'] = talib.RSI(data['Close'], timeperiod=period)
    data['RSI_MA'] = data['RSI'].rolling(window=ma_period).mean()
    return data


# Function to calculate SMA
def calculate_sma(data, period=50):
    data['SMA'] = data['Close'].rolling(window=period).mean()
    return data


# Function to calculate TSI (True Strength Index)
def calculate_tsi(data, long_period=25, short_period=13):
    data['Momentum'] = data['Close'].diff()
    data['Abs_Momentum'] = data['Momentum'].abs()
    data['Momentum_Smooth'] = data['Momentum'].ewm(span=short_period, adjust=False).mean()
    data['Abs_Momentum_Smooth'] = data['Abs_Momentum'].ewm(span=short_period, adjust=False).mean()
    data['Momentum_Smooth_Long'] = data['Momentum_Smooth'].ewm(span=long_period, adjust=False).mean()
    data['Abs_Momentum_Smooth_Long'] = data['Abs_Momentum_Smooth'].ewm(span=long_period, adjust=False).mean()
    data['TSI'] = 100 * (data['Momentum_Smooth_Long'] / data['Abs_Momentum_Smooth_Long'])
    return data


# Function to calculate MACD (Moving Average Convergence Divergence)
def calculate_macd(data, fastperiod=12, slowperiod=26, signalperiod=9):
    data['MACD'], data['MACD_Signal'], data['MACD_Hist'] = talib.MACD(data['Close'], fastperiod, slowperiod, signalperiod)
    return data


# Function to check crossovers for each indicator
def check_crossover(data, indicator):
    if indicator == "RSI":
        return check_rsi_crossover(data)
    elif indicator == "SMA":
        return check_sma_crossover(data)
    elif indicator == "TSI":
        return check_tsi_crossover(data)
    elif indicator == "MACD":
        return check_macd_crossover(data)


# RSI crossover check
def check_rsi_crossover(data):
    if len(data) < 2:
        return None
    rsi, rsi_ma = data['RSI'], data['RSI_MA']
    crossover_data = []
    if rsi.iloc[-2] < rsi_ma.iloc[-2] and rsi.iloc[-1] > rsi_ma.iloc[-1]:
        crossover_data.append({
            "crossover_type": "Bullish RSI Crossover",
            "RSI": rsi.iloc[-1],
            "RSI_MA": rsi_ma.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Buy"
        })
    elif rsi.iloc[-2] > rsi_ma.iloc[-2] and rsi.iloc[-1] < rsi_ma.iloc[-1]:
        crossover_data.append({
            "crossover_type": "Bearish RSI Crossover",
            "RSI": rsi.iloc[-1],
            "RSI_MA": rsi_ma.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Sell"
        })
    if crossover_data:
        return crossover_data[-1]
    return None


# SMA crossover check
def check_sma_crossover(data):
    if len(data) < 2:
        return None
    close, sma = data['Close'], data['SMA']
    crossover_data = []
    if close.iloc[-2] < sma.iloc[-2] and close.iloc[-1] > sma.iloc[-1]:
        crossover_data.append({
            "crossover_type": "Bullish SMA Crossover",
            "Close": close.iloc[-1],
            "SMA": sma.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Buy"
        })
    elif close.iloc[-2] > sma.iloc[-2] and close.iloc[-1] < sma.iloc[-1]:
        crossover_data.append({
            "crossover_type": "Bearish SMA Crossover",
            "Close": close.iloc[-1],
            "SMA": sma.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Sell"
        })
    if crossover_data:
        return crossover_data[-1]
    return None


# TSI crossover check
def check_tsi_crossover(data):
    if len(data) < 2:
        return None
    tsi = data['TSI']
    crossover_data = []
    if tsi.iloc[-2] < 0 and tsi.iloc[-1] > 0:
        crossover_data.append({
            "crossover_type": "Bullish TSI Crossover",
            "TSI": tsi.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Buy"
        })
    elif tsi.iloc[-2] > 0 and tsi.iloc[-1] < 0:
        crossover_data.append({
            "crossover_type": "Bearish TSI Crossover",
            "TSI": tsi.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Sell"
        })
    if crossover_data:
        return crossover_data[-1]
    return None


# MACD crossover check
def check_macd_crossover(data):
    if len(data) < 2:
        return None
    macd, macd_signal = data['MACD'], data['MACD_Signal']
    crossover_data = []
    if macd.iloc[-2] < macd_signal.iloc[-2] and macd.iloc[-1] > macd_signal.iloc[-1]:
        crossover_data.append({
            "crossover_type": "Bullish MACD Crossover",
            "MACD": macd.iloc[-1],
            "MACD_Signal": macd_signal.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Buy"
        })
    elif macd.iloc[-2] > macd_signal.iloc[-2] and macd.iloc[-1] < macd_signal.iloc[-1]:
        crossover_data.append({
            "crossover_type": "Bearish MACD Crossover",
            "MACD": macd.iloc[-1],
            "MACD_Signal": macd_signal.iloc[-1],
            "timestamp": data['Datetime'].iloc[-1],
            "signal": "Sell"
        })
    if crossover_data:
        return crossover_data[-1]
    return None


# Function to display crossover data on the Streamlit dashboard
def display_crossover_data(crossover_data, interval, indicator_name):
    if crossover_data:
        st.subheader(f"{interval} - {indicator_name} Crossover")  # Smaller header
        st.write(f"Signal: {crossover_data['signal']} at {crossover_data['timestamp'].strftime('%H:%M:%S')}")
    else:
        last_crossover = st.session_state.get(f'last_{indicator_name.lower()}_crossovers', {}).get(interval)
        if last_crossover:
            st.write(f"Last {indicator_name} Signal: {last_crossover['signal']} at {last_crossover['timestamp'].strftime('%H:%M:%S')}")
        else:
            st.write(f"No {indicator_name} signal yet for {interval} interval.")


# Function to update data for different intervals
def update_data():
    if MARKET_OPEN_TIME <= datetime.now().time() <= MARKET_CLOSE_TIME:
        intervals = ['1m', '5m', '15m']
        all_crossover_data = {}

        for interval in intervals:
            data = fetch_nifty_data(interval)
            if data is not None:
                data = calculate_rsi(data)
                data = calculate_sma(data)
                data = calculate_tsi(data)
                data = calculate_macd(data)

                rsi_crossover_data = check_crossover(data, "RSI")
                sma_crossover_data = check_crossover(data, "SMA")
                tsi_crossover_data = check_crossover(data, "TSI")
                macd_crossover_data = check_crossover(data, "MACD")

                if rsi_crossover_data:
                    new_rsi_crossover = rsi_crossover_data
                    if new_rsi_crossover != st.session_state.last_rsi_crossovers.get(interval):
                        st.session_state.last_rsi_crossovers[interval] = new_rsi_crossover

                if sma_crossover_data:
                    new_sma_crossover = sma_crossover_data
                    if new_sma_crossover != st.session_state.last_sma_crossovers.get(interval):
                        st.session_state.last_sma_crossovers[interval] = new_sma_crossover

                if tsi_crossover_data:
                    new_tsi_crossover = tsi_crossover_data
                    if new_tsi_crossover != st.session_state.last_tsi_crossovers.get(interval):
                        st.session_state.last_tsi_crossovers[interval] = new_tsi_crossover

                if macd_crossover_data:
                    new_macd_crossover = macd_crossover_data
                    if new_macd_crossover != st.session_state.last_macd_crossovers.get(interval):
                        st.session_state.last_macd_crossovers[interval] = new_macd_crossover

                all_crossover_data[interval] = {
                    'RSI': rsi_crossover_data, 'SMA': sma_crossover_data, 'TSI': tsi_crossover_data, 'MACD': macd_crossover_data
                }

        return all_crossover_data
    return None


# Main Streamlit loop (with 1-minute refresh)
while True:
    all_crossover_data = update_data()

    if all_crossover_data:
        # Create four columns
        col1, col2, col3, col4 = st.columns(4)

        # Display RSI crossover data in the first column
        with col1:
            for interval in ['1m', '5m', '15m']:
                rsi_crossover_data = all_crossover_data.get(interval, {}).get('RSI', {})
                display_crossover_data(rsi_crossover_data, interval, "RSI")

        # Display SMA crossover data in the second column
        with col2:
            for interval in ['1m', '5m', '15m']:
                sma_crossover_data = all_crossover_data.get(interval, {}).get('SMA', {})
                display_crossover_data(sma_crossover_data, interval, "SMA")

        # Display TSI crossover data in the third column
        with col3:
            for interval in ['1m', '5m', '15m']:
                tsi_crossover_data = all_crossover_data.get(interval, {}).get('TSI', {})
                display_crossover_data(tsi_crossover_data, interval, "TSI")

        # Display MACD crossover data in the fourth column
        with col4:
            for interval in ['1m', '5m', '15m']:
                macd_crossover_data = all_crossover_data.get(interval, {}).get('MACD', {})
                display_crossover_data(macd_crossover_data, interval, "MACD")

    time.sleep(30)
    st.rerun()
