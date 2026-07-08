"""
components/metrics.py
Small helpers for rendering a dict of metrics as a row of st.metric cards,
so every tab formats numbers consistently instead of hand-rolling columns.
"""
import streamlit as st


def render_metric_row(metrics: dict, max_per_row: int = 4):
    """
    Render a flat dict as a row (or rows) of st.metric cards.
    Keys are used as labels (snake_case is prettified); values may be
    plain numbers/strings, or (value, delta) tuples.
    """
    items = list(metrics.items())
    for start in range(0, len(items), max_per_row):
        chunk = items[start:start + max_per_row]
        cols = st.columns(len(chunk))
        for col, (label, value) in zip(cols, chunk):
            pretty_label = label.replace("_", " ").replace("%", "").strip().title()
            if isinstance(value, tuple):
                col.metric(pretty_label, value[0], value[1])
            else:
                col.metric(pretty_label, value)


def render_comparison_metrics(title_a: str, metrics_a: dict, title_b: str, metrics_b: dict):
    """Side-by-side metric comparison, e.g. Strategy vs Buy & Hold."""
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{title_a}**")
        st.json(metrics_a)
    with col2:
        st.write(f"**{title_b}**")
        st.json(metrics_b)
