"""
backtest.py
A simple, transparent rule-based backtesting engine: fast/slow SMA crossover
vs. buy-and-hold, with transaction costs, an equity curve, and a metrics summary
(CAGR, volatility, Sharpe, max drawdown, win rate).
"""
import numpy as np
import pandas as pd

from config import TRADING_DAYS, RISK_FREE_RATE


def sma_crossover_signals(close: pd.Series, fast: int = 20, slow: int = 50) -> pd.Series:
    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    signal = (fast_ma > slow_ma).astype(int)  # 1 = long, 0 = flat
    return signal.fillna(0)


def run_backtest(close: pd.Series, fast: int = 20, slow: int = 50, cost_bps: float = 5.0):
    """
    Backtest a fast/slow SMA crossover strategy against buy-and-hold.
    cost_bps: one-way transaction cost in basis points, applied whenever the position changes.
    Returns (trade_log DataFrame, summary dict).
    """
    signal = sma_crossover_signals(close, fast, slow).shift(1).fillna(0)  # trade on next bar, avoid lookahead
    daily_ret = close.pct_change().fillna(0)

    strategy_ret = signal * daily_ret
    position_changes = signal.diff().abs().fillna(0)
    cost = position_changes * (cost_bps / 10000)
    strategy_ret_net = strategy_ret - cost

    equity_strategy = (1 + strategy_ret_net).cumprod()
    equity_buyhold = (1 + daily_ret).cumprod()

    trade_log = pd.DataFrame({
        "Signal": signal,
        "Return": strategy_ret_net,
        "Equity_Strategy": equity_strategy,
        "Equity_BuyHold": equity_buyhold,
    })

    summary = {
        "strategy": _summarize(strategy_ret_net, equity_strategy),
        "buy_and_hold": _summarize(daily_ret, equity_buyhold),
        "num_trades": int(position_changes.sum() / 2),
    }
    return trade_log, summary


def _summarize(returns: pd.Series, equity: pd.Series) -> dict:
    total_return = equity.iloc[-1] - 1
    n_years = max(len(returns) / TRADING_DAYS, 1e-6)
    cagr = equity.iloc[-1] ** (1 / n_years) - 1 if equity.iloc[-1] > 0 else -1.0
    vol = returns.std() * np.sqrt(TRADING_DAYS)
    sharpe = (returns.mean() * TRADING_DAYS - RISK_FREE_RATE) / vol if vol > 0 else 0.0
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    nonzero = (returns != 0).sum()
    win_rate = (returns > 0).sum() / nonzero if nonzero > 0 else 0.0
    return {
        "total_return_%": round(total_return * 100, 2),
        "cagr_%": round(cagr * 100, 2),
        "volatility_%": round(vol * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_%": round(drawdown.min() * 100, 2),
        "win_rate_%": round(win_rate * 100, 2),
    }
