# Attributions

This project was built to match the feature set of several reference repos
you pointed me at. Here's exactly what was checked, what license each repo
carries, and what that meant for how it was used here.

| Repo | License found | How it was used |
|---|---|---|
| [DataRohit/Stockastic](https://github.com/DataRohit/Stockastic) | MIT | Confirmed as validation for the architecture already in `services/forecasting.py` (yfinance + statsmodels ARIMA + Plotly + Streamlit). No code copied verbatim; the ARIMA/AIC-search/holdout-evaluation logic here is an original implementation. |
| [marketcalls/VectorBT-Streamlit](https://github.com/marketcalls/VectorBT-Streamlit) | **None found** (no LICENSE file → all rights reserved by default) | Code was **not copied or adapted**. `services/backtest_vectorbt.py` is an original implementation that uses the same open-source `vectorbt` library, written independently, to provide an optional advanced backtest engine. |
| [ethan-tsai-tsai/AI-Stock-Analysis-Dashboard](https://github.com/ethan-tsai-tsai/AI-Stock-Analysis-Dashboard) | MIT | `main.py` was reviewed directly. Its pattern of a structured `{action, justification}` LLM response and an OpenRouter-based free-tier LLM call informed `services/llm_agent.py`'s `get_ticker_recommendation()` and the OpenRouter provider option. Code was rewritten, not copied. |
| pranay-surya/market-ml, PhongCT1105/S-P_500_Stock_Prediction, 0xZee/financial-dashboard-streamlit, YassineOUAHMANE/Stock-Sentiment-Analysis-Dashboard, m-turnergane/stock-sentiment-dashboard, I3eka/Stock-Sentiment-Portfolio-Analyzer, Juheb-19/ai-stock-analysis-dashboard-public | Not individually checked | Only descriptions/feature lists were used to shape the requirements list (dashboard layout, portfolio holdings, sentiment layer). No code was reviewed or reused from these. If you want any of them specifically pulled in, paste the repo's LICENSE + the relevant file's raw content and I'll adapt it the same way as the three above. |

## Why this approach

- **MIT-licensed repos**: safe to read and adapt, but even then the code
  here is a fresh implementation rather than a copy-paste, so it fits this
  project's structure and stays exact-match debuggable.
- **Unlicensed repos** (no LICENSE file): under default copyright, nobody
  but the author has redistribution/modification rights, even though the
  code is publicly viewable on GitHub. The safe move is to reimplement the
  *idea* independently, which is what `backtest_vectorbt.py` does.
- **Repos not checked**: rather than guess at their license or lift code
  I hadn't verified, their features were treated as a spec to build toward,
  not a source to copy from.

## If you want more repos actually pulled in

The most reliable way to hand me real code (see the earlier answer in this
chat) is:
1. A direct link to the specific file (not just the repo root), or
2. Pasting the raw file content directly into the chat, or
3. Uploading the repo as a zip.

I'll check the LICENSE file first, then either adapt it (permissive license)
or reimplement the same idea from scratch (no/copyleft license) — same
process as above.
