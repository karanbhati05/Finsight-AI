# app/pages/dashboard.py
"""
Sentiment Dashboard — Page 1 of the FinSight AI Streamlit app.

Shows:
    - Company overview KPI cards
    - Sentiment trend over time (line chart)
    - Sentiment distribution (pie chart)
    - Top mentioned entities (companies, people, money)
    - Recent news feed with sentiment badges
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from src.utils.constants import (
    PROCESSED_DATA_DIR,
    SENTIMENT_COLOR_MAP,
    TICKER_COMPANY_MAP,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_enriched_news(ticker: str) -> pd.DataFrame:
    """Load the NLP-enriched news CSV for a ticker."""
    path = Path(PROCESSED_DATA_DIR) / ticker / "news_enriched.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    return df


def sentiment_badge(label: str) -> str:
    """Return a colored HTML badge for a sentiment label."""
    colors = {
        "positive": ("#dcfce7", "#16a34a"),   # green background, dark green text
        "negative": ("#fee2e2", "#dc2626"),   # red background, dark red text
        "neutral":  ("#f1f5f9", "#64748b"),   # gray background, dark gray text
    }
    bg, fg = colors.get(label, colors["neutral"])
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-size:12px;font-weight:500;">'
        f'{label.upper()}</span>'
    )


# ── KPI Cards ─────────────────────────────────────────────────────────────────

def render_kpi_cards(df: pd.DataFrame, ticker: str) -> None:
    """Render the top row of metric cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    avg_score   = df["sentiment_score"].mean()   if "sentiment_score"   in df.columns else 0
    pos_pct     = (df["sentiment_label"] == "positive").mean() * 100 \
                  if "sentiment_label" in df.columns else 0
    neg_pct     = (df["sentiment_label"] == "negative").mean() * 100 \
                  if "sentiment_label" in df.columns else 0

    # Sentiment trend: compare last 7 days vs previous 7 days
    score_delta = None
    if "published_at" in df.columns and "sentiment_score" in df.columns:
        df_sorted = df.sort_values("published_at")
        recent  = df_sorted.tail(int(len(df_sorted) * 0.3))["sentiment_score"].mean()
        older   = df_sorted.head(int(len(df_sorted) * 0.3))["sentiment_score"].mean()
        score_delta = round(recent - older, 3)

    col1.metric(
        "Articles Analyzed",
        f"{len(df):,}",
    )
    col2.metric(
        "Avg Sentiment Score",
        f"{avg_score:+.3f}",
        delta      = f"{score_delta:+.3f} trend" if score_delta is not None else None,
        delta_color = "normal",
    )
    col3.metric(
        "Positive Coverage",
        f"{pos_pct:.1f}%",
    )
    col4.metric(
        "Negative Coverage",
        f"{neg_pct:.1f}%",
    )
    col5.metric(
        "Neutral Coverage",
        f"{100 - pos_pct - neg_pct:.1f}%",
    )


# ── Charts ────────────────────────────────────────────────────────────────────

