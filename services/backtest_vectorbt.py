"""
backtest_vectorbt.py
Optional, more advanced backtest engine built on the `vectorbt` library
(vectorized, numba-accelerated). This is an ORIGINAL implementation -- it
was not copied from any reference repo (the VectorBT-Streamlit project it
was inspired by ships with no LICENSE file, so its code isn't reused here;
only the general idea of "use vectorbt for fast multi-parameter backtests"
carries over).

Caveat: the open-source `vectorbt` package only supports Python 3.6-3.10.
If you're on a newer interpreter, either run this module in a separate
3.10 virtualenv, or stick with services/backtest.py (pure pandas/numpy,
works on any Python version) which app.py uses by default.

Usage (from a 3.10 environment with `pip install vectorbt`):
    from services.backtest_vectorbt import run_vectorbt_backtest
    pf, stats = run_vectorbt_backtest(close, fast=10, slow=30)
"""
from __future__ import annotations

import pandas as pd


def is_available() -> bool:
    try:
        import vectorbt  # noqa: F401
        return True
    except ImportError:
        return False


def run_vectorbt_backtest(
    close: pd.Series,
    fast: int = 10,
    slow: int = 30,
    init_cash: float = 100_000.0,
    fees: float = 0.001,
):
    """
    Fast/slow EMA-crossover backtest using vectorbt's vectorized Portfolio engine.
    Returns (portfolio, stats_dict). Raises ImportError with a clear message
    if vectorbt isn't installed (e.g. on Python 3.11+).
    """
    try:
        import vectorbt as vbt
    except ImportError as e:
        raise ImportError(
            "vectorbt is not installed or unsupported on this Python version "
            "(vectorbt requires Python 3.6-3.10). Install it in a 3.10 env with "
            "`pip install vectorbt`, or use services/backtest.py instead."
        ) from e

    fast_ema = vbt.MA.run(close, fast, ewm=True)
    slow_ema = vbt.MA.run(close, slow, ewm=True)
    entries = fast_ema.ma_crossed_above(slow_ema)
    exits = fast_ema.ma_crossed_below(slow_ema)

    portfolio = vbt.Portfolio.from_signals(
        close, entries, exits, init_cash=init_cash, fees=fees, freq="1D"
    )

    stats = portfolio.stats()
    summary = {
        "total_return_%": round(float(stats.get("Total Return [%]", 0.0)), 2),
        "sharpe": round(float(stats.get("Sharpe Ratio", 0.0)), 2),
        "max_drawdown_%": round(float(stats.get("Max Drawdown [%]", 0.0)), 2),
        "win_rate_%": round(float(stats.get("Win Rate [%]", 0.0)), 2),
        "num_trades": int(stats.get("Total Trades", 0)),
    }
    return portfolio, summary
