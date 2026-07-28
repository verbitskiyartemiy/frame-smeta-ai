"""Классификатор названий работ: замена regex-нормализации с явным отказом.

Регулярки понимают только то, что в них вписали руками, и не обобщаются на
новые формулировки. Классификатор учится на строках, которые регулярки уже
разобрали, и должен покрыть те, которые они пропускают.

Прошлая попытка (work_matcher.py) провалилась по двум причинам: класс задавался
тремя фразами-якорями вместо реальных примеров, и не было способа ответить
«не знаю» — любая строка проваливалась в ближайший класс. Здесь исправлено
и то, и другое.

Оценка идёт по компаниям: обучаемся на 21 компании, проверяем на 22-й.
Это отвечает на вопрос «поймёт ли модель формулировки подрядчика, которого
она не видела», а не «запомнила ли она обучающую выборку».
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

sys.path.append(os.path.dirname(__file__))
from clean_prices import to_canonical

BASE = os.path.dirname(__file__)
EMB_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMB_CACHE = os.path.join(BASE, "..", "data", "processed", "classifier_embeddings.npz")
THRESHOLDS = (0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
MIN_CLASS = 3


def load_names() -> pd.DataFrame:
    raw = pd.read_csv(os.path.join(BASE, "..", "data", "real", "raw_prices.csv"))
    raw = raw.dropna(subset=["work_raw"])
    raw["work_raw"] = raw["work_raw"].astype(str).str.strip()
    raw = raw[raw["work_raw"].str.len() >= 4]
    raw["label"] = [to_canonical(n)[0] for n in raw["work_raw"]]
    # Одна строка на пару «название + компания»: иначе частые позиции
    # перевешивают редкие просто за счёт повторов в прайсе.
    return raw.drop_duplicates(subset=["work_raw", "source"])[
        ["work_raw", "source", "label"]].reset_index(drop=True)


def embed(texts: list[str]) -> np.ndarray:
    unique = sorted(set(texts))
    if os.path.exists(EMB_CACHE):
        cached = np.load(EMB_CACHE, allow_pickle=True)
        if list(cached["names"]) == unique:
            lookup = dict(zip(cached["names"], cached["vectors"]))
            return np.vstack([lookup[t] for t in texts])

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMB_MODEL)
    vectors = model.encode(unique, normalize_embeddings=True, batch_size=64)
    np.savez_compressed(EMB_CACHE, names=np.array(unique, dtype=object),
                        vectors=vectors)
    lookup = dict(zip(unique, vectors))
    return np.vstack([lookup[t] for t in texts])


def ngram_model() -> Pipeline:
    # Признаковое пространство ограничено осознанно: на 4 тысячах строк
    # символьные n-граммы от 2 до 5 при min_df=2 дают десятки тысяч признаков,
    # решатель на них не сходится за разумное время и выигрыша это не даёт.
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4),
                                  min_df=3, max_features=20000,
                                  sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=200, C=1.0,
                                   class_weight="balanced")),
    ])


def evaluate_by_company(labelled: pd.DataFrame, emb: np.ndarray) -> dict:
    """Обучаемся на всех компаниях кроме одной, проверяем на ней."""
    companies = sorted(labelled["source"].unique())
    rows = {"ngram": [], "embeddings": []}

    print(f"{'компания':28s} {'строк':>6} {'n-граммы@0.7':>13} {'эмбеддинги@0.7':>15}",
          flush=True)
    for held_out in companies:
        test_mask = (labelled["source"] == held_out).values
        train, test = labelled[~test_mask], labelled[test_mask]
        if len(test) < 20 or train["label"].nunique() < 10:
            continue

        keep = train["label"].value_counts()
        keep = set(keep[keep >= MIN_CLASS].index)
        train = train[train["label"].isin(keep)]
        test_known = test[test["label"].isin(keep)]
        if test_known.empty:
            continue

        ngram = ngram_model()
        ngram.fit(train["work_raw"], train["label"])
        proba = ngram.predict_proba(test_known["work_raw"])
        ngram_fold = _score(proba, ngram.classes_, test_known["label"].values)
        rows["ngram"].append(ngram_fold)

        # labelled переиндексирован с нуля, поэтому позиции строк совпадают
        # со строками матрицы эмбеддингов.
        emb_clf = LogisticRegression(max_iter=400, C=1.0, class_weight="balanced")
        emb_clf.fit(emb[train.index], train["label"])
        proba_e = emb_clf.predict_proba(emb[test_known.index])
        emb_fold = _score(proba_e, emb_clf.classes_, test_known["label"].values)
        rows["embeddings"].append(emb_fold)

        def brief(fold):
            cell = fold[0.7]
            if not cell["n_answered"]:
                return "  молчит"
            return (f"{cell['n_correct']/cell['n_answered']*100:>3.0f}%"
                    f" @{cell['n_answered']/cell['n_total']*100:>3.0f}%")
        print(f"{held_out[:27]:28s} {len(test_known):>6}   "
              f"{brief(ngram_fold):>12} {brief(emb_fold):>14}", flush=True)

    out = {}
    for name, folds in rows.items():
        out[name] = {}
        for t in THRESHOLDS:
            total = sum(f[t]["n_total"] for f in folds)
            answered = sum(f[t]["n_answered"] for f in folds)
            correct = sum(f[t]["n_correct"] for f in folds)
            out[name][str(t)] = {
                "coverage": round(answered / total, 3) if total else 0.0,
                "accuracy": round(correct / answered, 3) if answered else None,
                "n_answered": answered,
                "n_total": total,
            }
        out[name]["n_folds"] = len(folds)
    return out


def _score(proba: np.ndarray, classes: np.ndarray, truth: np.ndarray) -> dict:
    """Возвращает счётчики, а не доли.

    Усреднять точность по фолдам нельзя: фолд, где модель промолчала на всех
    строках, вносил бы в среднее ноль и занижал точность на высоких порогах.
    Правильная величина — микро-среднее по всем выданным ответам сразу.
    """
    best_idx = proba.argmax(axis=1)
    best_p = proba.max(axis=1)
    pred = classes[best_idx]
    result = {}
    for t in THRESHOLDS:
        answered = best_p >= t
        result[t] = {
            "n_total": int(len(truth)),
            "n_answered": int(answered.sum()),
            "n_correct": int((pred[answered] == truth[answered]).sum()),
        }
    return result


def main() -> None:
    df = load_names()
    labelled = df.dropna(subset=["label"]).reset_index(drop=True)
    unlabelled = df[df["label"].isna()].reset_index(drop=True)

    print(f"Всего пар «название + компания»: {len(df)}")
    print(f"Разобрано регулярками:           {len(labelled)} "
          f"({len(labelled)/len(df)*100:.0f}%)")
    print(f"Регулярки не поняли:             {len(unlabelled)} "
          f"({len(unlabelled)/len(df)*100:.0f}%)")
    print(f"Классов в разметке:              {labelled['label'].nunique()}\n")

    emb = embed(labelled["work_raw"].tolist())
    metrics = evaluate_by_company(labelled, emb)

    print("ПРОВЕРКА НА НЕВИДАННОЙ КОМПАНИИ — совпадение с regex-разметкой")
    print("-" * 68)
    for name in ("ngram", "embeddings"):
        print(f"\n{name}  (фолдов: {metrics[name]['n_folds']})")
        print(f"{'порог':>7} {'отвечает':>10} {'точность':>10}")
        for t in THRESHOLDS:
            row = metrics[name][str(t)]
            acc = f"{row['accuracy']*100:>8.0f}%" if row['accuracy'] is not None else "       —"
            print(f"{t:>7.1f} {row['coverage']*100:>9.0f}% {acc} "
                  f"  ({row['n_answered']} из {row['n_total']})")

    out = os.path.join(BASE, "..", "reports", "work_classifier.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"embedding_model": EMB_MODEL,
                   "n_pairs": int(len(df)),
                   "n_labelled": int(len(labelled)),
                   "n_unlabelled": int(len(unlabelled)),
                   "by_company": metrics}, fh, ensure_ascii=False, indent=1)
    print(f"\nОтчёт: {os.path.relpath(out, BASE)}")


if __name__ == "__main__":
    main()
