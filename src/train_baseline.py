from __future__ import annotations

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
)

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.abspath(os.path.join(HERE, "..", "data", "raw", "smeta_dataset.csv"))
REPORT_PATH = os.path.abspath(os.path.join(HERE, "..", "reports", "baseline_metrics.md"))

CAT_FEATURES = ["work_name", "region", "quality_class", "unit"]
TARGET = "unit_price"


def evaluate(name: str, y_true, y_pred) -> dict:
    return {
        "model": name,
        "MAE_руб": mean_absolute_error(y_true, y_pred),
        "MAPE_%": mean_absolute_percentage_error(y_true, y_pred) * 100,
        "R2": r2_score(y_true, y_pred),
    }


def main():
    df = pd.read_csv(DATA_PATH)

    X = df[CAT_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Обучающих строк: {len(X_train):,} | проверочных: {len(X_test):,}")

    preprocess = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES)]
    )

    results = []

    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X_train, y_train)
    results.append(evaluate("Глупая (средняя цена)", y_test, dummy.predict(X_test)))

    linreg = Pipeline([("prep", preprocess), ("model", LinearRegression())])
    linreg.fit(X_train, y_train)
    results.append(evaluate("Baseline (линейная регрессия)", y_test, linreg.predict(X_test)))

    res_df = pd.DataFrame(results).round(2)
    print("\n=== Результаты на проверочных данных ===")
    print(res_df.to_string(index=False))

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Baseline — метрики\n\n")
        f.write("Предсказание справедливой цены за единицу работы. "
                "Проверка на отложенных 20% данных.\n\n")
        f.write(res_df.to_markdown(index=False))
        f.write("\n\n**Как читать:** MAE — средняя ошибка в рублях, "
                "MAPE — в процентах, R² — доля объяснённого разброса (ближе к 1 — лучше).\n")
    print(f"\nОтчёт сохранён: reports/baseline_metrics.md")


if __name__ == "__main__":
    main()
