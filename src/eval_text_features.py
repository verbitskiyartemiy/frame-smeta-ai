"""Объясняет ли текст позиции разброс цены внутри одного вида работ.

После нормализации исходное название отбрасывается, а в нём остаётся то, чего
нет ни в одном другом признаке: толщина слоя, тип смеси, число слоёв, каркас.
Гипотеза — эмбеддинг сырого названия объясняет часть разброса, который
справочник объяснить не может.

Проверка идёт под leave-one-company-out: на случайной разбивке выигрывает почти
что угодно, а продукт встречает смету от незнакомой компании.

Предобученная модель используется как экстрактор признаков, дообучения нет.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from scipy.sparse import hstack

sys.path.append(os.path.dirname(__file__))
from clean_prices import to_canonical

BASE = os.path.dirname(__file__)
CACHE = os.path.join(BASE, "..", "data", "processed", "name_embeddings.npz")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
CAT_FEATURES = ["canonical_work", "category", "region", "unit", "source"]
SVD_DIMS = 64
ALPHAS = (0.1, 1.0, 10.0, 100.0)


def build_dataset() -> pd.DataFrame:
    """Тот же пайплайн очистки, что в clean_prices, но сырое название сохраняется."""
    raw = pd.read_csv(os.path.join(BASE, "..", "data", "real", "raw_prices.csv"))
    canon = raw["work_raw"].map(to_canonical)
    raw["canonical_work"] = [c[0] for c in canon]
    raw["category"] = [c[1] for c in canon]
    raw["lo"] = [c[2] for c in canon]
    raw["hi"] = [c[3] for c in canon]

    matched = raw.dropna(subset=["canonical_work"])
    plausible = matched[(matched["price"] >= matched["lo"]) &
                        (matched["price"] <= matched["hi"])]

    def keep_inliers(g):
        q1, q3 = g["price"].quantile([0.25, 0.75])
        iqr = q3 - q1
        return g[(g["price"] >= q1 - 1.5 * iqr) & (g["price"] <= q3 + 1.5 * iqr)]

    clean = (plausible.groupby("canonical_work", group_keys=False)[plausible.columns]
             .apply(keep_inliers)).copy()
    clean = clean.rename(columns={"unit_raw": "unit"})
    for col in ("unit", "region", "category"):
        clean[col] = clean[col].fillna("н/д")
    return clean.reset_index(drop=True)


def embed_names(names: list[str]) -> np.ndarray:
    unique = sorted(set(names))
    if os.path.exists(CACHE):
        cached = np.load(CACHE, allow_pickle=True)
        if list(cached["names"]) == unique and str(cached["model"]) == MODEL_NAME:
            lookup = {n: v for n, v in zip(cached["names"], cached["vectors"])}
            return np.vstack([lookup[n] for n in names])

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    vectors = model.encode(unique, normalize_embeddings=True,
                           batch_size=64, show_progress_bar=False)
    np.savez_compressed(CACHE, names=np.array(unique, dtype=object),
                        vectors=vectors, model=MODEL_NAME)
    lookup = {n: v for n, v in zip(unique, vectors)}
    return np.vstack([lookup[n] for n in names])


def mape(true: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs((true - pred) / true)) * 100)


def r2(true: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((true - pred) ** 2))
    ss_tot = float(np.sum((true - np.mean(true)) ** 2))
    return 1.0 - ss_res / ss_tot


def onehot() -> ColumnTransformer:
    return ColumnTransformer([
        ("oh", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
    ])


def run_fold(train: pd.DataFrame, test: pd.DataFrame,
             emb_train: np.ndarray, emb_test: np.ndarray) -> dict:
    y_train = np.log(train["price"].values)
    y_true = test["price"].values

    work_median = train.groupby("canonical_work")["price"].median()
    fallback = float(train["price"].median())
    med_pred = test["canonical_work"].map(work_median).fillna(fallback).values

    cat_model = Pipeline([("enc", onehot()), ("ridge", RidgeCV(alphas=ALPHAS))])
    cat_model.fit(train[CAT_FEATURES], y_train)
    cat_pred = np.exp(cat_model.predict(test[CAT_FEATURES]))

    # SVD обучается только на train — иначе тестовая компания влияет на базис.
    svd = TruncatedSVD(n_components=min(SVD_DIMS, emb_train.shape[1] - 1),
                       random_state=42)
    tr_svd = svd.fit_transform(emb_train)
    te_svd = svd.transform(emb_test)

    enc = onehot()
    tr_cat = enc.fit_transform(train[CAT_FEATURES])
    te_cat = enc.transform(test[CAT_FEATURES])
    tr_cat = tr_cat.toarray() if hasattr(tr_cat, "toarray") else tr_cat
    te_cat = te_cat.toarray() if hasattr(te_cat, "toarray") else te_cat

    both = RidgeCV(alphas=ALPHAS)
    both.fit(np.hstack([tr_cat, tr_svd]), y_train)
    both_pred = np.exp(both.predict(np.hstack([te_cat, te_svd])))

    text_only = Ridge(alpha=1.0)
    text_only.fit(tr_svd, y_train)
    text_pred = np.exp(text_only.predict(te_svd))

    # Символьные n-граммы: ловят «до 5 см», «2 слоя», «цементн» — то,
    # что плотные эмбеддинги смазывают.
    tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                            min_df=3, sublinear_tf=True)
    tr_tf = tfidf.fit_transform(train["work_raw"])
    te_tf = tfidf.transform(test["work_raw"])

    ngram = RidgeCV(alphas=ALPHAS)
    ngram.fit(hstack([tr_cat, tr_tf]).tocsr(), y_train)
    ngram_pred = np.exp(ngram.predict(hstack([te_cat, te_tf]).tocsr()))

    return {
        "median_by_work": (mape(y_true, med_pred), r2(y_true, med_pred)),
        "categorical": (mape(y_true, cat_pred), r2(y_true, cat_pred)),
        "text_only_embeddings": (mape(y_true, text_pred), r2(y_true, text_pred)),
        "categorical_plus_embeddings": (mape(y_true, both_pred), r2(y_true, both_pred)),
        "categorical_plus_char_ngrams": (mape(y_true, ngram_pred), r2(y_true, ngram_pred)),
    }


def main() -> None:
    df = build_dataset()
    print(f"Строк: {len(df)}, видов работ: {df.canonical_work.nunique()}, "
          f"компаний: {df.source.nunique()}, уникальных названий: {df.work_raw.nunique()}")
    print(f"Эмбеддинги: {MODEL_NAME}")

    emb = embed_names(df["work_raw"].tolist())
    print(f"Размерность эмбеддинга: {emb.shape[1]} -> SVD {SVD_DIMS}\n")

    methods = ["median_by_work", "categorical", "text_only_embeddings",
               "categorical_plus_embeddings", "categorical_plus_char_ngrams"]
    acc = {m: {"mape": [], "r2": []} for m in methods}

    for company in sorted(df["source"].unique()):
        test_mask = (df["source"] == company).values
        train, test = df[~test_mask], df[test_mask]
        if len(test) < 5:
            continue
        fold = run_fold(train, test, emb[~test_mask], emb[test_mask])
        for name, (m, r) in fold.items():
            acc[name]["mape"].append(m)
            acc[name]["r2"].append(r)

    print("LEAVE-ONE-COMPANY-OUT, 22 компании")
    print("-" * 66)
    print(f"{'Метод':32s} {'MAPE, %':>16s} {'R²':>12s}")
    result = {}
    for name in methods:
        m = np.mean(acc[name]["mape"]); s = np.std(acc[name]["mape"])
        r = np.mean(acc[name]["r2"])
        result[name] = {"MAPE": [round(float(m), 1), round(float(s), 1)],
                        "R2": round(float(r), 3), "n_folds": len(acc[name]["mape"])}
        print(f"{name:32s} {m:9.1f} ± {s:4.1f} {r:12.3f}")

    base = result["median_by_work"]["MAPE"][0]
    best_text = min(result["categorical_plus_embeddings"]["MAPE"][0],
                    result["categorical_plus_char_ngrams"]["MAPE"][0])
    gain = round(base - best_text, 2)
    verdict = (
        f"Текстовые признаки дают {gain:+.2f} п.п. MAPE против медианы по виду работы "
        f"при межфолдовом разбросе {result['median_by_work']['MAPE'][1]} п.п. "
    )
    verdict += ("Выигрыш больше разброса — текст несёт сигнал, которого нет в справочнике."
                if gain > result["median_by_work"]["MAPE"][1]
                else "Выигрыш не превышает разброс между компаниями — сигнала недостаточно.")
    print("\n" + verdict)

    out = os.path.join(BASE, "..", "reports", "text_features.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"model": MODEL_NAME, "svd_dims": SVD_DIMS,
                   "n_rows": int(len(df)), "results": result,
                   "verdict": verdict}, fh, ensure_ascii=False, indent=1)
    print(f"Отчёт: {os.path.relpath(out, BASE)}")


if __name__ == "__main__":
    main()
