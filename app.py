"""
app.py
AI-Powered Portfolio Intelligence Dashboard -- main Streamlit entry point.

Professional dark UI: deep navy/charcoal background, glassmorphism cards,
mint-teal + electric-blue accent gradient, Sora/Inter typography with
JetBrains Mono reserved for numbers. Sticky top header + sticky horizontal
nav bar (stays pinned while you scroll), card/grid layout, prominent KPI
cards, and a chat-style AI Assistant panel.

Run with: streamlit run app.py

Optional (nicer sidebar nav icons):
    pip install streamlit-option-menu
The app falls back to a plain radio-based nav automatically if that
package isn't installed, so nothing breaks without it.
"""
import streamlit as st

from config import DEFAULT_INTERVAL
from services import market_data, indicators, forecasting, portfolio, backtest, alerts, llm_agent, sentiment
from storage import db
from components import sidebar, charts, metrics, tables

try:
    from streamlit_option_menu import option_menu  # type: ignore  # optional dep, see requirements note above
    HAS_OPTION_MENU = True
except ImportError:
    HAS_OPTION_MENU = False


# ============================================================================
# Page config + theme state
# ============================================================================
st.set_page_config(
    page_title="AI Portfolio Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
db.init_db()

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Overview"


# ============================================================================
# Theme / CSS — fixed dark "hacker terminal" theme (green-on-black, no light mode)
# ============================================================================
def inject_theme() -> None:
    bg = "#070a10"
    bg_secondary = "#0b0f18"
    card_bg = "rgba(22, 28, 40, 0.55)"
    card_border = "rgba(148, 163, 184, 0.14)"
    card_border_hover = "rgba(45, 212, 191, 0.35)"
    text_primary = "#eef2f7"
    text_secondary = "#8a94a6"
    accent_mint = "#2dd4bf"       # teal-green — primary accent
    accent_blue = "#5b8def"       # electric blue — secondary accent
    accent_mint_soft = "rgba(45, 212, 191, 0.12)"
    accent_blue_soft = "rgba(91, 141, 239, 0.12)"
    accent_gradient = "linear-gradient(120deg, #2dd4bf 0%, #5b8def 100%)"
    positive = "#34d399"
    negative = "#fb7185"
    divider = "rgba(148, 163, 184, 0.10)"
    shadow = "0 8px 24px rgba(0, 0, 0, 0.35)"
    shadow_hover = "0 8px 28px rgba(45, 212, 191, 0.12)"
    input_bg = "#0d1220"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .stApp {{
        background:
            radial-gradient(circle at 15% -10%, rgba(45,212,191,0.06) 0%, transparent 45%),
            radial-gradient(circle at 85% 0%, rgba(91,141,239,0.06) 0%, transparent 45%),
            {bg};
        color: {text_primary};
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Sora', sans-serif !important;
        color: {text_primary} !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}

    p, span, label, div {{
        color: {text_primary};
    }}

    code, .stCodeBlock, [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* ---------- Sticky top header ---------- */
    .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        margin: -1rem -1rem 0.6rem -1rem;
        background: {bg_secondary};
        border-bottom: 1px solid {divider};
        backdrop-filter: blur(10px);
        position: sticky;
        top: 0;
        z-index: 999;
    }}
    .topbar-title {{
        font-family: 'Sora', sans-serif;
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .topbar-title .accent {{
        background: {accent_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .topbar-sub {{
        font-size: 0.78rem;
        color: {text_secondary};
        margin-top: 3px;
        font-weight: 500;
    }}
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 999px;
        background: {accent_mint_soft};
        color: {accent_mint};
        border: 1px solid rgba(45, 212, 191, 0.3);
        letter-spacing: 0.02em;
    }}
    .status-dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: {accent_mint};
        box-shadow: 0 0 8px {accent_mint};
        animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.45; }}
    }}

    /* ---------- Sticky horizontal nav (pinned as you scroll) ---------- */
    .navbar-anchor {{
        position: sticky;
        top: 70px;
        z-index: 998;
        background: {bg};
        padding: 8px 0 12px 0;
        margin: 0 -1rem 1.4rem -1rem;
        border-bottom: 1px solid {divider};
    }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{
        background: {bg_secondary};
        border-right: 1px solid {divider};
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.4rem;
    }}

    /* ---------- Cards (st.container(border=True)) — glassmorphism ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {card_bg};
        border: 1px solid {card_border} !important;
        border-radius: 14px;
        padding: 6px 8px;
        box-shadow: {shadow};
        backdrop-filter: blur(14px);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: {card_border_hover} !important;
        box-shadow: {shadow_hover};
    }}

    /* ---------- Metrics as KPI cards ---------- */
    div[data-testid="stMetric"] {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 16px 18px 12px 18px;
        box-shadow: {shadow};
        backdrop-filter: blur(14px);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {text_secondary} !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.68rem !important;
        letter-spacing: 0.06em;
    }}
    div[data-testid="stMetricValue"] {{
        color: {text_primary} !important;
        font-weight: 700;
    }}
    div[data-testid="stMetricDelta"] svg {{ display: none; }}

    /* ---------- Section headers ---------- */
    .section-header {{
        display: flex;
        align-items: baseline;
        gap: 10px;
        margin: 6px 0 16px 0;
        padding-bottom: 10px;
        border-bottom: 1px solid {divider};
    }}
    .section-header h3 {{
        margin: 0;
        font-weight: 700;
    }}
    .section-header .tag {{
        font-size: 0.7rem;
        font-weight: 600;
        color: {accent_mint};
        background: {accent_mint_soft};
        padding: 3px 10px;
        border-radius: 999px;
        letter-spacing: 0.03em;
        border: 1px solid rgba(45, 212, 191, 0.25);
    }}

    /* ---------- Buttons ---------- */
    .stButton>button {{
        background: {accent_gradient};
        color: #08110f;
        border: none;
        border-radius: 9px;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        padding: 0.5rem 1.2rem;
        letter-spacing: 0.01em;
        transition: transform 0.14s ease, box-shadow 0.14s ease, filter 0.14s ease;
        box-shadow: 0 4px 14px rgba(45, 212, 191, 0.18);
    }}
    .stButton>button:hover {{
        transform: translateY(-1px);
        filter: brightness(1.08);
        box-shadow: 0 6px 20px rgba(45, 212, 191, 0.28);
    }}
    .stButton>button:active {{
        transform: translateY(0px);
    }}

    /* ---------- Inputs ---------- */
    input, textarea, .stTextInput input, .stNumberInput input, .stChatInput textarea {{
        background: {input_bg} !important;
        color: {text_primary} !important;
        border-radius: 9px !important;
        border: 1px solid {card_border} !important;
        caret-color: {accent_mint};
    }}
    input:focus, textarea:focus {{
        border-color: {accent_mint} !important;
        box-shadow: 0 0 0 1px {accent_mint} !important;
    }}
    div[data-baseweb="select"] > div {{
        background: {input_bg} !important;
        border-radius: 9px !important;
        border: 1px solid {card_border} !important;
    }}

    /* ---------- Sliders / radio ---------- */
    .stSlider [data-baseweb="slider"] div div div {{
        background: {accent_gradient};
    }}
    .stRadio label, .stCheckbox label {{
        color: {text_primary} !important;
    }}

    /* ---------- Tables ---------- */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {card_border};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ---------- Chat bubbles (AI assistant) ---------- */
    div[data-testid="stChatMessage"] {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        box-shadow: {shadow};
        backdrop-filter: blur(14px);
    }}

    /* ---------- Alerts / callouts ---------- */
    div[data-testid="stAlert"] {{
        border-radius: 12px;
        border: 1px solid {card_border};
        background: {card_bg};
    }}

    /* ---------- Divider ---------- */
    hr {{ border-color: {divider} !important; }}

    /* ---------- Scrollbar ---------- */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: {bg}; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(148,163,184,0.25); border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {accent_mint}; }}
    </style>
    """, unsafe_allow_html=True)


inject_theme()


# ============================================================================
# Top header bar
# ============================================================================
st.markdown(
    """
    <div class="topbar">
        <div>
            <div class="topbar-title">📊 <span class="accent">Portfolio Intelligence</span> Dashboard</div>
            <div class="topbar-sub">Market data · Forecasting · Backtesting · AI Research Assistant</div>
        </div>
        <div class="status-pill"><span class="status-dot"></span> Live</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# Sidebar: existing settings only (navigation now lives in the sticky top nav)
