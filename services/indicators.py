"""
indicators.py
Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands.
"""
import pandas as pd
import numpy as np


def sma(series: pd.Series, window: int = 20) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int = 20) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + rs))
    return result.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({"MACD": macd_line, "Signal": signal_line, "Histogram": histogram})


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"Mid": mid, "Upper": upper, "Lower": lower})


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with SMA/EMA/RSI/MACD/Bollinger columns attached to the Close price."""
    out = df.copy()
    close = out["Close"]
    out["SMA_20"] = sma(close, 20)
    out["SMA_50"] = sma(close, 50)
    out["EMA_20"] = ema(close, 20)
    out["RSI_14"] = rsi(close, 14)
    out = out.join(macd(close))
    out = out.join(bollinger_bands(close).add_prefix("BB_"))
    return out
