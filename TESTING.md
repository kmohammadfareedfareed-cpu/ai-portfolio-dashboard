# Testing & Validation Guide

Three layers, from fastest to most thorough. Run them in this order.

## 1. Unit tests (logic correctness, offline, ~1 second)

```bash
pytest tests/ -v
```

Checks the pure-math services (indicators, portfolio, backtest, alerts) against
known invariants using synthetic data — RSI stays in [0,100], optimizer weights
sum to 1, etc. No network calls, so it also tells you if a dependency upgrade
(like the pandas 3.0 issue you hit) broke something structurally.

## 2. Live end-to-end check (real data, real API calls, ~30-60 seconds)

```bash
python scripts/verify_setup.py            # defaults to AAPL
python scripts/verify_setup.py MSFT --verbose
```

This is the one that answers "is every feature actually giving accurate
results" — it runs every service against real yfinance data and, where
possible, **cross-checks the app's output against an independent manual
calculation**, not just "did it crash":

| Check | What it verifies |
|---|---|
| config / .env | The provider your `.env` says to use actually has its API key loaded |
| market_data | Real OHLCV data comes back non-empty |
| indicators | RSI stays in bounds; **SMA_20 is compared against a plain `mean()` of the last 20 closes** |
| forecasting (forward) | Forecast dates are genuinely in the future (catches the 1970-epoch bug class) |
| forecasting (backtest) | Reports MAE/RMSE/MAPE alongside a naive "no change" baseline for context |
| portfolio | Optimizer weights sum to 1, no negative (short) weights |
| backtest | **Buy-and-hold return is cross-checked against a plain `last/first - 1` price ratio** |
| alerts | Always returns at least one message (even if it's "nothing detected") |
| sentiment | Headline count + aggregate score |
| llm_agent | An actual live call to your configured provider — this is the fastest way to confirm your `.env` / API key setup works, without opening the UI |
| storage | SQLite write + read round-trip |

Exit code is non-zero if anything fails, so you can wire it into a pre-commit
hook or CI if you want.

## 3. Manual UI walkthrough (judgment calls, ~10 minutes)

Some things can only be sanity-checked by a human looking at real numbers.
Do this once after any significant change:

- **Dashboard** — Pull up the same ticker on [TradingView](https://www.tradingview.com)
  or Yahoo Finance and eyeball whether your SMA/RSI/MACD lines roughly match
  theirs for the same date range. Small differences are normal (different
  data providers, adjusted vs unadjusted close); large ones are a bug.
- **Portfolio Builder** — Try 2 highly correlated tickers (e.g. `AAPL, MSFT`)
  vs. 2 uncorrelated ones. The efficient frontier should visibly bow outward
  more for the uncorrelated pair — that's diversification working. If the
  frontier is a straight line, something's wrong with the covariance calc.
- **Forecast Lab** — Compare the "Run backtested evaluation" MAPE against the
  naive baseline `verify_setup.py` prints. If ARIMA's MAPE isn't meaningfully
  better than the naive baseline, that's not a bug — short-horizon stock
  prices are close to a random walk, so this is expected more often than not.
  Treat the forecast as illustrative, not predictive.
- **Backtesting Lab** — Set fast/slow SMA windows to something extreme (e.g.
  fast=2, slow=5) and confirm the number of trades goes up a lot and net
  return drops (transaction costs eating into over-trading) — that's the
  cost model actually doing something, not just decoration.
- **AI Query** — Ask a question, then manually compare the numbers the AI
  cites in its answer against the metrics shown elsewhere on that same tab
  (SMA/RSI/latest close). It's instructed to only use the metrics it's
  given, so a mismatch means either a prompt/context bug or the model
  ignoring grounding — worth flagging either way.
- **Sentiment** — Read 3-4 of the actual headlines and check the 🟢/🔴 tag
  makes intuitive sense. The scorer is a small built-in word list (see
  `services/sentiment.py`), not a trained model — it'll miss sarcasm, negation
  ("not bad"), and domain-specific phrasing. Treat it as a rough signal.
- **Alerts** — Pick a ticker you know had a real news-driven price shock
  recently and confirm it shows up in the flagged list.

## Known limitations (not bugs)

- **Forecasting** is a statistical extrapolation (ARIMA), not a prediction
  service — it will not reliably beat a naive baseline over short horizons.
  This is a property of markets, not something to "fix" in the code.
- **Sentiment** is a lightweight lexicon, not an ML model. Good for a quick
  directional read, not for anything you'd trade on.
- **Backtest** uses a fixed bps cost model and no slippage/liquidity
  modeling — real execution will differ, especially on illiquid tickers.
- **AI Query** answers are only as good as the metrics context it's given;
  it doesn't have any information beyond what's shown in `ai_context` in
  `app.py`.

If you want stronger guarantees than "cross-checked against a manual
calculation," the next step up would be recorded reference outputs (golden
files) for a fixed ticker/date range with `pytest -k regression`-style
snapshot tests — say the word if you want that added.