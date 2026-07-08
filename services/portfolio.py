"""
portfolio.py
Return/risk metrics (Sharpe, volatility, drawdown) and a Markowitz-style
mean-variance portfolio optimizer with an efficient frontier sampler.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config import RISK_FREE_RATE, TRADING_DAYS


def daily_returns(price_matrix: pd.DataFrame) -> pd.DataFrame:
    return price_matrix.pct_change().dropna()


def annualize_return(returns: pd.Series) -> float:
    return returns.mean() * TRADING_DAYS


def annualize_volatility(returns: pd.Series) -> float:
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: pd.Series, risk_free: float = RISK_FREE_RATE) -> float:
    vol = annualize_volatility(returns)
    if vol == 0:
        return 0.0
    return (annualize_return(returns) - risk_free) / vol


def max_drawdown(price_series: pd.Series) -> float:
    cumulative = price_series / price_series.iloc[0]
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    return float(drawdown.min())


def portfolio_stats(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame):
    port_return = float(np.dot(weights, mean_returns) * TRADING_DAYS)
    port_vol = float(np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(TRADING_DAYS))
    sharpe = (port_return - RISK_FREE_RATE) / port_vol if port_vol > 0 else 0.0
    return port_return, port_vol, sharpe


def optimize_portfolio(price_matrix: pd.DataFrame, objective: str = "max_sharpe") -> dict:
    """
    objective: "max_sharpe" or "min_volatility"
    Returns the optimal weight vector and resulting expected return / volatility / Sharpe.
    """
    returns = daily_returns(price_matrix)
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    n = len(price_matrix.columns)
    bounds = tuple((0.0, 1.0) for _ in range(n))
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)
    init_guess = np.repeat(1 / n, n)

    def neg_sharpe(w):
        return -portfolio_stats(w, mean_returns, cov_matrix)[2]

    def volatility(w):
        return portfolio_stats(w, mean_returns, cov_matrix)[1]

    fun = neg_sharpe if objective == "max_sharpe" else volatility
    result = minimize(fun, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)
    weights = result.x
    ret, vol, sharpe = portfolio_stats(weights, mean_returns, cov_matrix)
    return {
        "weights": dict(zip(price_matrix.columns, np.round(weights, 4).tolist())),
        "expected_return": round(ret, 4),
        "volatility": round(vol, 4),
        "sharpe": round(sharpe, 4),
    }


def efficient_frontier(price_matrix: pd.DataFrame, n_portfolios: int = 40) -> pd.DataFrame:
    """Sample target returns and solve min-volatility weights for each -- used to plot the frontier."""
    returns = daily_returns(price_matrix)
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    n = len(price_matrix.columns)
    bounds = tuple((0.0, 1.0) for _ in range(n))

    target_returns = np.linspace(mean_returns.min() * TRADING_DAYS, mean_returns.max() * TRADING_DAYS, n_portfolios)
    frontier = []
    for target in target_returns:
        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, target=target: np.dot(w, mean_returns) * TRADING_DAYS - target},
        )
        result = minimize(
            lambda w: portfolio_stats(w, mean_returns, cov_matrix)[1],
            np.repeat(1 / n, n), method="SLSQP", bounds=bounds, constraints=constraints,
        )
        if result.success:
            _, vol, sharpe = portfolio_stats(result.x, mean_returns, cov_matrix)
            frontier.append({"return": target, "volatility": vol, "sharpe": sharpe})
    return pd.DataFrame(frontier)


def portfolio_summary(price_matrix: pd.DataFrame, weights: dict) -> dict:
    """Summary stats (return, volatility, Sharpe, drawdown, growth curve) for a fixed set of weights."""
    w = np.array([weights[t] for t in price_matrix.columns])
    w = w / w.sum()
    returns = daily_returns(price_matrix)
    port_daily = returns @ w
    port_value = (1 + port_daily).cumprod()
    return {
        "annual_return": round(annualize_return(port_daily), 4),
        "annual_volatility": round(annualize_volatility(port_daily), 4),
        "sharpe": round(sharpe_ratio(port_daily), 4),
        "max_drawdown": round(max_drawdown(port_value), 4),
        "cumulative_growth": port_value,
    }
