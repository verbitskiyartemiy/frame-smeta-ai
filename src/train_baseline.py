"""
Baseline-модель: предсказание справедливой цены за единицу работы.

ИДЕЯ
-----
Это "стартовая планка" — самая простая модель (линейная регрессия). Её задача —
дать ориентир, который в День 2 обгонит более умная модель (градиентный бустинг).

Модель учится: (вид работы, регион, класс ремонта) -> цена за единицу.

Для сравнения считаем ещё "глупую" модель (DummyRegressor), которая всегда
предсказывает среднюю цену. Если наша модель заметно точнее глупой — значит,
она реально уловила закономерности, а не притворяется.

МЕТРИКИ
-------
MAE  — средняя ошибка в рублях (насколько в среднем промахиваемся).
MAPE — средняя ошибка в процентах (промах относительно самой цены).
R2   — доля разброса цен, которую модель объясняет (1.0 — идеал, 0 — бесполезна).
"""

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

# Признаки (features) — то, ПО ЧЕМУ модель предсказывает цену.
CAT_FEATURES = ["work_name", "region", "quality_class", "unit"]
TARGET = "unit_price"  # что предсказываем


def evaluate(name: str, y_true, y_pred) -> dict:
    """Посчитать метрики и вернуть словарём."""
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

    # Делим данные: 80% на обучение, 20% на честную проверку (модель их не видит).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Обучающих строк: {len(X_train):,} | проверочных: {len(X_test):,}")

    # Категории (текст) превращаем в числа методом one-hot (по колонке на категорию).
    preprocess = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES)]
    )

    results = []

    # 1) "Глупая" модель — всегда средняя цена.
    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X_train, y_train)
    results.append(evaluate("Глупая (средняя цена)", y_test, dummy.predict(X_test)))

    # 2) Baseline — линейная регрессия.
    linreg = Pipeline([("prep", preprocess), ("model", LinearRegression())])
    linreg.fit(X_train, y_train)
    results.append(evaluate("Baseline (линейная регрессия)", y_test, linreg.predict(X_test)))

    res_df = pd.DataFrame(results).round(2)
    print("\n=== Результаты на проверочных данных ===")
    print(res_df.to_string(index=False))

    # Сохраняем отчёт.
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
