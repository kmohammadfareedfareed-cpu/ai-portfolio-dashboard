"""
forecasting.py
ARIMA-based forecasting with an AIC-based small grid search for order selection,
forward forecasting with confidence intervals, and holdout evaluation (MAE/RMSE/MAPE).
"""
import warnings
from itertools import product

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")


def _best_order(train: pd.Series, p_range=range(0, 4), d_range=range(0, 2), q_range=range(0, 4)):
    """Small grid search over (p, d, q) picking the combination with lowest AIC."""
    best_aic = np.inf
    best_order = (1, 1, 1)
    for p, d, q in product(p_range, d_range, q_range):
        try:
            model = ARIMA(train, order=(p, d, q)).fit()
            if model.aic < best_aic:
                best_aic = model.aic
                best_order = (p, d, q)
        except Exception:
            continue
    return best_order


def train_test_split_series(series: pd.Series, holdout: int = 30):
    if len(series) <= holdout:
        raise ValueError("Series is too short for the requested holdout size.")
    return series.iloc[:-holdout], series.iloc[-holdout:]


def fit_and_forecast(series: pd.Series, steps: int = 30, order=None):
    """Fit ARIMA on the full series and forecast `steps` ahead with 95% confidence intervals."""
    close = series.dropna()
    order = order or _best_order(close)
    model = ARIMA(close, order=order).fit()
    fc = model.get_forecast(steps=steps)
    mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)
    ci.columns = ["Lower", "Upper"]

    # statsmodels can't always infer a date frequency from irregular trading-day
    # data (weekends/holidays break auto-detection), and silently falls back to
    # an integer index in that case -- which Plotly then renders as 1970-01-01
    # epoch dates on a shared datetime axis. Build the future index explicitly.
    future_index = pd.bdate_range(start=close.index[-1] + pd.Timedelta(days=1), periods=steps)
    mean.index = future_index
    ci.index = future_index

    result = pd.DataFrame({"Forecast": mean}).join(ci)
    return result, order, model


def evaluate_forecast(actual: pd.Series, predicted: pd.Series) -> dict:
    actual, predicted = actual.align(predicted, join="inner")
    error = actual - predicted
    mae = error.abs().mean()
    rmse = np.sqrt((error ** 2).mean())
    mape = (error.abs() / actual.replace(0, np.nan)).mean() * 100
    return {"MAE": round(float(mae), 4), "RMSE": round(float(rmse), 4), "MAPE_%": round(float(mape), 2)}


def backtest_forecast(series: pd.Series, holdout: int = 30, order=None):
    """
    Fit ARIMA on the training portion only, forecast across the holdout window,
    and score the forecast against what actually happened. This is the
    forecast-vs-actual evaluation panel.
    """
    train, test = train_test_split_series(series.dropna(), holdout)
    order = order or _best_order(train)
    model = ARIMA(train, order=order).fit()
    fc = model.get_forecast(steps=len(test))

    predicted = fc.predicted_mean
    predicted.index = test.index
    ci = fc.conf_int(alpha=0.05)
    ci.index = test.index
    ci.columns = ["Lower", "Upper"]

    metrics = evaluate_forecast(test, predicted)
    comparison = pd.DataFrame({"Actual": test, "Predicted": predicted}).join(ci)
    return comparison, metrics, order