# ============================================================================
with st.sidebar:
    st.markdown("#### ⚙️ Configuration")
    settings = sidebar.render_sidebar()
    ticker = settings["ticker"]
    period = settings["period"]
    portfolio_tickers = settings["portfolio_tickers"]


# ============================================================================
# Sticky horizontal navigation bar (pinned under the header as you scroll)
# ============================================================================
nav_items = ["Overview", "Strategies", "Forecasts", "Backtests",
             "AI Assistant", "Sentiment", "Alerts", "Settings"]
nav_icons = ["bar-chart-line", "wallet2", "graph-up-arrow", "clipboard-data",
             "robot", "newspaper", "bell", "gear"]

st.markdown('<div class="navbar-anchor">', unsafe_allow_html=True)
if HAS_OPTION_MENU:
    selected = option_menu(
        menu_title=None,
        options=nav_items,
        icons=nav_icons,
        default_index=nav_items.index(st.session_state.nav_page),
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"font-size": "14px", "color": "#2dd4bf"},
            "nav-link": {
                "font-size": "13px", "font-weight": "600", "text-align": "center",
                "margin": "0 3px", "border-radius": "8px", "color": "#8a94a6",
                "background-color": "rgba(22, 28, 40, 0.55)", "border": "1px solid rgba(148, 163, 184, 0.14)",
                "font-family": "'Inter', sans-serif",
            },
            "nav-link-selected": {
                "background": "linear-gradient(120deg, rgba(45,212,191,0.18), rgba(91,141,239,0.18))",
                "color": "#eef2f7", "font-weight": "700",
                "border": "1px solid rgba(45, 212, 191, 0.4)",
            },
        },

    )
