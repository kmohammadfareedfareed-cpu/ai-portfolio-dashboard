"""
components/tables.py
Table/dataframe rendering helpers -- alerts tables, chat history, and
clickable news headlines all go through here for consistent formatting.
"""
import pandas as pd
import streamlit as st


def render_dataframe(df: pd.DataFrame, caption: str | None = None, height: int | None = None):
    if caption:
        st.write(f"**{caption}**")
    if df.empty:
        st.caption("No rows to display.")
        return
    # st.dataframe's height validator rejects None outright (must be a positive
    # int, "stretch", or "content") -- only pass it through when it's a real value.
    kwargs = {"width": "stretch"}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(df, **kwargs)


def render_headlines_table(news_df: pd.DataFrame):
    """Render fetched headlines as a clickable list with sentiment tags."""
    if news_df.empty:
        st.caption("No recent headlines found for this ticker.")
        return
    for _, row in news_df.iterrows():
        tag = "🟢" if row["Score"] > 0 else "🔴" if row["Score"] < 0 else "⚪"
        title = row["Title"]
        link = row.get("Link") or ""
        publisher = row.get("Publisher", "")
        if link:
            st.markdown(f"{tag} [{title}]({link})  \n*{publisher} — score {row['Score']:+.2f}*")
        else:
            st.markdown(f"{tag} {title}  \n*{publisher} — score {row['Score']:+.2f}*")


def render_chat_history(rows):
    """rows: iterable of (question, answer, timestamp) tuples."""
    if not rows:
        st.caption("No conversation yet for this ticker.")
        return
    for q, a, ts in rows:
        st.markdown(f"**Q ({ts[:19]}):** {q}")
        st.markdown(f"**A:** {a}")
        st.divider()