"""
components/sidebar.py
Renders the sidebar (primary ticker, period, watchlist, portfolio ticker list)
and returns the selected settings as a plain dict, so app.py stays declarative.
"""
import streamlit as st

from storage import db


def render_sidebar() -> dict:
    st.sidebar.header("Settings")

    ticker = st.sidebar.text_input("Primary ticker", value="AAPL").upper().strip()
    period = st.sidebar.selectbox("History period", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

    if st.sidebar.button("⭐ Add to watchlist"):
        db.add_to_watchlist(ticker)
    watchlist = db.get_watchlist()
    st.sidebar.write("Watchlist:", ", ".join(watchlist) if watchlist else "empty")
    if watchlist:
        remove_choice = st.sidebar.selectbox("Remove from watchlist", ["--"] + watchlist)
        if remove_choice != "--" and st.sidebar.button("Remove"):
            db.remove_from_watchlist(remove_choice)
            st.rerun()

    portfolio_input = st.sidebar.text_input(
        "Portfolio tickers (comma-separated)", value="AAPL, MSFT, GOOGL, AMZN"
    )
    portfolio_tickers = [t.strip().upper() for t in portfolio_input.split(",") if t.strip()]

    with st.sidebar.expander("AI provider status"):
        from config import LLM_PROVIDER
        st.write(f"Provider: `{LLM_PROVIDER}`")
        st.caption("Set LLM_PROVIDER / API keys in your .env file.")

    return {
        "ticker": ticker,
        "period": period,
        "portfolio_tickers": portfolio_tickers,
        "watchlist": watchlist,
    }