else:
    emoji_map = ["📈", "💼", "🔮", "🧪", "🤖", "📰", "🚨", "⚙️"]
    labeled = [f"{e} {n}" for e, n in zip(emoji_map, nav_items)]
    nav_cols = st.columns(len(nav_items))
    selected = st.session_state.nav_page
    for col, label, item in zip(nav_cols, labeled, nav_items):
        with col:
            if st.button(label, key=f"nav_{item}", use_container_width=True):
                selected = item
st.markdown('</div>', unsafe_allow_html=True)

st.session_state.nav_page = selected


def section_header(title: str, tag: str = ""):
    tag_html = f'<span class="tag">{tag}</span>' if tag else ""
    st.markdown(f'<div class="section-header"><h3>{title}</h3>{tag_html}</div>', unsafe_allow_html=True)


# ============================================================================
# Load primary ticker data (shared across pages)
# ============================================================================
try:
    price_df = market_data.get_price_data(ticker, period=period, interval=DEFAULT_INTERVAL)
    price_df = indicators.add_all_indicators(price_df)
except ValueError as e:
    st.error(str(e))
    st.stop()

page = st.session_state.nav_page

# ================= Overview =================
if page == "Overview":
    info = market_data.get_company_info(ticker)
    section_header(f"{info['name']} ({ticker})", f"{info['sector']} · {info['industry']}")

    last_close = float(price_df["Close"].iloc[-1])
    prev_close = float(price_df["Close"].iloc[-2]) if len(price_df) > 1 else last_close
    change_pct = (last_close / prev_close - 1) * 100 if prev_close else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Last Close", f"{last_close:,.2f}", f"{change_pct:+.2f}%")
    kpi2.metric("RSI (14)", f"{float(price_df['RSI_14'].iloc[-1]):.1f}")
    kpi3.metric("SMA 20", f"{float(price_df['SMA_20'].iloc[-1]):,.2f}")
    kpi4.metric("SMA 50", f"{float(price_df['SMA_50'].iloc[-1]):,.2f}")

    st.write("")
    with st.container(border=True):
        st.plotly_chart(charts.build_price_chart(price_df), use_container_width=True)
    st.write("")
    with st.container(border=True):
        st.plotly_chart(charts.build_macd_chart(price_df), use_container_width=True)

