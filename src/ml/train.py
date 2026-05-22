# src/ml/train.py

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from src.ml.feature_engineering import build_feature_matrix, get_X_y
from src.ml.evaluate import evaluate_model, log_feature_importance
from src.utils.logger import get_logger
from src.utils.constants import MODELS_DIR

logger = get_logger(__name__)


def build_model_pipeline(class_weight_balanced: bool = False) -> Pipeline:
    """
    Build a scikit-learn Pipeline wrapping StandardScaler + XGBoost.

    Why a Pipeline instead of separate scaler and model?
        1. Prevents data leakage: the scaler fits ONLY on training data,
           then applies the same transformation to test data.
           If you fit the scaler on all data before splitting, your test
           set's scaling is informed by test data — that's leakage.
        2. Single object to save: pickle the pipeline and you get the
           fitted scaler AND the fitted model in one file.
        3. Predict() just works: pipeline.predict(X_new) auto-scales
           before passing to the model — no manual preprocessing needed.

    Why StandardScaler with XGBoost?
        XGBoost is tree-based and theoretically scale-invariant.
        But StandardScaler still helps because:
        - RSI is in range [0, 100]
        - sentiment_score is in range [-1, +1]
        - volume_change_pct can be [-50, +200]
        The scaler makes features comparable and improves convergence.

    Args:
        class_weight_balanced: if True, upweight minority class
                               use when target is imbalanced (>60% one class)

    Returns:
        Unfitted sklearn Pipeline
    """
    # Scale_pos_weight balances class weights in XGBoost
    # Set to ratio of negative/positive samples if imbalanced
    # We'll compute this dynamically in train() if needed
    xgb_params = dict(
        n_estimators      = 300,
        max_depth         = 4,        # shallow trees = less overfitting
        learning_rate     = 0.05,     # small steps = better generalization
        subsample         = 0.8,      # use 80% of rows per tree (row sampling)
        colsample_bytree  = 0.8,      # use 80% of features per tree
        min_child_weight  = 3,        # min samples in leaf = regularization
        gamma             = 0.1,      # min loss reduction to split = regularization
        random_state      = 42,
        eval_metric       = "logloss",
        use_label_encoder = False,
        verbosity         = 0,        # suppress XGBoost's own logging
    )

    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    XGBClassifier(**xgb_params)),
    ])


def train(
    df:        pd.DataFrame,
    ticker:    str = "model",
    save_dir:  str = MODELS_DIR,
) -> dict:
    """
    Full training pipeline:
        feature split → class balance check → cross-validation
        → final fit → evaluation → save

    Args:
        df:       feature matrix from build_feature_matrix()
        ticker:   used for the saved model filename
        save_dir: directory to save the .pkl file

    Returns:
        Dict with cv_scores, test_metrics, feature_importance, model_path
    """
    logger.info(f"Starting model training for {ticker}...")

    # ── Step 1: Split features and target ───────────────────────────────────
    X, y = get_X_y(df)
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")

    # ── Step 2: Train/test split ─────────────────────────────────────────────
    # stratify=y ensures both splits have the same class ratio
    # e.g. if 55% of all days are "up", both train and test will be ~55% "up"
    # Without stratify, random splits can create very different distributions
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size    = 0.2,
        random_state = 42,
        stratify     = y,
    )
    logger.info(
        f"Train: {len(X_train)} samples | Test: {len(X_test)} samples"
    )

    # ── Step 3: Check class balance ──────────────────────────────────────────
    train_pos_ratio = y_train.mean()
    scale_pos_weight = None

    if train_pos_ratio < 0.4 or train_pos_ratio > 0.6:
        # Imbalanced — compute scale_pos_weight for XGBoost
        # Formula: count(negative) / count(positive)
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        scale_pos_weight = n_neg / n_pos
        logger.warning(
            f"Class imbalance detected: {train_pos_ratio:.1%} positive. "
            f"Setting scale_pos_weight={scale_pos_weight:.2f}"
        )

    # ── Step 4: Build model pipeline ─────────────────────────────────────────
    model = build_model_pipeline()

    if scale_pos_weight is not None:
        # Access the XGBoost classifier inside the pipeline to set weight
        model.named_steps["clf"].set_params(scale_pos_weight=scale_pos_weight)

    # ── Step 5: Cross-validation ─────────────────────────────────────────────
    # StratifiedKFold preserves class ratio in each fold
    # 5 folds = each fold uses 80% train / 20% validation
    # This gives us 5 independent estimates of model performance
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    logger.info("Running 5-fold cross-validation...")
    cv_scores = cross_val_score(
        model, X_train, y_train,
        cv      = cv,
        scoring = "f1",        # F1 balances precision and recall
        n_jobs  = -1,          # use all CPU cores
    )

    logger.info(
        f"CV F1 scores: {cv_scores.round(3)} | "
        f"Mean: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}"
    )

    # ── Step 6: Final fit on all training data ───────────────────────────────
    # After CV told us the model generalizes, fit on full training set
    # to give the model as much data as possible before test evaluation
    logger.info("Fitting final model on full training set...")
    model.fit(X_train, y_train)

    # ── Step 7: Evaluate on held-out test set ────────────────────────────────
    # Test set was never seen during CV or final fit — true held-out evaluation
    test_metrics = evaluate_model(model, X_test, y_test)
    logger.info(f"Test metrics: {test_metrics}")

    # ── Step 8: Feature importance ───────────────────────────────────────────
    feature_cols     = X.columns.tolist()
    feature_importance = log_feature_importance(model, feature_cols)

    # ── Step 9: Save model ───────────────────────────────────────────────────
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    model_path = f"{save_dir}/{ticker}_xgb_model.pkl"

    with open(model_path, "wb") as f:
        pickle.dump({
            "model":            model,
            "feature_cols":     feature_cols,
            "ticker":           ticker,
            "cv_mean_f1":       float(cv_scores.mean()),
            "test_metrics":     test_metrics,
        }, f)

    logger.info(f"Model saved to {model_path}")

    return {
        "cv_scores":          cv_scores.tolist(),
        "cv_mean_f1":         float(cv_scores.mean()),
        "cv_std_f1":          float(cv_scores.std()),
        "test_metrics":       test_metrics,
        "feature_importance": feature_importance,
        "model_path":         model_path,
        "n_train":            len(X_train),
        "n_test":             len(X_test),
    }


def load_model(ticker: str, model_dir: str = MODELS_DIR) -> dict:
    """
    Load a saved model dict from disk.

    Returns:
        Dict with keys: model, feature_cols, ticker, cv_mean_f1, test_metrics
    """
    path = Path(model_dir) / f"{ticker}_xgb_model.pkl"

    if not path.exists():
        raise FileNotFoundError(
            f"No trained model found for {ticker} at {path}.\n"
            f"Run: python scripts/train_model.py --ticker {ticker}"
        )

    with open(path, "rb") as f:
        model_dict = pickle.load(f)

    logger.info(
        f"Model loaded for {ticker} | "
        f"CV F1: {model_dict['cv_mean_f1']:.3f}"
    )
    return model_dict