"""
components/charts.py
Plotly figure builders. Pulling these out of app.py keeps the page logic
readable and makes each chart independently testable/reusable.
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_price_chart(price_df: pd.DataFrame) -> go.Figure:
    """Candlestick + SMA/Bollinger overlay on top, RSI below."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
                         vertical_spacing=0.05, subplot_titles=("Price + Indicators", "RSI"))
    fig.add_trace(go.Candlestick(x=price_df.index, open=price_df["Open"], high=price_df["High"],
                                  low=price_df["Low"], close=price_df["Close"], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["SMA_20"], name="SMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["SMA_50"], name="SMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["BB_Upper"], name="BB Upper",
                              line=dict(dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["BB_Lower"], name="BB Lower",
                              line=dict(dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["RSI_14"], name="RSI 14"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.update_layout(height=650, xaxis_rangeslider_visible=False)
    return fig


def build_macd_chart(price_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=price_df.index, y=price_df["Histogram"], name="Histogram"))
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["MACD"], name="MACD"))
    fig.add_trace(go.Scatter(x=price_df.index, y=price_df["Signal"], name="Signal"))
    fig.update_layout(height=300, title="MACD")
    return fig


def build_forecast_eval_chart(comparison: pd.DataFrame) -> go.Figure:
    """Forecast-vs-actual chart for the Forecast Lab's holdout evaluation panel."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=comparison.index, y=comparison["Actual"], name="Actual"))
    fig.add_trace(go.Scatter(x=comparison.index, y=comparison["Predicted"], name="Predicted"))
    fig.add_trace(go.Scatter(x=comparison.index, y=comparison["Upper"], name="Upper CI",
                              line=dict(dash="dot"), opacity=0.5))
    fig.add_trace(go.Scatter(x=comparison.index, y=comparison["Lower"], name="Lower CI",
                              line=dict(dash="dot"), opacity=0.5))
    fig.update_layout(title="Forecast vs Actual (holdout window)")
    return fig


def build_forward_forecast_chart(price_df: pd.DataFrame, forecast_df: pd.DataFrame, steps: int, order) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price_df.index[-120:], y=price_df["Close"].iloc[-120:], name="History"))
    fig.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df["Forecast"], name="Forecast"))
    fig.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df["Upper"], name="Upper CI",
                              line=dict(dash="dot"), opacity=0.5))
    fig.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df["Lower"], name="Lower CI",
                              line=dict(dash="dot"), opacity=0.5))
    fig.update_layout(title=f"{steps}-day forward forecast (order={order})")
    return fig


def build_equity_curve_chart(trade_log: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trade_log.index, y=trade_log["Equity_Strategy"], name="Strategy"))
    fig.add_trace(go.Scatter(x=trade_log.index, y=trade_log["Equity_BuyHold"], name="Buy & Hold"))
    fig.update_layout(title="Equity Curve (growth of $1)")
    return fig


def build_efficient_frontier_chart(frontier: pd.DataFrame, optimal_point: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frontier["volatility"], y=frontier["return"], mode="markers",
        marker=dict(color=frontier["sharpe"], colorscale="Viridis", showscale=True),
        name="Efficient frontier"))
    fig.add_trace(go.Scatter(
        x=[optimal_point["volatility"]], y=[optimal_point["expected_return"]], mode="markers",
        marker=dict(color="red", size=14, symbol="star"), name="Optimal portfolio"))
    fig.update_layout(title="Efficient Frontier", xaxis_title="Volatility", yaxis_title="Return")
    return fig


def build_sentiment_chart(news_df: pd.DataFrame) -> go.Figure:
    """Bar chart of per-headline sentiment scores, colored positive/negative."""
    colors = ["#2ecc71" if s > 0 else "#e74c3c" if s < 0 else "#95a5a6" for s in news_df["Score"]]
    fig = go.Figure(go.Bar(
        x=news_df["Score"], y=news_df["Title"].str.slice(0, 60), orientation="h",
        marker_color=colors,
    ))
    fig.update_layout(title="Headline sentiment (last N articles)", height=max(300, 40 * len(news_df)),
                       xaxis_title="Score (-1 negative to +1 positive)", yaxis=dict(autorange="reversed"))
    return fig
