"""
tests/test_services.py
Unit tests for the pure-computation services (indicators, portfolio, backtest,
alerts). These use synthetic price series so they run offline/deterministically
-- no yfinance or LLM calls involved. Run with: pytest tests/
"""
import numpy as np
import pandas as pd
import pytest

from services import indicators, portfolio, backtest, alerts


@pytest.fixture
def synthetic_close():
    np.random.seed(0)
    dates = pd.date_range("2023-01-01", periods=300, freq="B")
    prices = 100 + np.cumsum(np.random.randn(300))
    return pd.Series(prices, index=dates)


@pytest.fixture
def synthetic_ohlcv(synthetic_close):
    close = synthetic_close
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": 1_000_000,
    })


@pytest.fixture
def synthetic_price_matrix():
    np.random.seed(1)
    dates = pd.date_range("2023-01-01", periods=300, freq="B")
    tickers = ["A", "B", "C"]
    return pd.DataFrame(
        {t: 100 + np.cumsum(np.random.randn(300)) for t in tickers}, index=dates
    )


def test_indicators_add_all_columns(synthetic_ohlcv):
    out = indicators.add_all_indicators(synthetic_ohlcv)
    for col in ["SMA_20", "SMA_50", "EMA_20", "RSI_14", "MACD", "Signal", "Histogram",
                "BB_Mid", "BB_Upper", "BB_Lower"]:
        assert col in out.columns
    # RSI must stay within [0, 100]
    assert out["RSI_14"].dropna().between(0, 100).all()


def test_portfolio_optimizer_weights_sum_to_one(synthetic_price_matrix):
    result = portfolio.optimize_portfolio(synthetic_price_matrix, objective="max_sharpe")
    total_weight = sum(result["weights"].values())
    assert abs(total_weight - 1.0) < 1e-3
    assert all(w >= -1e-6 for w in result["weights"].values())  # no shorting


def test_portfolio_summary_has_expected_keys(synthetic_price_matrix):
    weights = {t: 1 / 3 for t in synthetic_price_matrix.columns}
    summary = portfolio.portfolio_summary(synthetic_price_matrix, weights)
    for key in ["annual_return", "annual_volatility", "sharpe", "max_drawdown", "cumulative_growth"]:
        assert key in summary
    assert summary["cumulative_growth"].iloc[0] > 0


def test_backtest_runs_and_produces_summary(synthetic_close):
    trade_log, summary = backtest.run_backtest(synthetic_close, fast=10, slow=30)
    assert "strategy" in summary and "buy_and_hold" in summary
    assert set(summary["strategy"].keys()) == {
        "total_return_%", "cagr_%", "volatility_%", "sharpe", "max_drawdown_%", "win_rate_%"
    }
    assert len(trade_log) == len(synthetic_close)


def test_alerts_summarize_never_empty(synthetic_close):
    messages = alerts.summarize_alerts(synthetic_close)
    assert isinstance(messages, list)
    assert len(messages) >= 1


def test_max_drawdown_is_non_positive(synthetic_close):
    dd = portfolio.max_drawdown(synthetic_close)
    assert dd <= 0
