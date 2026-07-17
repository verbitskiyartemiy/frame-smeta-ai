"""
Обучение модели справедливой цены + детекция аномалий в смете.

Данные: data/processed/clean_prices.csv — РЕАЛЬНЫЕ цены из прайс-листов.

Что делаем:
1. Признаки: работа, категория, единица, регион (one-hot). Цель: log(цена).
   Лог-преобразование — потому что цены распределены мультипликативно
   (ошибка "в 2 раза" важнее ошибки "на 200 руб").
2. Два сценария валидации:
   a) random  — случайный сплит 80/20 (классическая проверка);
   b) company — отложены ЦЕЛЫЕ компании-источники (модель не видела их цен).
      Это честный тест на domain shift: как модель поведёт себя на прайсе
      новой компании.
3. Модели: baseline (линейная регрессия) vs градиентный бустинг (XGBoost).
   Метрики: MAE (руб), MAPE (%), R².
4. Детекция аномалий: квантильные модели P10/P90 дают "коридор справедливой
   цены". В тест подмешиваем синтетические завышения/занижения с метками
   и меряем ROC-AUC, precision, recall, confusion matrix.

Результаты: reports/metrics.json + reports/figures/*.png + models/*.joblib
"""
from __future__ import annotations
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (confusion_matrix, mean_absolute_error,
                             mean_absolute_percentage_error, r2_score,
                             roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

RNG = np.random.default_rng(42)
BASE = os.path.dirname(__file__)
# source = компания-источник: кодирует ценовой сегмент компании (премиум/эконом).
# Для новой компании (domain shift) признак неизвестен -> нулевой вектор, модель
# опирается на работу/регион. Это отражает реальный продукт: сегмент подрядчика
# на платформе известен из его профиля.
FEATURES = ["canonical_work", "category", "unit", "region", "source"]


def make_pipe(model):
    """Общий конвейер: one-hot кодирование категорий -> модель."""
    enc = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES),
    ])
    return Pipeline([("enc", enc), ("model", model)])


def evaluate(pipe, X_tr, y_tr, X_te, y_te) -> dict:
    """Обучить на train, посчитать метрики на test (цены в рублях)."""
    pipe.fit(X_tr, np.log(y_tr))
    pred = np.exp(pipe.predict(X_te))
    return {
        "MAE_rub": round(float(mean_absolute_error(y_te, pred)), 1),
        "MAPE_pct": round(float(mean_absolute_percentage_error(y_te, pred)) * 100, 1),
        "R2": round(float(r2_score(y_te, pred)), 3),
    }


def split_random(df, test_size=0.2):
    idx = RNG.permutation(len(df))
    n_test = int(len(df) * test_size)
    return df.iloc[idx[n_test:]], df.iloc[idx[:n_test]]


