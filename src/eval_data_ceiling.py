"""Отвечает на вопрос «поможет ли больше данных».

Два независимых замера:

1. Потолок набора признаков. Оракул подгоняется на самих тестовых данных —
   лучше него на этих признаках не сделает никакая модель и никакой объём
   выборки. Разрыв между честной моделью и оракулом = всё, что ещё можно
   выиграть на текущих признаках.

2. Кривая обучения по компаниям. Если преимущество модели над медианой растёт
   с числом обучающих компаний — данные помогут. Если стоит на месте —
   упёрлись не в объём, а в состав признаков.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE = os.path.dirname(__file__)
FEATURES = ["canonical_work", "category", "region", "unit", "source"]
TRAIN_SIZES = [3, 6, 9, 12, 15, 18, 21]
SEED = 42


def load() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(BASE, "..", "data", "processed", "clean_prices.csv"))
    for col in ("unit", "region", "category"):
        df[col] = df[col].fillna("н/д")
    return df


def mape(true: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs((true - pred) / true)) * 100)


def build_model() -> Pipeline:
    return Pipeline([
        ("enc", ColumnTransformer([
            ("oh", OneHotEncoder(handle_unknown="ignore"), FEATURES),
        ])),
        ("lr", LinearRegression()),
    ])


def oracle_ceiling(df: pd.DataFrame) -> list[dict]:
    """Оракул: медиана внутри ячейки, посчитанная на тех же строках."""
    ladder = [
        ("глобальная медиана", []),
        ("вид работы", ["canonical_work"]),
        ("вид + город", ["canonical_work", "region"]),
        ("вид + город + единица", ["canonical_work", "region", "unit"]),
        ("вид + город + единица + компания",
         ["canonical_work", "region", "unit", "source"]),
    ]
    out = []
    y = df["price"].values
    for name, keys in ladder:
        if not keys:
            pred = np.full_like(y, float(np.median(y)), dtype=float)
            cells, per_cell = 1, len(df)
        else:
            pred = df.groupby(keys)["price"].transform("median").values
            cells = int(df.groupby(keys).ngroups)
            per_cell = float(df.groupby(keys).size().median())
        out.append({"features": name, "oracle_mape": round(mape(y, pred), 1),
                    "cells": cells, "median_rows_per_cell": per_cell})
    return out


def learning_curve(df: pd.DataFrame) -> list[dict]:
    """LOCO при разном числе обучающих компаний."""
    rng = np.random.default_rng(SEED)
    companies = sorted(df["source"].unique())
    rows = []

    for size in TRAIN_SIZES:
        model_errors, median_errors = [], []
        for held_out in companies:
            pool = [c for c in companies if c != held_out]
            if size > len(pool):
                continue
            # Несколько случайных подвыборок компаний — иначе результат
            # зависит от того, какие именно компании попали в обучение.
            for _ in range(5):
                chosen = rng.choice(pool, size=size, replace=False)
                train = df[df["source"].isin(chosen)]
                test = df[df["source"] == held_out]
                if len(train) < 50 or test.empty:
                    continue

                model = build_model()
                model.fit(train[FEATURES], np.log(train["price"]))
                pred = np.exp(model.predict(test[FEATURES]))
                model_errors.append(mape(test["price"].values, pred))

                work_median = train.groupby("canonical_work")["price"].median()
                fallback = float(train["price"].median())
                med_pred = test["canonical_work"].map(work_median).fillna(fallback)
                median_errors.append(mape(test["price"].values, med_pred.values))

        rows.append({
            "train_companies": size,
            "train_rows_median": int(df.groupby("source").size().median() * size),
            "model_mape": round(float(np.mean(model_errors)), 1),
            "median_mape": round(float(np.mean(median_errors)), 1),
            "gap_pp": round(float(np.mean(median_errors) - np.mean(model_errors)), 2),
        })
    return rows


def main() -> None:
    df = load()

    ceiling = oracle_ceiling(df)
    print("ПОТОЛОК НАБОРА ПРИЗНАКОВ — оракул подгоняется на самом тесте")
    print("-" * 78)
    for row in ceiling:
        print(f"{row['features']:34s} MAPE {row['oracle_mape']:5.1f}%   "
              f"ячеек {row['cells']:4d}, строк в ячейке {row['median_rows_per_cell']:.0f}")

    curve = learning_curve(df)
    print("\nКРИВАЯ ОБУЧЕНИЯ — LOCO при разном числе обучающих компаний")
    print("-" * 78)
    print(f"{'компаний':>9} {'строк~':>8} {'модель':>9} {'медиана':>9} {'разрыв':>9}")
    for row in curve:
        print(f"{row['train_companies']:>9} {row['train_rows_median']:>8} "
              f"{row['model_mape']:>8.1f}% {row['median_mape']:>8.1f}% "
              f"{row['gap_pp']:>+8.2f}")

    first, last = curve[0]["gap_pp"], curve[-1]["gap_pp"]
    verdict = (
        f"Разрыв модель-минус-медиана при {curve[0]['train_companies']} компаниях "
        f"{first:+.2f} п.п., при {curve[-1]['train_companies']} компаниях {last:+.2f} п.п. "
    )
    verdict += (
        "Преимущество не растёт с объёмом: узкое место не количество строк, "
        "а состав признаков."
        if last - first < 1.0 else
        "Преимущество растёт с объёмом: сбор данных окупается."
    )
    print("\n" + verdict)

    out = os.path.join(BASE, "..", "reports", "data_ceiling.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"oracle_ceiling": ceiling, "learning_curve": curve,
                   "verdict": verdict}, fh, ensure_ascii=False, indent=1)
    print(f"\nОтчёт: {os.path.relpath(out, BASE)}")


if __name__ == "__main__":
    main()
