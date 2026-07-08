"""
alerts.py
Anomaly detection: z-score based price shocks and short-vs-long-term
volatility spikes, plus a human-readable summary used by both the
Alerts tab and the AI Query panel's grounding context.
"""
import numpy as np
import pandas as pd


def detect_price_shocks(close: pd.Series, z_thresh: float = 2.5) -> pd.DataFrame:
    """Flag daily returns whose rolling z-score exceeds the threshold (up or down shocks)."""
    returns = close.pct_change()
    rolling_mean = returns.rolling(60, min_periods=20).mean()
    rolling_std = returns.rolling(60, min_periods=20).std()
    z = (returns - rolling_mean) / rolling_std
    flagged = pd.DataFrame({"Return": returns, "ZScore": z})
    flagged["Alert"] = np.where(z.abs() >= z_thresh, np.where(z > 0, "Spike Up", "Spike Down"), "")
    return flagged[flagged["Alert"] != ""]


def detect_volatility_spikes(close: pd.Series, short: int = 5, long: int = 30, ratio_thresh: float = 1.8) -> pd.DataFrame:
    """Flag periods where short-term rolling volatility is unusually high vs. the longer-term average."""
    returns = close.pct_change()
    short_vol = returns.rolling(short).std()
    long_vol = returns.rolling(long).std()
    ratio = short_vol / long_vol.replace(0, np.nan)
    flagged = pd.DataFrame({"ShortVol": short_vol, "LongVol": long_vol, "Ratio": ratio})
    return flagged[flagged["Ratio"] >= ratio_thresh]


def summarize_alerts(close: pd.Series) -> list[str]:
    messages = []
    shocks = detect_price_shocks(close)
    if not shocks.empty:
        last = shocks.iloc[-1]
        messages.append(f"Last flagged move: {last['Alert']} of {last['Return']*100:.2f}% (z={last['ZScore']:.2f}).")
    vol_spikes = detect_volatility_spikes(close)
    if not vol_spikes.empty:
        messages.append(f"Volatility spike detected: short-term volatility is {vol_spikes.iloc[-1]['Ratio']:.2f}x the longer-term average.")
    if not messages:
        messages.append("No significant price or volatility anomalies detected recently.")
    return messages