def split_by_company(df, n_holdout=2):
    """Отложить целые компании — тест на 'невиданный' прайс (domain shift)."""
    sources = df.groupby("source").size().sort_values()
    # Берём средние по размеру источники, чтобы тест был не микроскопическим.
    holdout = list(sources.index[len(sources)//2 - 1: len(sources)//2 - 1 + n_holdout])
    te = df[df["source"].isin(holdout)]
    tr = df[~df["source"].isin(holdout)]
    return tr, te, holdout


def empirical_corridor(df_tr):
    """Коридор справедливой цены P10-P90 из РЕАЛЬНЫХ цен.

    Для каждой работы берём эмпирические квантили обучающих цен (если
    наблюдений >= 5), иначе откатываемся к квантилям категории. Такой
    "справочник коридоров" устойчивее модельных квантилей на малых данных.
    """
    by_work = (df_tr.groupby("canonical_work")["price"]
               .agg(n="count", lo=lambda s: s.quantile(0.10),
                    hi=lambda s: s.quantile(0.90)))
    by_cat = (df_tr.groupby("category")["price"]
              .agg(lo=lambda s: s.quantile(0.10), hi=lambda s: s.quantile(0.90)))

    def corridor(row):
        w = by_work.loc[row["canonical_work"]] if row["canonical_work"] in by_work.index else None
        if w is not None and w["n"] >= 5:
            return w["lo"], w["hi"]
        c = by_cat.loc[row["category"]]
        return c["lo"], c["hi"]

    return corridor


def anomaly_eval(df_tr, df_te) -> dict:
    """Коридор P10-P90 (эмпирический) + подмешанные аномалии с метками."""
    corridor = empirical_corridor(df_tr)

    # Подмешиваем аномалии: 15% завышений (x1.6-3.0), 10% занижений (x0.3-0.6).
    te = df_te.copy().reset_index(drop=True)
    n = len(te)
    labels = np.zeros(n, dtype=int)
    prices = te["price"].to_numpy(dtype=float)
    k_hi = int(n * 0.15)
    k_lo = int(n * 0.10)
    pick = RNG.permutation(n)
    idx_hi, idx_lo = pick[:k_hi], pick[k_hi:k_hi + k_lo]
    prices[idx_hi] *= RNG.uniform(1.6, 3.0, size=k_hi)
    prices[idx_lo] *= RNG.uniform(0.3, 0.6, size=k_lo)
    labels[idx_hi] = 1
    labels[idx_lo] = 1

    bounds = te.apply(corridor, axis=1, result_type="expand")
    lo, hi = bounds[0].to_numpy(float), bounds[1].to_numpy(float)
    mid = np.sqrt(lo * hi)  # геометрическая середина коридора

    flags = ((prices < lo) | (prices > hi)).astype(int)     # решение "флаг/не флаг"
    # Скор аномальности, НОРМИРОВАННЫЙ на ширину коридора данной работы:
    # для работ с естественно широким разбросом цен отклонение "прощается",
    # для стабильных работ — то же отклонение даёт высокий скор.
    half_width = np.maximum(np.log(hi / lo) / 2, 1e-6)
    score = np.abs(np.log(prices / mid)) / half_width

    tn, fp, fn, tp = confusion_matrix(labels, flags).ravel()
    return {
        "n_test": int(n),
        "n_anomalies": int(k_hi + k_lo),
        "ROC_AUC": round(float(roc_auc_score(labels, score)), 3),
        "precision": round(float(tp / (tp + fp)) if tp + fp else 0.0, 3),
        "recall": round(float(tp / (tp + fn)) if tp + fn else 0.0, 3),
        "confusion": {"TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)},
    }


def main():
    df = pd.read_csv(os.path.join(BASE, "..", "data", "processed", "clean_prices.csv"))
    print(f"Обучающих данных: {len(df)} реальных цен, {df['canonical_work'].nunique()} работ\n")

    results = {"data": {"rows": len(df), "works": int(df['canonical_work'].nunique()),
                        "sources": int(df['source'].nunique())}}

    # --- Сценарий A: случайный сплит ---
    tr, te = split_random(df)
    for name, model in [("baseline_linear", LinearRegression()),
                        ("xgboost", XGBRegressor(n_estimators=200, max_depth=3,
                                                 learning_rate=0.08, subsample=0.9,
                                                 reg_lambda=2.0, random_state=42))]:
        m = evaluate(make_pipe(model), tr[FEATURES], tr["price"], te[FEATURES], te["price"])
        results[f"random_split/{name}"] = m
        print(f"[random ] {name:16} MAE={m['MAE_rub']:8} руб  MAPE={m['MAPE_pct']:5}%  R2={m['R2']}")

    # --- Сценарий B: отложенные компании (domain shift) ---
    tr_c, te_c, holdout = split_by_company(df)
    results["company_holdout/sources"] = holdout
    for name, model in [("baseline_linear", LinearRegression()),
                        ("xgboost", XGBRegressor(n_estimators=200, max_depth=3,
                                                 learning_rate=0.08, subsample=0.9,
                                                 reg_lambda=2.0, random_state=42))]:
        m = evaluate(make_pipe(model), tr_c[FEATURES], tr_c["price"], te_c[FEATURES], te_c["price"])
        results[f"company_holdout/{name}"] = m
        print(f"[company] {name:16} MAE={m['MAE_rub']:8} руб  MAPE={m['MAPE_pct']:5}%  R2={m['R2']}")

    # --- Детекция аномалий ---
    an = anomaly_eval(tr, te)
    results["anomaly_detection"] = an
    print(f"\n[anomaly] ROC-AUC={an['ROC_AUC']}  precision={an['precision']}  "
          f"recall={an['recall']}  (аномалий {an['n_anomalies']}/{an['n_test']})")
    print(f"          confusion: {an['confusion']}")

    # --- Сохранение финальной модели (на всех данных) и метрик ---
    final = make_pipe(XGBRegressor(n_estimators=200, max_depth=3,
                                   learning_rate=0.08, subsample=0.9,
                                   reg_lambda=2.0, random_state=42))
    final.fit(df[FEATURES], np.log(df["price"]))
    q_lo = make_pipe(GradientBoostingRegressor(loss="quantile", alpha=0.10, random_state=42))
    q_hi = make_pipe(GradientBoostingRegressor(loss="quantile", alpha=0.90, random_state=42))
    q_lo.fit(df[FEATURES], np.log(df["price"]))
    q_hi.fit(df[FEATURES], np.log(df["price"]))

    models_dir = os.path.abspath(os.path.join(BASE, "..", "models"))
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump({"price": final, "q_lo": q_lo, "q_hi": q_hi},
                os.path.join(models_dir, "frame_smeta_model.joblib"))

    rep_dir = os.path.abspath(os.path.join(BASE, "..", "reports"))
    os.makedirs(rep_dir, exist_ok=True)
    with open(os.path.join(rep_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nМодель: models/frame_smeta_model.joblib\nМетрики: reports/metrics.json")


if __name__ == "__main__":
    main()
