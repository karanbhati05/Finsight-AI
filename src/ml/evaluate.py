# src/ml/evaluate.py

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
    log_loss,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def evaluate_model(model, X_test, y_test) -> dict:
    """
    Full evaluation suite for the binary price-direction classifier.

    Metrics computed and why each matters:

    accuracy:   % of correct predictions overall
                Misleading if classes are imbalanced — a model that
                always predicts "up" on a 55% up-day dataset gets 55%
                accuracy without learning anything

    f1:         harmonic mean of precision and recall
                Better than accuracy for imbalanced classes
                Balances: "when I predict up, am I right?" (precision)
                      and "do I catch all the up days?" (recall)

    precision:  of all days I predicted "up", how many were actually up?
                High precision = few false alarms

    recall:     of all actual "up" days, how many did I correctly identify?
                High recall = few missed opportunities

    roc_auc:    Area Under the ROC Curve
                Measures how well the model separates classes at all
                probability thresholds. 0.5 = random, 1.0 = perfect.
                More reliable than accuracy for financial prediction.

    log_loss:   measures calibration of probability estimates
                A well-calibrated model that says "70% chance up" should
                be right 70% of the time. Lower is better.

    Args:
        model:  fitted sklearn Pipeline
        X_test: test features DataFrame
        y_test: true labels Series

    Returns:
        Dict of metric name → value
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]   # probability of class 1 (up)

    metrics = {
        "accuracy":         round(accuracy_score(y_test,  y_pred),           4),
        "f1":               round(f1_score(y_test,        y_pred),            4),
        "precision":        round(precision_score(y_test, y_pred,
                                  zero_division=0),                            4),
        "recall":           round(recall_score(y_test,    y_pred,
                                  zero_division=0),                            4),
        "roc_auc":          round(roc_auc_score(y_test,   y_prob),            4),
        "log_loss":         round(log_loss(y_test,        y_prob),            4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "n_test_samples":   len(y_test),
        "positive_rate":    round(float(y_test.mean()),                       4),
    }

    # Print readable classification report to logs
    report = classification_report(
        y_test, y_pred,
        target_names = ["Down (0)", "Up (1)"],
        digits       = 3,
    )
    logger.info(f"\nClassification Report:\n{report}")

    # Confusion matrix breakdown for interpretability
    cm = metrics["confusion_matrix"]
    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
    logger.info(
        f"Confusion Matrix | "
        f"TN={tn} FP={fp} FN={fn} TP={tp} | "
        f"False Alarm Rate={fp/(fp+tn):.1%} | "
        f"Miss Rate={fn/(fn+tp):.1%}"
    )

    return metrics


def compute_sharpe_ratio(
    returns:        np.ndarray,
    risk_free_rate: float = 0.05,
    periods_per_year: int = 252,
) -> float:
    """
    Compute the annualized Sharpe Ratio for a returns series.

    Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns
    Annualized by multiplying by sqrt(periods_per_year)

    Why this matters for UBS:
        Any quant strategy is evaluated by its Sharpe ratio, not raw returns.
        A strategy returning 15% with Sharpe 0.5 is worse than one returning
        10% with Sharpe 1.5 — the second takes less risk per unit of return.

        Sharpe > 1.0  = good
        Sharpe > 2.0  = very good
        Sharpe > 3.0  = exceptional (rare in practice)

    Args:
        returns:          array of daily returns (e.g. [0.01, -0.005, 0.02])
        risk_free_rate:   annual risk-free rate (US 10Y treasury ~5% in 2024)
        periods_per_year: 252 trading days per year

    Returns:
        Annualized Sharpe ratio (float)
    """
    returns = np.array(returns)

    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    # Convert annual risk-free rate to daily
    daily_rf = risk_free_rate / periods_per_year

    excess_returns = returns - daily_rf
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)

    return round(float(sharpe), 4)


def simulate_strategy_returns(
    model,
    X_test:      pd.DataFrame,
    price_df:    pd.DataFrame,
    ticker:      str,
) -> dict:
    """
    Simulate a simple trading strategy based on model predictions.

    Strategy:
        - If model predicts "up" → go long (buy) → earn that day's return
        - If model predicts "down" → stay out → earn 0%
        - Compare against buy-and-hold baseline

    This converts model accuracy into financial performance,
    which is the metric UBS actually cares about.

    Args:
        model:    fitted sklearn Pipeline
        X_test:   test features
        price_df: price DataFrame with 'date', 'daily_return', 'ticker' cols
        ticker:   stock symbol for filtering price_df

    Returns:
        Dict with strategy_sharpe, buyhold_sharpe, strategy_returns,
        cumulative_return
    """
    predictions = model.predict(X_test)

    # Align predictions with price returns by index
    # X_test.index maps back to rows in the merged feature DataFrame
    test_indices = X_test.index

    # Filter price data for this ticker
    ticker_prices = price_df[price_df["ticker"] == ticker].copy()
    ticker_prices["date"] = pd.to_datetime(ticker_prices["date"], utc=True)
    ticker_prices = ticker_prices.sort_values("date").reset_index(drop=True)

    # Get daily returns for test period
    if "daily_return" not in ticker_prices.columns:
        logger.warning("daily_return column not found in price_df")
        return {}

    # Match returns to predictions (best effort by index length)
    n = min(len(predictions), len(ticker_prices))
    actual_returns = ticker_prices["daily_return"].values[-n:] / 100  # pct to decimal
    pred_labels    = predictions[-n:]

    # Strategy returns: only earn return on days model predicts "up"
    strategy_returns = np.where(pred_labels == 1, actual_returns, 0.0)

    # Buy-and-hold returns: always invested
    buyhold_returns = actual_returns

    # Compute Sharpe ratios
    strategy_sharpe = compute_sharpe_ratio(strategy_returns)
    buyhold_sharpe  = compute_sharpe_ratio(buyhold_returns)

    # Cumulative returns
    strategy_cumret = float((1 + strategy_returns).prod() - 1)
    buyhold_cumret  = float((1 + buyhold_returns).prod() - 1)

    results = {
        "strategy_sharpe":      strategy_sharpe,
        "buyhold_sharpe":       buyhold_sharpe,
        "strategy_cumret":      round(strategy_cumret, 4),
        "buyhold_cumret":       round(buyhold_cumret,  4),
        "n_trades":             int(pred_labels.sum()),
        "trade_rate":           round(float(pred_labels.mean()), 4),
    }

    logger.info(
        f"Strategy Simulation | "
        f"Strategy Sharpe: {strategy_sharpe:.3f} | "
        f"Buy&Hold Sharpe: {buyhold_sharpe:.3f} | "
        f"Strategy Return: {strategy_cumret:.1%} | "
        f"Buy&Hold Return: {buyhold_cumret:.1%} | "
        f"Trades: {results['n_trades']}/{n} days"
    )

    return results


def log_feature_importance(model, feature_cols: list[str]) -> dict:
    """
    Extract and log XGBoost feature importances.

    Feature importance tells you which signals the model
    actually used — critical for understanding and explaining
    the model to non-technical stakeholders at UBS.

    Uses 'gain' importance: the average loss reduction from
    splits on that feature. More meaningful than 'weight'
    (split count) because it accounts for how much each split
    actually improved predictions.

    Args:
        model:        fitted sklearn Pipeline with 'clf' step
        feature_cols: list of feature names in same order as X

    Returns:
        Dict mapping feature_name → importance_score (sorted descending)
    """
    clf = model.named_steps["clf"]

    if not hasattr(clf, "feature_importances_"):
        logger.warning("Model does not have feature_importances_ attribute")
        return {}

    importances = clf.feature_importances_

    importance_dict = dict(zip(feature_cols, importances))
    sorted_importance = dict(
        sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    )

    logger.info("Feature Importances (top 10):")
    for i, (feat, score) in enumerate(sorted_importance.items()):
        if i >= 10:
            break
        logger.info(f"  {i+1:2d}. {feat:<35} {score:.4f}")

    return sorted_importance