# ================= Strategies (Portfolio Builder) =================
elif page == "Strategies":
    section_header("Portfolio Optimizer", "Strategies")

    ctrl_col, view_col = st.columns([1, 2.2])

    with ctrl_col:
        with st.container(border=True):
            st.markdown("**Controls**")
            if len(portfolio_tickers) < 2:
                st.info("Add at least 2 tickers in the sidebar to build a portfolio.")
                objective = None
                run_clicked = False
            else:
                objective = st.radio("Optimize for", ["max_sharpe", "min_volatility"])
                run_clicked = st.button("▶ Run optimizer", use_container_width=True)

    with view_col:
        if len(portfolio_tickers) >= 2:
            price_matrix = market_data.get_close_matrix(portfolio_tickers, period=period)

            if run_clicked:
                result = portfolio.optimize_portfolio(price_matrix, objective=objective)
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1.4])
                    with c1:
                        st.markdown("**Optimal weights**")
                        st.json(result["weights"])
                    with c2:
                        metrics.render_metric_row({
                            "expected_return": f"{result['expected_return']*100:.2f}%",
                            "volatility": f"{result['volatility']*100:.2f}%",
                            "sharpe": f"{result['sharpe']:.2f}",
                        })

                frontier = portfolio.efficient_frontier(price_matrix)
                if not frontier.empty:
                    with st.container(border=True):
                        st.plotly_chart(charts.build_efficient_frontier_chart(frontier, result),
                                         use_container_width=True)

            st.write("")
            with st.container(border=True):
                st.markdown("**Equal-weight baseline**")
                equal_weights = {t: 1 / len(portfolio_tickers) for t in portfolio_tickers}
                summary = portfolio.portfolio_summary(price_matrix, equal_weights)
                b1, b2, b3, b4 = st.columns(4)
                b1.metric("Annual Return", f"{summary['annual_return']*100:.2f}%")
                b2.metric("Volatility", f"{summary['annual_volatility']*100:.2f}%")
                b3.metric("Sharpe", f"{summary['sharpe']:.2f}")
                b4.metric("Max Drawdown", f"{summary['max_drawdown']*100:.2f}%")
                st.line_chart(summary["cumulative_growth"])

# ================= Forecasts =================
elif page == "Forecasts":
    section_header(f"ARIMA Forecast — {ticker}", "Forecast Lab")

    ctrl_col, view_col = st.columns([1, 2.2])
    with ctrl_col:
        with st.container(border=True):
            st.markdown("**Controls**")
            holdout = st.slider("Holdout window (days, for evaluation)", 10, 60, 30)
            steps = st.slider("Forecast horizon (days)", 5, 60, 30)
            run_eval = st.button("▶ Run backtested evaluation", use_container_width=True)
            run_fwd = st.button("🔮 Forecast forward", use_container_width=True)

    with view_col:
        if run_eval:
            with st.spinner("Fitting ARIMA on holdout window..."):
                comparison, eval_metrics, order = forecasting.backtest_forecast(price_df["Close"], holdout=holdout)
                db.log_forecast_run(ticker, order, eval_metrics)
            with st.container(border=True):
                st.caption(f"Best order found: `{order}`")
                metrics.render_metric_row(eval_metrics)
                st.plotly_chart(charts.build_forecast_eval_chart(comparison), use_container_width=True)

        if run_fwd:
            with st.spinner("Forecasting..."):
                forecast_df, order, _ = forecasting.fit_and_forecast(price_df["Close"], steps=steps)
            with st.container(border=True):
                st.plotly_chart(charts.build_forward_forecast_chart(price_df, forecast_df, steps, order),
                                 use_container_width=True)

        if not run_eval and not run_fwd:
            st.info("Set your parameters on the left, then run an evaluation or forward forecast.")

