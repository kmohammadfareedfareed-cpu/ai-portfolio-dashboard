"""
market_data.py
Fetches and caches OHLCV price data and company info from Yahoo Finance via yfinance.
"""
import pandas as pd
import yfinance as yf
import streamlit as st


@st.cache_data(ttl=900, show_spinner=False)
def get_price_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLCV data for a single ticker."""
    df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'. Check the symbol and try again.")
    df = df.rename(columns=str.title)
    df.index.name = "Date"
    return df.dropna(subset=["Close"])


@st.cache_data(ttl=900, show_spinner=False)
def get_multiple_price_data(tickers: list[str], period: str = "1y", interval: str = "1d") -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data for multiple tickers, skipping any that fail."""
    data = {}
    for t in tickers:
        try:
            data[t] = get_price_data(t, period, interval)
        except ValueError:
            continue
    return data


def get_close_matrix(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    """Build an aligned matrix of close prices for multiple tickers (used for portfolio math)."""
    data = get_multiple_price_data(tickers, period)
    closes = {t: df["Close"] for t, df in data.items()}
    matrix = pd.DataFrame(closes).dropna(how="all")
    return matrix.ffill().dropna()


@st.cache_data(ttl=3600, show_spinner=False)
def get_company_info(ticker: str) -> dict:
    """Fetch basic company metadata. Falls back to defaults if unavailable."""
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        info = {}
    return {
        "name": info.get("longName", ticker),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "marketCap": info.get("marketCap", None),
        "currency": info.get("currency", "USD"),
    }
