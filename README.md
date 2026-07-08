# AI-Powered Portfolio Intelligence Dashboard

A Streamlit dashboard combining live market data, technical indicators, ARIMA
forecasting with holdout evaluation, portfolio optimization, rule-based
backtesting (plus an optional vectorbt engine), news sentiment, anomaly
alerts, and an LLM query panel grounded in the metrics the app computes.

## Project structure

```
ai_portfolio_dashboard/
├── app.py                     # Streamlit entry point — 7 tabs, thin, delegates to components/services
├── config.py                   # env-based settings (API keys, risk-free rate, paths)
├── requirements.txt
├── .env.example                 # copy to .env and fill in your keys
├── .gitignore
├── LICENSE                      # MIT (this project)
├── ATTRIBUTIONS.md              # what was adapted from reference repos, and their licenses
├── data/                        # scratch space (kept for compatibility; not used by default)
├── services/
│   ├── market_data.py           # yfinance fetch + caching, company info
│   ├── indicators.py            # SMA, EMA, RSI, MACD, Bollinger Bands
│   ├── forecasting.py           # ARIMA fit/forecast + holdout MAE/RMSE/MAPE evaluation
│   ├── portfolio.py             # returns, volatility, Sharpe, drawdown, mean-variance optimizer
│   ├── backtest.py              # SMA-crossover vs buy-and-hold (pure pandas, any Python version)
│   ├── backtest_vectorbt.py     # optional advanced engine using `vectorbt` (Python ≤3.10 only)
│   ├── alerts.py                # z-score price shocks + volatility spike detection
│   ├── sentiment.py             # yfinance news + lightweight lexicon sentiment scoring
│   └── llm_agent.py             # grounded Q&A + structured recommendations (Anthropic/OpenAI/OpenRouter)
├── components/
│   ├── sidebar.py                # ticker/period/watchlist controls
│   ├── charts.py                 # all Plotly figure builders
│   ├── metrics.py                 # st.metric row rendering helpers
│   └── tables.py                  # dataframe / headline / chat-history rendering
├── storage/
│   ├── db.py                      # SQLite: watchlist, forecast run log, chat log
│   ├── watchlists.db              # created automatically at runtime
│   └── cache/                     # reserved for future on-disk caching
└── tests/
    └── test_services.py            # offline unit tests (indicators, portfolio, backtest, alerts)
```

## Setup (VS Code / local)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env: set LLM_PROVIDER to anthropic / openai / openrouter, and add the matching API key

streamlit run app.py
```

Opens at `http://localhost:8501`.

Run the test suite any time with:
```bash
pytest tests/
```

### Troubleshooting: `TypeError: deprecate_kwarg() missing 1 required positional argument`

If `streamlit run app.py` fails on import with this error inside
`statsmodels/tsa/arima/estimators/yule_walker.py`, it's a known incompatibility
between **pandas 3.0** (released Jan 2026) and **statsmodels 0.14.x**, which
relies on a pandas private API that changed. `requirements.txt` already pins
`pandas<3.0` to avoid this on a fresh install; if you're hitting it on an
existing environment, fix it with:
```bash
pip install "pandas<3.0"
```

## Features by tab

- **Dashboard** — candlestick chart with SMA/Bollinger overlays, RSI, and MACD.
- **Portfolio Builder** — mean-variance optimizer (max Sharpe or min volatility),
  efficient frontier plot, equal-weight baseline with a growth-of-$1 chart.
- **Forecast Lab** — ARIMA order selected by AIC grid search; a forecast-vs-actual
  evaluation panel on a holdout window (MAE/RMSE/MAPE), plus a forward forecast
  with confidence intervals.
- **Backtesting Lab** — SMA-crossover strategy vs. buy-and-hold with transaction
  costs, equity curve, and CAGR/Sharpe/drawdown/win-rate. An optional `vectorbt`
  engine is available in the expander if you have it installed.
- **AI Query** — free-form grounded Q&A, plus a one-click structured
  Bullish/Bearish/Neutral read with justification. Supports Anthropic, OpenAI,
  OpenRouter (including free-tier models like `deepseek/deepseek-chat-v3-0324:free`),
  or Google Gemini (via the current `google-genai` SDK). Chat history is saved
  to SQLite per ticker.
- **Sentiment** — recent headlines pulled directly from yfinance (no news API
  key needed), scored with a small built-in lexicon, shown as a bar chart and
  a clickable headline list.
- **Alerts** — flags abnormal single-day price moves (z-score) and short-vs-long-term
  volatility spikes.

## Deploying to Streamlit Cloud

1. Push this folder to a GitHub repo.
2. On [share.streamlit.io](https://share.streamlit.io), point at the repo, entry point `app.py`.
3. In **Settings → Secrets**, add whichever provider you're using, e.g.:
   ```
   LLM_PROVIDER = "openrouter"
   OPENROUTER_API_KEY = "sk-or-..."
   ```
4. Deploy. `storage/watchlists.db` lives on ephemeral storage — fine for demos,
   but it resets on redeploy. Swap `storage/db.py` for a hosted Postgres/Supabase
   connection if you need persistence across redeploys.

## On the reference repos you shared

See [`ATTRIBUTIONS.md`](./ATTRIBUTIONS.md) for exactly which repos were checked,
their license status, and what was adapted vs. written from scratch. Short version:
MIT-licensed repos (Stockastic, AI-Stock-Analysis-Dashboard) informed the design
directly; the unlicensed one (VectorBT-Streamlit) was not copied — its
`vectorbt`-based idea was reimplemented independently instead.

## Extending further
- Swap the lexicon-based sentiment scorer for a real model (VADER, a HuggingFace
  pipeline, or route headlines through `llm_agent.py`).
- Add authentication + a hosted database for multi-user watchlists.
- Add a `holdings.py` service for tracking actual position sizes/cost basis,
  not just target weights.