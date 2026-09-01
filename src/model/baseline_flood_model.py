from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "data" / "processed" / "master_daily_grid_splits.parquet"


def build_model_columns(df: pd.DataFrame) -> list[str]:
    exclude = {
        "GaugeID",
        "Date",
        "Station",
        "River_Name",
        "Basin",
        "State",
        "Privacy",
        "split",
        "target_onset",
        "target_active",
        "target_peak",
    }
    feature_cols = [c for c in df.columns if c not in exclude]

    usable_cols = []
    for col in feature_cols:
        series = df[col]
        if series.isna().all():
            continue
        if series.dropna().nunique() <= 1:
            continue
        usable_cols.append(col)

    return usable_cols


def main() -> None:
    df = pd.read_parquet(DATASET_PATH)
    feature_cols = build_model_columns(df)
    X_train = df[df["split"] == "train"][feature_cols]
    X_val = df[df["split"] == "val"][feature_cols]
    X_test = df[df["split"] == "test"][feature_cols]

    y_train = (df[df["split"] == "train"]["target_onset"] > 0).astype(int)
    y_val = (df[df["split"] == "val"]["target_onset"] > 0).astype(int)
    y_test = (df[df["split"] == "test"]["target_onset"] > 0).astype(int)

    numeric_cols = list(X_train.select_dtypes(include=["number"]).columns)
    categorical_cols = [c for c in X_train.columns if c not in numeric_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_cols,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced_subsample",
                    random_state=42,
                    min_samples_leaf=5,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    for split_name, X_split, y_split in [("train", X_train, y_train), ("val", X_val, y_val), ("test", X_test, y_test)]:
        pred = model.predict(X_split)
        proba = model.predict_proba(X_split)[:, 1]
        print(
            split_name,
            "rows",
            len(X_split),
            "pos",
            int(y_split.sum()),
            "pred_pos",
            int(pred.sum()),
        )
        print(
            "  f1",
            round(f1_score(y_split, pred, zero_division=0), 4),
            "precision",
            round(precision_score(y_split, pred, zero_division=0), 4),
            "recall",
            round(recall_score(y_split, pred, zero_division=0), 4),
            "roc_auc",
            round(roc_auc_score(y_split, proba), 4),
        )

    print("feature_count", len(feature_cols))


if __name__ == "__main__":
    main()