# ================= Backtests =================
elif page == "Backtests":
    section_header("Strategy Backtest — SMA Crossover vs Buy & Hold", "Backtesting Lab")

    ctrl_col, view_col = st.columns([1, 2.2])
    with ctrl_col:
        with st.container(border=True):
            st.markdown("**Controls**")
            fast = st.slider("Fast SMA window", 5, 50, 20)
            slow = st.slider("Slow SMA window", 20, 200, 50)
            cost_bps = st.number_input("Transaction cost (bps per trade)", 0.0, 50.0, 5.0)
            run_bt = st.button("▶ Run backtest", use_container_width=True)

        with st.expander("⚡ Advanced: vectorbt engine"):
            st.caption("Vectorized EMA-crossover backtest via the `vectorbt` library. "
                       "Only works if `vectorbt` is installed and importable in this environment "
                       "(needs Python ≤3.10).")
            from services import backtest_vectorbt
            if backtest_vectorbt.is_available():
                run_vbt = st.button("Run vectorbt backtest", use_container_width=True)
            else:
                run_vbt = False
                st.warning("vectorbt is not installed. Install it in a Python 3.10 venv with "
                           "`pip install vectorbt` to use this engine.")

    with view_col:
        if run_bt:
            trade_log, bt_summary = backtest.run_backtest(price_df["Close"], fast=fast, slow=slow, cost_bps=cost_bps)
            with st.container(border=True):
                s = bt_summary["strategy"]
                bh = bt_summary["buy_and_hold"]
                st.markdown("**Strategy vs Buy & Hold**")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Return", f"{s.get('total_return', 0)*100:.2f}%",
                          f"{(s.get('total_return', 0) - bh.get('total_return', 0))*100:+.2f}% vs B&H")
                m2.metric("Sharpe", f"{s.get('sharpe', 0):.2f}")
                m3.metric("Max Drawdown", f"{s.get('max_drawdown', 0)*100:.2f}%")
                m4.metric("Trades", f"{bt_summary['num_trades']}")
                metrics.render_comparison_metrics("Strategy", s, "Buy & Hold", bh)
                st.plotly_chart(charts.build_equity_curve_chart(trade_log), use_container_width=True)

        if "run_vbt" in dir() and run_vbt:
            try:
                _, vbt_summary = backtest_vectorbt.run_vectorbt_backtest(price_df["Close"], fast=fast, slow=slow)
                with st.container(border=True):
                    st.markdown("**vectorbt engine results**")
                    metrics.render_metric_row(vbt_summary)
            except ImportError as e:
                st.error(str(e))

        if not run_bt:
            st.info("Configure the backtest on the left and click **Run backtest**.")

