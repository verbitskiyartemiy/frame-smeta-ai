from __future__ import annotations
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

sys.path.append(os.path.dirname(__file__))
from absa import (analyze_review, get_aspect_matcher, get_neural_sentiment,
                  lexicon_sentiment, review_sentiment, split_clauses)

BASE = os.path.dirname(__file__)
RNG = np.random.default_rng(42)


def part_a_review_level(df):
    labeled = df[df["rating"].isin([1, 2, 5])].copy()
    labeled["y"] = (labeled["rating"] == 5).astype(int)
    print(f"Отзывов с меткой (1-2 = негатив, 5 = позитив): {len(labeled)}")
    print(f"  негативных: {(labeled['y']==0).sum()}, позитивных: {(labeled['y']==1).sum()}")

    texts = labeled["text"].tolist()
    neural = get_neural_sentiment()
    scores_n = []
    for i in range(0, len(texts), 32):
        batch = texts[i:i+32]
        clauses_flat, owners = [], []
        for j, t in enumerate(batch):
            cl = split_clauses(t) or [t[:250]]
            clauses_flat.extend(cl)
            owners.extend([j] * len(cl))
        cs = neural.score(clauses_flat)
        agg = {}
        for o, s in zip(owners, cs):
            agg.setdefault(o, []).append(s)
        scores_n.extend(float(np.mean(agg[j])) for j in range(len(batch)))
    scores_l = [review_sentiment(t, use_neural=False) for t in texts]

    y = labeled["y"].to_numpy()
    res = {}
    for name, sc in [("neural", scores_n), ("lexicon", scores_l)]:
        sc = np.asarray(sc)
        pred = (sc > 0).astype(int)
        res[name] = {
            "ROC_AUC": round(float(roc_auc_score(y, sc)), 3),
            "F1": round(float(f1_score(y, pred)), 3),
            "accuracy": round(float(accuracy_score(y, pred)), 3),
        }
        print(f"  {name:8} ROC-AUC={res[name]['ROC_AUC']}  F1={res[name]['F1']}  acc={res[name]['accuracy']}")
    return res, labeled


def part_b_aspects(df):
    matcher = get_aspect_matcher()
    neural = get_neural_sentiment()
    rows = []
    sample = df.sample(min(300, len(df)), random_state=42)
    for _, r in sample.iterrows():
        for clause in split_clauses(r["text"]):
            matches = matcher.match(clause)
            if not matches:
                continue
            senti = neural.score([clause])[0]
            rows.append({
                "clause": clause,
                "aspect_pred": matches[0][0],
                "aspect_sim": round(matches[0][1], 3),
                "sentiment_pred": round(senti, 3),
                "rating": r["rating"],
            })
    cl = pd.DataFrame(rows)
    print(f"\nКлауз с аспектами: {len(cl)} (из {len(sample)} отзывов)")
    print("Частоты аспектов:")
    print(cl["aspect_pred"].value_counts().to_string())

    gold = (cl.groupby("aspect_pred", group_keys=False)
            .apply(lambda g: g.sample(min(12, len(g)), random_state=42)))
    gold = gold.reset_index(drop=True)
    gold["aspect_true"] = ""
    gold["sentiment_true"] = ""
    out = os.path.abspath(os.path.join(BASE, "..", "data", "reviews", "gold_sample.csv"))
    gold.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nВыборка для gold-разметки ({len(gold)} клауз): {out}")
    return cl


def main():
    df = pd.read_csv(os.path.join(BASE, "..", "data", "reviews", "raw_reviews.csv"))
    print(f"Всего отзывов: {len(df)}")

    print("\n=== A. Валидация сентимента на реальных оценках авторов ===")
    res, _ = part_a_review_level(df)

    print("\n=== B. Аспектный разбор + выборка под gold-разметку ===")
    part_b_aspects(df)

    import json
    rep = os.path.abspath(os.path.join(BASE, "..", "reports"))
    os.makedirs(rep, exist_ok=True)
    with open(os.path.join(rep, "absa_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\nМетрики: reports/absa_metrics.json")


if __name__ == "__main__":
    main()
