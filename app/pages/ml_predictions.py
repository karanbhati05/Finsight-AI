# app/pages/ml_predictions.py
"""
ML Predictions Page — Page 3 of the FinSight AI Streamlit app.

Shows:
    - Today's price direction prediction + confidence
    - Prediction probability history chart
    - XGBoost feature importance chart
    - Strategy vs Buy-and-Hold Sharpe ratio comparison
    - Recent predictions table
"""

import pickle
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from src.utils.constants import (
    MODELS_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    FEATURE_COLS,
    TICKER_COMPANY_MAP,
)


# ── Data loading ───────────────────────────────────────────────────────────────

def load_model_dict(ticker: str) -> dict:
    """Load saved model dict. Returns None if not found."""
    path = Path(MODELS_DIR) / f"{ticker}_xgb_model.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def load_price_data(ticker: str) -> pd.DataFrame:
    """Load price data with technical indicators."""
    path = Path(RAW_DATA_DIR) / ticker / "price_data.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def load_enriched_news(ticker: str) -> pd.DataFrame:
    """Load NLP-enriched news with sentiment scores."""
    path = Path(PROCESSED_DATA_DIR) / ticker / "news_enriched.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    return df


# ── Today's prediction card ────────────────────────────────────────────────────

def render_prediction_card(ticker: str, model_dict: dict) -> None:
    """
    Render the hero card showing today's prediction.
    This is the first thing users see — make it clear and impactful.
    """
    st.subheader("Today's Prediction")

    try:
        price_df = load_price_data(ticker)
        news_df  = load_enriched_news(ticker)

        if price_df.empty or news_df.empty:
            st.info("Run the pipeline to generate predictions.")
            return

        from src.ml.predict import predict_latest
        result = predict_latest(
            ticker       = ticker,
            price_df     = price_df,
            sentiment_df = news_df,
        )

        if "error" in result:
            st.warning(f"Prediction unavailable: {result['error']}")
            return

        # ── Display prediction ───────────────────────────────────────────────
        label       = result["label"]
        probability = result["probability"]
        confidence  = result["confidence"]
        date        = result.get("date", "Latest")

        # Color based on direction
        is_up   = result["prediction"] == 1
        color   = "#22c55e" if is_up else "#ef4444"
        icon    = "↑" if is_up else "↓"

        col1, col2, col3 = st.columns(3)

        col1.markdown(
            f"""
            <div style="text-align:center;padding:20px;border-radius:12px;
                        border:2px solid {color};background:{color}15;">
                <div style="font-size:48px;color:{color};">{icon}</div>
                <div style="font-size:24px;font-weight:600;color:{color};">
                    {label}
                </div>
                <div style="color:#64748b;font-size:13px;">
                    Predicted direction · {date}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col2.metric(
            "Probability (Up)",
            f"{probability:.1%}",
            help="Model's confidence that price will increase tomorrow",
        )

        col3.metric(
            "Signal Confidence",
            confidence,
            help="High: >65% or <35% probability. Medium: 55-65%. Low: 45-55%",
        )

        # Show key features used
        features = result.get("features", {})
        if features:
            with st.expander("📊 Input features used"):
                feat_df = pd.DataFrame([
                    {"Feature": k, "Value": round(v, 4)}
                    for k, v in features.items()
                ])
                st.dataframe(feat_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error generating prediction: {e}")


# ── Probability history chart ──────────────────────────────────────────────────

def render_probability_chart(ticker: str, model_dict: dict) -> None:
    """
    Line chart of predicted up-probability over time.
    Shows how the model's confidence has evolved — useful for spotting
    when the model started turning bullish or bearish.
    """
    st.subheader("Prediction History")

    try:
        price_df = load_price_data(ticker)
        news_df  = load_enriched_news(ticker)

        if price_df.empty or news_df.empty:
            st.info("No prediction history available.")
            return

        from src.ml.predict import get_prediction_history
        pred_df = get_prediction_history(ticker, price_df, news_df)

        if pred_df.empty:
            st.info("Insufficient data for prediction history.")
            return

        # Show last 90 days
        pred_df = pred_df.tail(90)

        fig = go.Figure()

        # Confidence bands
        fig.add_hrect(
            y0=0.65, y1=1.0,
            fillcolor="#dcfce7", opacity=0.3,
            line_width=0, annotation_text="Strong Buy Zone",
            annotation_position="top left",
        )
        fig.add_hrect(
            y0=0.0, y1=0.35,
            fillcolor="#fee2e2", opacity=0.3,
            line_width=0, annotation_text="Strong Sell Zone",
            annotation_position="bottom left",
        )

        # Probability line
        fig.add_trace(go.Scatter(
            x    = pred_df["date"],
            y    = pred_df["up_probability"],
            mode = "lines",
            name = "P(Price Up)",
            line = dict(color="#3b82f6", width=2),
            fill = "tozeroy",
            fillcolor = "rgba(59, 130, 246, 0.08)",
            hovertemplate = "Date: %{x}<br>P(Up): %{y:.1%}<extra></extra>",
        ))

        # 50% neutral line
        fig.add_hline(
            y=0.5, line_dash="dash",
            line_color="rgba(100,100,100,0.5)",
            annotation_text="50% (Neutral)",
        )

        fig.update_layout(
            title     = f"Predicted Probability of Price Increase — Last 90 Days",
            xaxis     = dict(title="Date"),
            yaxis     = dict(
                title      = "P(Up)",
                range      = [0, 1],
                tickformat = ".0%",
            ),
            height    = 380,
            hovermode = "x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error rendering probability chart: {e}")


# ── Feature importance chart ───────────────────────────────────────────────────

def render_feature_importance(model_dict: dict) -> None:
    """
    Horizontal bar chart of XGBoost feature importances.

    This is one of the most important charts for explaining the model
    to non-technical stakeholders:
    'The model primarily uses sentiment trend and RSI to make predictions.'
    """
    st.subheader("What Drives the Model?")

    test_metrics = model_dict.get("test_metrics", {})

    # Model performance summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Test Accuracy",  f"{test_metrics.get('accuracy',  0):.1%}")
    col2.metric("F1 Score",       f"{test_metrics.get('f1',        0):.3f}")
    col3.metric("ROC-AUC",        f"{test_metrics.get('roc_auc',   0):.3f}")
    col4.metric("CV F1 (Mean)",   f"{model_dict.get('cv_mean_f1',  0):.3f}")

    st.markdown("")

    # Feature importance from saved model
    model = model_dict.get("model")
    feat_cols = model_dict.get("feature_cols", FEATURE_COLS)

    if model is None:
        st.info("Model not found.")
        return

    clf = model.named_steps.get("clf")
    if clf is None or not hasattr(clf, "feature_importances_"):
        st.info("Feature importance not available.")
        return

    importances = clf.feature_importances_
    fi_df = pd.DataFrame({
        "Feature":    feat_cols[:len(importances)],
        "Importance": importances,
    }).sort_values("Importance", ascending=True)

    fig = px.bar(
        fi_df,
        x                  = "Importance",
        y                  = "Feature",
        orientation        = "h",
        title              = "XGBoost Feature Importance (Gain)",
        color              = "Importance",
        color_continuous_scale = "Viridis",
    )
    fig.update_layout(
        height     = 420,
        showlegend = False,
        xaxis      = dict(title="Importance (Gain)"),
        yaxis      = dict(title=""),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "**Gain importance**: average loss reduction from splits on each feature. "
        "Higher = more predictive power."
    )


# ── Sharpe ratio comparison ────────────────────────────────────────────────────

def render_sharpe_comparison(ticker: str, model_dict: dict) -> None:
    """
    Compare model trading strategy vs buy-and-hold using Sharpe ratio.
    This is the financial performance translation of model accuracy.
    """
    st.subheader("Strategy vs Buy-and-Hold")

    try:
        price_df = load_price_data(ticker)
        news_df  = load_enriched_news(ticker)

        if price_df.empty or news_df.empty:
            st.info("No data available for Sharpe ratio simulation.")
            return

        from src.ml.feature_engineering import build_feature_matrix, get_X_y
        from src.ml.evaluate import simulate_strategy_returns

        feature_df = build_feature_matrix(price_df, news_df)
        if feature_df.empty:
            st.info("Insufficient data for strategy simulation.")
            return

        model = model_dict["model"]
        X, y  = get_X_y(feature_df)

        # Use the last 20% as test period for simulation
        split     = int(len(X) * 0.8)
        X_test    = X.iloc[split:]

        sim = simulate_strategy_returns(model, X_test, price_df, ticker)

        if not sim:
            st.info("Strategy simulation requires daily_return column.")
            return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "Strategy Sharpe",
            f"{sim['strategy_sharpe']:.2f}",
            delta     = f"{sim['strategy_sharpe'] - sim['buyhold_sharpe']:+.2f} vs B&H",
            delta_color = "normal",
        )
        col2.metric(
            "Buy & Hold Sharpe",
            f"{sim['buyhold_sharpe']:.2f}",
        )
        col3.metric(
            "Strategy Return",
            f"{sim['strategy_cumret']:.1%}",
        )
        col4.metric(
            "Buy & Hold Return",
            f"{sim['buyhold_cumret']:.1%}",
        )

        st.caption(
            f"Model traded on {sim['n_trades']} of "
            f"{int(sim['n_trades'] / sim['trade_rate']) if sim['trade_rate'] > 0 else 0} "
            f"test days ({sim['trade_rate']:.0%} of days). "
            f"Sharpe > 1.0 = good risk-adjusted return."
        )

    except Exception as e:
        st.error(f"Sharpe simulation error: {e}")


# ── Recent predictions table ───────────────────────────────────────────────────

def render_predictions_table(ticker: str, model_dict: dict) -> None:
    """Show the most recent 20 predictions with actual outcomes."""
    st.subheader("Recent Predictions")

    try:
        price_df = load_price_data(ticker)
        news_df  = load_enriched_news(ticker)

        if price_df.empty or news_df.empty:
            return

        from src.ml.predict import get_prediction_history
        pred_df = get_prediction_history(ticker, price_df, news_df)

        if pred_df.empty:
            return

        display_cols = [
            c for c in [
                "date", "close", "up_probability",
                "prediction_label", "sentiment_score", "rsi_14",
            ]
            if c in pred_df.columns
        ]

        display_df = pred_df[display_cols].tail(20).sort_values(
            "date", ascending=False
        )

        # Rename for readability
        rename_map = {
            "close":            "Close Price",
            "up_probability":   "P(Up)",
            "prediction_label": "Prediction",
            "sentiment_score":  "Sentiment",
            "rsi_14":           "RSI",
        }
        display_df = display_df.rename(columns=rename_map)

        st.dataframe(
            display_df,
            use_container_width = True,
            hide_index          = True,
        )

    except Exception as e:
        st.error(f"Error loading predictions table: {e}")


# ── Main render function ───────────────────────────────────────────────────────

def render(ticker: str) -> None:
    """
    Main entry point called by streamlit_app.py.
    Renders the full ML predictions page.
    """
    company = TICKER_COMPANY_MAP.get(ticker, ticker)

    st.title(f"📈 {company} ({ticker}) — ML Predictions")
    st.caption(
        "XGBoost classifier trained on FinBERT sentiment + "
        "technical indicators · Predicts next-day price direction"
    )

    # Load model
    model_dict = load_model_dict(ticker)

    if model_dict is None:
        st.warning(
            f"No trained model found for **{ticker}**.\n\n"
            f"Run the pipeline first:\n"
            f"```bash\npython scripts/run_pipeline.py --ticker {ticker}\n```"
        )
        return

    cv_f1 = model_dict.get("cv_mean_f1", 0)
    st.success(
        f"Model loaded ✓ · CV F1: {cv_f1:.3f} · "
        f"Trained on sentiment + technical features"
    )

    # ── Today's prediction ───────────────────────────────────────────────────
    render_prediction_card(ticker, model_dict)
    st.divider()

    # ── Probability history ──────────────────────────────────────────────────
    render_probability_chart(ticker, model_dict)
    st.divider()

    # ── Feature importance + metrics ─────────────────────────────────────────
    render_feature_importance(model_dict)
    st.divider()

    # ── Sharpe comparison ────────────────────────────────────────────────────
    render_sharpe_comparison(ticker, model_dict)
    st.divider()

    # ── Predictions table ────────────────────────────────────────────────────
    render_predictions_table(ticker, model_dict)