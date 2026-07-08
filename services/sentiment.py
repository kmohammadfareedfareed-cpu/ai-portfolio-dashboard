"""
sentiment.py
Lightweight news sentiment layer. Pulls recent headlines straight from
yfinance (no external news API key required) and scores them with a small
built-in positive/negative lexicon. This is intentionally simple and
deterministic -- swap `_score_text` for a proper model (VADER, a
HuggingFace sentiment pipeline, or an LLM call) if you need more nuance.
"""
import re
from collections import Counter

import pandas as pd
import yfinance as yf
import streamlit as st

_POSITIVE_WORDS = {
    "beat", "beats", "growth", "surge", "surges", "soar", "soars", "rally",
    "rallies", "gain", "gains", "upgrade", "upgraded", "outperform", "record",
    "strong", "strength", "profit", "profits", "bullish", "optimistic",
    "expand", "expands", "expansion", "buyback", "breakthrough", "win", "wins",
    "positive", "boost", "boosts", "recover", "recovery", "top", "tops",
}

_NEGATIVE_WORDS = {
    "miss", "misses", "decline", "declines", "plunge", "plunges", "slump",
    "sinks", "sink", "downgrade", "downgraded", "underperform", "weak",
    "weakness", "loss", "losses", "bearish", "pessimistic", "cut", "cuts",
    "layoff", "layoffs", "lawsuit", "investigation", "recall", "warning",
    "negative", "risk", "risks", "fraud", "scandal", "crash", "crashes",
    "fall", "falls", "drop", "drops",
}

_WORD_RE = re.compile(r"[a-zA-Z']+")


def _score_text(text: str) -> float:
    """Return a score in [-1, 1]: fraction of sentiment words that are positive minus negative."""
    words = [w.lower() for w in _WORD_RE.findall(text or "")]
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in _POSITIVE_WORDS)
    neg = sum(1 for w in words if w in _NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


@st.cache_data(ttl=1800, show_spinner=False)
def get_recent_news(ticker: str, limit: int = 10) -> pd.DataFrame:
    """Fetch recent headlines for a ticker directly from yfinance."""
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        raw = []

    rows = []
    for item in raw[:limit]:
        # yfinance nests fields under "content" in newer versions, flat in older ones
        content = item.get("content", item)
        title = content.get("title") or item.get("title", "")
        publisher = (content.get("provider") or {}).get("displayName") if isinstance(content.get("provider"), dict) else item.get("publisher", "")
        link = (content.get("canonicalUrl") or {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else item.get("link", "")
        if not title:
            continue
        rows.append({"Title": title, "Publisher": publisher or "Unknown", "Link": link, "Score": _score_text(title)})

    return pd.DataFrame(rows)


def summarize_sentiment(ticker: str, limit: int = 10) -> dict:
    """Aggregate headline-level sentiment into a single ticker-level summary."""
    news = get_recent_news(ticker, limit=limit)
    if news.empty:
        return {"headline_count": 0, "average_score": 0.0, "label": "No recent headlines found", "headlines": []}

    avg = round(float(news["Score"].mean()), 3)
    if avg > 0.15:
        label = "Net positive"
    elif avg < -0.15:
        label = "Net negative"
    else:
        label = "Mixed / neutral"

    counts = Counter("Positive" if s > 0 else "Negative" if s < 0 else "Neutral" for s in news["Score"])
    return {
        "headline_count": int(len(news)),
        "average_score": avg,
        "label": label,
        "breakdown": dict(counts),
        "headlines": news.to_dict("records"),
    }