def render_sentiment_trend(df: pd.DataFrame) -> None:
    """Line chart of daily average sentiment score over time."""
    if "published_at" not in df.columns or "sentiment_score" not in df.columns:
        st.info("No sentiment trend data available.")
        return

    df_copy = df.copy()
    df_copy["date"] = df_copy["published_at"].dt.date

    daily = (
        df_copy.groupby("date")
        .agg(
            avg_score     = ("sentiment_score", "mean"),
            article_count = ("sentiment_score", "count"),
            pos_ratio     = ("sentiment_label",
                             lambda x: (x == "positive").mean()),
        )
        .reset_index()
    )

    # Dual-axis chart: sentiment score (line) + article count (bars)
    fig = go.Figure()

    # Bar chart for article volume
    fig.add_trace(go.Bar(
        x     = daily["date"],
        y     = daily["article_count"],
        name  = "Article Count",
        yaxis = "y2",
        marker_color = "rgba(148, 163, 184, 0.3)",
        hovertemplate = "%{y} articles<extra></extra>",
    ))

    # Line chart for sentiment score
    fig.add_trace(go.Scatter(
        x    = daily["date"],
        y    = daily["avg_score"],
        name = "Avg Sentiment",
        mode = "lines+markers",
        line = dict(color="#3b82f6", width=2),
        marker = dict(size=5),
        hovertemplate = "Score: %{y:.3f}<extra></extra>",
    ))

    # Zero line — neutral sentiment reference
    fig.add_hline(
        y           = 0,
        line_dash   = "dash",
        line_color  = "rgba(100,100,100,0.4)",
        annotation_text = "Neutral",
        annotation_position = "bottom right",
    )

    fig.update_layout(
        title   = "Daily Sentiment Score & Article Volume",
        xaxis   = dict(title="Date"),
        yaxis   = dict(
            title      = "Sentiment Score",
            range      = [-1, 1],
            tickformat = "+.2f",
            side       = "left",
        ),
        yaxis2  = dict(
            title    = "Article Count",
            overlaying = "y",
            side     = "right",
            showgrid = False,
        ),
        legend  = dict(orientation="h", y=1.1),
        hovermode = "x unified",
        height  = 400,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_sentiment_distribution(df: pd.DataFrame) -> None:
    """Pie chart of sentiment label distribution."""
    if "sentiment_label" not in df.columns:
        return

    counts = df["sentiment_label"].value_counts().reset_index()
    counts.columns = ["label", "count"]

    fig = px.pie(
        counts,
        names  = "label",
        values = "count",
        title  = "Sentiment Distribution",
        color  = "label",
        color_discrete_map = SENTIMENT_COLOR_MAP,
        hole   = 0.4,    # donut chart — cleaner than full pie
    )
    fig.update_traces(
        textposition = "inside",
        textinfo     = "percent+label",
        hovertemplate = "%{label}: %{value} articles (%{percent})<extra></extra>",
    )
    fig.update_layout(
        showlegend = False,
        height     = 320,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_entity_summary(df: pd.DataFrame) -> None:
    """
    Show top mentioned companies, people, and money amounts.
    Parses the 'entity_orgs' column saved by ner.py.
    """
    if "entity_orgs" not in df.columns:
        st.info("Entity data not available. Re-run pipeline with NER enabled.")
        return

    st.subheader("Most Mentioned Entities")

    # Parse comma-separated org strings into flat list
    all_orgs = []
    for val in df["entity_orgs"].dropna():
        all_orgs.extend([o.strip() for o in val.split(",") if o.strip()])

    if not all_orgs:
        st.info("No entity data found.")
        return

    from collections import Counter
    org_counts = Counter(all_orgs).most_common(10)
    org_df     = pd.DataFrame(org_counts, columns=["Entity", "Mentions"])

    fig = px.bar(
        org_df,
        x                 = "Mentions",
        y                 = "Entity",
        orientation       = "h",
        title             = "Top Mentioned Companies / Organizations",
        color             = "Mentions",
        color_continuous_scale = "Blues",
    )
    fig.update_layout(
        height     = 350,
        showlegend = False,
        yaxis      = dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_news_feed(df: pd.DataFrame) -> None:
    """Render paginated news feed with sentiment badges."""
    st.subheader("Recent News")

    if df.empty:
        st.info("No news articles available.")
        return

    # Sort by date descending
    display_df = df.sort_values("published_at", ascending=False).head(50)

    # Pagination
    page_size = 10
    n_pages   = max(1, len(display_df) // page_size)
    page      = st.selectbox(
        "Page",
        range(1, n_pages + 1),
        format_func = lambda x: f"Page {x} of {n_pages}",
    )

    start = (page - 1) * page_size
    page_df = display_df.iloc[start : start + page_size]

    for _, row in page_df.iterrows():
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                title  = row.get("title",  "No title")
                source = row.get("source", "Unknown")
                date   = str(row.get("published_at", ""))[:10]
                url    = row.get("url", "")

                if url:
                    st.markdown(f"**[{title}]({url})**")
                else:
                    st.markdown(f"**{title}**")

                st.caption(f"{source} · {date}")

                # Show summary if available
                summary = row.get("summary", "")
                if summary and isinstance(summary, str) and len(summary) > 10:
                    st.markdown(
                        f'<p style="color:#64748b;font-size:13px;">{summary}</p>',
                        unsafe_allow_html=True,
                    )

            with col2:
                label = row.get("sentiment_label", "neutral")
                st.markdown(sentiment_badge(label), unsafe_allow_html=True)
                score = row.get("sentiment_score", 0)
                if isinstance(score, float):
                    st.caption(f"Score: {score:+.3f}")

        st.divider()


# ── Main render function ───────────────────────────────────────────────────────

def render(ticker: str) -> None:
    """
    Main entry point called by streamlit_app.py.
    Renders the full dashboard for the selected ticker.
    """
    company = TICKER_COMPANY_MAP.get(ticker, ticker)

    st.title(f"📊 {company} ({ticker}) — Sentiment Dashboard")
    st.caption(
        "Powered by FinBERT sentiment analysis · spaCy NER · "
        "Real-time financial news"
    )

    # Load data
    df = load_enriched_news(ticker)

    if df.empty:
        st.warning(
            f"No data found for **{ticker}**. Run the pipeline first:\n\n"
            f"```bash\npython scripts/run_pipeline.py --ticker {ticker}\n```"
        )
        return

    # ── KPI Row ──────────────────────────────────────────────────────────────
    render_kpi_cards(df, ticker)
    st.divider()

    # ── Charts Row ───────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns([2, 1])

    with chart_col1:
        render_sentiment_trend(df)

    with chart_col2:
        render_sentiment_distribution(df)

    st.divider()

    # ── Entities ─────────────────────────────────────────────────────────────
    render_entity_summary(df)
    st.divider()

    # ── News Feed ────────────────────────────────────────────────────────────
    render_news_feed(df)