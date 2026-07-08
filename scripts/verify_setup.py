"""
scripts/verify_setup.py
End-to-end sanity check for the whole project. Run this after any setup change
or dependency upgrade to catch config/data/logic issues in one shot, without
clicking through every tab in the Streamlit UI.

It doesn't just check "did this crash" -- where possible it cross-checks the
app's output against an independent manual calculation (e.g. SMA_20 vs a plain
mean(), buy-and-hold return vs a plain price ratio), so a wrong-but-not-crashing
result gets caught too.

Usage:
    python scripts/verify_setup.py            # uses AAPL
    python scripts/verify_setup.py MSFT        # any ticker
    python scripts/verify_setup.py AAPL --verbose   # print full tracebacks on failure
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TICKER = "AAPL"
for arg in sys.argv[1:]:
    if not arg.startswith("--"):
        TICKER = arg.upper()
PORTFOLIO = ["AAPL", "MSFT", "GOOGL"]
VERBOSE = "--verbose" in sys.argv

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((PASS, name, detail))
    except Exception as e:
        results.append((FAIL, name, f"{type(e).__name__}: {e}"))
        if VERBOSE:
            traceback.print_exc()


def main():
    print(f"Verifying project against ticker: {TICKER}\n")
    price_df = {}  # mutable holder so nested checks can share fetched data

    # ---- 0. Config / .env ----
    def check_config():
        import config
        provider = config.LLM_PROVIDER
        key_map = {
            "anthropic": config.ANTHROPIC_API_KEY,
            "openai": config.OPENAI_API_KEY,
            "openrouter": config.OPENROUTER_API_KEY,
            "google": config.GOOGLE_API_KEY,
        }
        key_present = bool(key_map.get(provider, ""))
        if not key_present:
            raise AssertionError(
                f"LLM_PROVIDER is '{provider}' but its matching API key is empty. "
                f"Check: (1) your file is named exactly '.env' (not '.env.txt'), "
                f"(2) it sits next to app.py, (3) you fully restarted "
                f"`streamlit run app.py` after editing it."
            )
        return f"LLM_PROVIDER={provider}, key present={key_present}, DB_PATH={config.DB_PATH}"
    check("config / .env loading", check_config)

    # ---- 1. Market data ----
    def check_market_data():
        from services import market_data
        df = market_data.get_price_data(TICKER, period="1y")
        assert not df.empty, "no rows returned"
        assert {"Open", "High", "Low", "Close", "Volume"}.issubset(df.columns)
        price_df["df"] = df
        return f"{len(df)} rows, last close={df['Close'].iloc[-1]:.2f}, last date={df.index[-1].date()}"
    check("services.market_data.get_price_data", check_market_data)

    # ---- 2. Indicators (cross-checked against a plain manual mean) ----
    def check_indicators():
        from services import indicators
        df = price_df["df"]
        ind = indicators.add_all_indicators(df)
        rsi = ind["RSI_14"].dropna()
        assert rsi.between(0, 100).all(), "RSI left [0, 100] bounds"
        manual_sma20 = df["Close"].iloc[-20:].mean()
        app_sma20 = ind["SMA_20"].iloc[-1]
        assert abs(manual_sma20 - app_sma20) < 1e-6, \
            f"SMA_20 mismatch: manual={manual_sma20:.4f} vs app={app_sma20:.4f}"
        price_df["ind"] = ind
        return f"RSI in bounds; SMA_20 matches manual mean(last 20 closes) = {app_sma20:.2f}"
    check("services.indicators.add_all_indicators", check_indicators)

    # ---- 3. Forecast forward (dates must be in the future, not epoch 1970) ----
    def check_forecast_forward():
        from services import forecasting
        df = price_df["df"]
        forecast_df, order, _ = forecasting.fit_and_forecast(df["Close"], steps=10)
        assert len(forecast_df) == 10
        assert forecast_df.index.min() > df.index[-1], "forecast dates aren't after history"
        assert forecast_df.index.min().year >= 2020, "forecast dates look like epoch/1970 -- date-index bug"
        return f"order={order}, forecast range {forecast_df.index[0].date()} -> {forecast_df.index[-1].date()}"
    check("services.forecasting.fit_and_forecast", check_forecast_forward)

    # ---- 4. Forecast holdout evaluation (with a naive baseline for context) ----
    def check_forecast_backtest():
        from services import forecasting
        df = price_df["df"]
        comparison, metrics, order = forecasting.backtest_forecast(df["Close"], holdout=20)
        naive_pred = comparison["Actual"].shift(1).bfill()
        naive_mae = (comparison["Actual"] - naive_pred).abs().mean()
        return (f"order={order}, MAE={metrics['MAE']}, RMSE={metrics['RMSE']}, "
                f"MAPE={metrics['MAPE_%']}%  (naive 'no change' baseline MAE={naive_mae:.4f} for comparison)")
    check("services.forecasting.backtest_forecast", check_forecast_backtest)

    # ---- 5. Portfolio optimizer (weights must sum to 1, no shorting) ----
    def check_portfolio():
        from services import market_data, portfolio
        matrix = market_data.get_close_matrix(PORTFOLIO, period="1y")
        result = portfolio.optimize_portfolio(matrix, objective="max_sharpe")
        total_w = sum(result["weights"].values())
        assert abs(total_w - 1.0) < 1e-3, f"weights sum to {total_w}, not 1"
        assert all(w >= -1e-6 for w in result["weights"].values()), "negative weight found"
        return f"weights={result['weights']}, sharpe={result['sharpe']}"
    check("services.portfolio.optimize_portfolio", check_portfolio)

    # ---- 6. Backtest (buy-and-hold cross-checked against a plain price ratio) ----
    def check_backtest():
        from services import backtest
        df = price_df["df"]
        _, summary = backtest.run_backtest(df["Close"], fast=20, slow=50)
        manual_bh_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
        app_bh_return = summary["buy_and_hold"]["total_return_%"]
        assert abs(manual_bh_return - app_bh_return) < 1.0, \
            f"buy-and-hold mismatch: manual={manual_bh_return:.2f}% vs app={app_bh_return}%"
        return f"strategy={summary['strategy']}; buy&hold {app_bh_return}% matches manual {manual_bh_return:.2f}%"
    check("services.backtest.run_backtest", check_backtest)

    # ---- 7. Alerts ----
    def check_alerts():
        from services import alerts
        messages = alerts.summarize_alerts(price_df["df"]["Close"])
        assert isinstance(messages, list) and len(messages) >= 1
        return messages[0]
    check("services.alerts.summarize_alerts", check_alerts)

    # ---- 8. Sentiment ----
    def check_sentiment():
        from services import sentiment
        summary = sentiment.summarize_sentiment(TICKER)
        return f"{summary['headline_count']} headlines, avg score={summary['average_score']}, label={summary['label']}"
    check("services.sentiment.summarize_sentiment", check_sentiment)

    # ---- 9. LLM agent -- a REAL live call using whatever provider is in your .env ----
    def check_llm():
        from services import llm_agent
        df = price_df["df"]
        answer = llm_agent.ask_llm(
            "In one short sentence, comment on the latest closing price.",
            TICKER, {"latest_close": float(df["Close"].iloc[-1])},
        )
        if answer.startswith(("Missing", "LLM request failed", "No LLM provider")):
            raise AssertionError(answer)
        return answer[:120] + ("..." if len(answer) > 120 else "")
    check("services.llm_agent.ask_llm (live API call)", check_llm)

    # ---- 10. Storage / SQLite ----
    def check_db():
        from storage import db
        db.init_db()
        db.add_to_watchlist(TICKER)
        wl = db.get_watchlist()
        assert TICKER in wl, "ticker not found after writing to watchlist"
        return f"watchlist write/read OK: {wl}"
    check("storage.db", check_db)

    # ---- Report ----
    print(f"{'STATUS':<6} {'CHECK':<42} DETAIL")
    print("-" * 110)
    n_fail = 0
    for status, name, detail in results:
        if status == FAIL:
            n_fail += 1
        print(f"{status:<6} {name:<42} {detail}")
    print("-" * 110)
    if n_fail:
        print(f"\n{n_fail} check(s) FAILED. Re-run with --verbose for full tracebacks. "
              f"Fix these before trusting the app's output.")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()