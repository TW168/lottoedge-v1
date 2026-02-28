"""Module 12: ML Engine — Random Forest + XGBoost ensemble. LSTM is optional."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import MinMaxScaler


def _build_features(df: pd.DataFrame, game: str, pool: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """
    Build supervised learning features for each number.
    For each draw i, create features from the prior window and labels from draw i.
    Features per draw:
        - freq in last 10, 20, 30 draws
        - skip since last appearance
        - positional average
    """
    from app.services.data_loader import get_main_numbers
    from app.services.frequency import _compute_skips

    df = get_main_numbers(df, game)
    draws = df["numbers"].tolist()
    n = len(draws)
    window = 30

    X_rows, y_rows = [], []

    for i in range(window, n):
        past = draws[max(0, i - window):i]
        target = draws[i]

        for num in pool:
            f10 = sum(1 for combo in past[-10:] if num in combo) / 10
            f20 = sum(1 for combo in past[-20:] if num in combo) / 20
            f30 = sum(1 for combo in past if num in combo) / window

            # Skip since last appearance
            appearances = [j for j, combo in enumerate(past) if num in combo]
            skip = (len(past) - appearances[-1]) if appearances else window

            label = 1 if num in target else 0
            X_rows.append([f10, f20, f30, skip / window])
            y_rows.append(label)

    X = np.array(X_rows, dtype=float)
    y = np.array(y_rows, dtype=int)
    return X, y


def train_ensemble(df: pd.DataFrame, game: str) -> dict:
    """
    Train RF + GBM ensemble. Returns trained model objects and scaler.
    Lightweight models suitable for batch scoring on CPU.
    """
    from app.services.frequency import _get_pool

    pool = _get_pool(game)
    X, y = _build_features(df, game, pool)

    if len(X) < 100:
        return {"trained": False, "reason": "Insufficient data (< 100 samples)"}

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Class balance
    pos = y.sum()
    neg = len(y) - pos
    ratio = neg / pos if pos > 0 else 1

    rf = RandomForestClassifier(
        n_estimators=100, max_depth=6, class_weight="balanced", random_state=42, n_jobs=-1
    )
    rf.fit(X_scaled, y)

    gbm = GradientBoostingClassifier(
        n_estimators=100, max_depth=4, random_state=42
    )
    gbm.fit(X_scaled, y)

    return {"trained": True, "rf": rf, "gbm": gbm, "scaler": scaler, "pool": pool}


def predict_scores(models: dict, df: pd.DataFrame, game: str) -> dict[int, float]:
    """
    Return a score (0–1) for each number in the pool using the ensemble.
    Higher = model thinks number is more likely to appear.
    """
    from app.services.frequency import _get_pool
    from app.services.data_loader import get_main_numbers

    if not models.get("trained"):
        # Fall back to uniform scores
        return {n: 0.5 for n in _get_pool(game)}

    df_main = get_main_numbers(df, game)
    draws = df_main["numbers"].tolist()
    pool = models["pool"]
    window = 30
    past = draws[-window:]

    features = []
    for num in pool:
        f10 = sum(1 for combo in past[-10:] if num in combo) / 10
        f20 = sum(1 for combo in past[-20:] if num in combo) / 20
        f30 = sum(1 for combo in past if num in combo) / window
        appearances = [j for j, combo in enumerate(past) if num in combo]
        skip = (len(past) - appearances[-1]) if appearances else window
        features.append([f10, f20, f30, skip / window])

    X = models["scaler"].transform(np.array(features, dtype=float))
    rf_probs = models["rf"].predict_proba(X)[:, 1]
    gbm_probs = models["gbm"].predict_proba(X)[:, 1]
    avg_probs = (rf_probs + gbm_probs) / 2

    return {num: round(float(p), 4) for num, p in zip(pool, avg_probs)}