# ================= AI Assistant =================
elif page == "AI Assistant":
    section_header("AI Finance Assistant", "Chat")

    recent = price_df["Close"].tail(63)
    ai_context = {
        "period": period,
        "latest_close": round(float(price_df["Close"].iloc[-1]), 2),
        "change_pct_over_period": round(float(recent.iloc[-1] / recent.iloc[0] - 1) * 100, 2),
        "sma_20": round(float(price_df["SMA_20"].iloc[-1]), 2),
        "sma_50": round(float(price_df["SMA_50"].iloc[-1]), 2),
        "rsi_14": round(float(price_df["RSI_14"].iloc[-1]), 2),
        "recent_alerts": alerts.summarize_alerts(price_df["Close"]),
    }

    chat_col, side_col = st.columns([2, 1])

    with side_col:
        with st.container(border=True):
            st.markdown("**Quick read**")
            st.caption(f"Ticker: `{ticker}`")
            if st.button("Get Bullish / Bearish / Neutral read", use_container_width=True):
                with st.spinner("Analyzing..."):
                    rec = llm_agent.get_ticker_recommendation(ticker, ai_context)
                emoji = {"Bullish": "📈", "Bearish": "📉", "Neutral": "➖"}[rec["action"]]
                color = {"Bullish": "#34d399", "Bearish": "#fb7185", "Neutral": "#8a94a6"}[rec["action"]]
                st.markdown(
                    f"<div style='font-size:1.4rem;font-weight:800;color:{color};'>"
                    f"{emoji} {rec['action']}</div>", unsafe_allow_html=True)
                st.write(rec["justification"])

        with st.container(border=True):
            st.markdown("**Live context**")
            st.json(ai_context)

    with chat_col:
        with st.container(border=True):
            history = db.get_chat_history(ticker)
            if history:
                for turn in history:
                    q = turn.get("question") if isinstance(turn, dict) else turn[0]
                    a = turn.get("answer") if isinstance(turn, dict) else turn[1]
                    with st.chat_message("user"):
                        st.write(q)
                    with st.chat_message("assistant"):
                        st.markdown(a)
            else:
                st.caption("Ask a question about strategy, risk, or forecasts to get started.")

            question = st.chat_input(f"Ask about {ticker}'s trend, risk, or forecast...")
            if question:
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        answer = llm_agent.ask_llm(question, ticker, ai_context)
                    st.markdown(answer)
                db.log_chat(ticker, question, answer)
                st.rerun()

# ================= Sentiment =================
elif page == "Sentiment":
    section_header(f"News Sentiment — {ticker}", "NLP")
    st.caption("Headlines pulled live from yfinance; scored with a lightweight built-in lexicon "
               "(swap in a real NLP model or LLM call for more nuance).")

    summary = sentiment.summarize_sentiment(ticker)
    if summary["headline_count"] == 0:
        st.info(summary["label"])
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Headlines", summary["headline_count"])
        c2.metric("Average Score", summary["average_score"])
        c3.metric("Read", summary["label"])

        news_df = sentiment.get_recent_news(ticker)
        with st.container(border=True):
            st.plotly_chart(charts.build_sentiment_chart(news_df), use_container_width=True)
        with st.container(border=True):
            tables.render_headlines_table(news_df)

# ================= Alerts =================
elif page == "Alerts":
    section_header("Anomaly & Volatility Alerts", "Risk")

    with st.container(border=True):
        for msg in alerts.summarize_alerts(price_df["Close"]):
            st.warning(msg)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**Recent flagged price moves**")
            shocks = alerts.detect_price_shocks(price_df["Close"])
            tables.render_dataframe(shocks.tail(10), caption="")
    with col2:
        with st.container(border=True):
            st.markdown("**Recent volatility spikes**")
            vol_spikes = alerts.detect_volatility_spikes(price_df["Close"])
            tables.render_dataframe(vol_spikes.tail(10), caption="")

# ================= Settings =================
elif page == "Settings":
    section_header("Settings", "App")

    with st.container(border=True):
        st.markdown("**Appearance**")
        st.caption("Theme is fixed: dark, glass-panel fintech look with mint + electric-blue accents.")
        st.write("Current theme: `midnight_mint`")

    with st.container(border=True):
        st.markdown("**Session**")
        st.write(f"Active ticker: `{ticker}`")
        st.write(f"Period: `{period}`")
        st.write(f"Portfolio tickers: `{', '.join(portfolio_tickers) if portfolio_tickers else 'none'}`")

    with st.container(border=True):
        st.markdown("**About**")
        st.caption(
            "AI-Powered Portfolio Intelligence Dashboard — market data, technical "
            "indicators, portfolio optimization, ARIMA forecasting, SMA-crossover "
            "backtesting, an AI research assistant, news sentiment, and anomaly alerts."
        )