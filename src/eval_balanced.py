from __future__ import annotations
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, f1_score, recall_score,
                             roc_auc_score)

sys.path.append(os.path.dirname(__file__))
from absa import get_neural_sentiment, review_sentiment

BASE = os.path.dirname(__file__)
REV = os.path.join(BASE, "..", "data", "reviews")
RNG = np.random.default_rng(42)


def load_balanced():
    src = pd.read_csv(os.path.join(REV, "otzyvru_reviews.csv"))
    pos = src[src["rating"] >= 4.5][["text"]].assign(y=1)
    neg = src[src["rating"] <= 2.0][["text"]].assign(y=0)
    print(f"Один источник (otzyvru): позитив 5* = {len(pos)}, негатив 1-2* = {len(neg)}")
    n = min(len(pos), len(neg))
    pos = pos.sample(n, random_state=42)
    neg = neg.sample(n, random_state=42)
    df = pd.concat([pos, neg]).sample(frac=1, random_state=42).reset_index(drop=True)
    df["text"] = df["text"].str.slice(0, 600)
    return df


def neural_scores(texts):
    ns = get_neural_sentiment()
    return np.array(ns.score(texts))


def main():
    df = load_balanced()
    y = df["y"].to_numpy()
    print(f"Сбалансированный набор: {len(df)} ({y.sum()} поз / {(1-y).sum():.0f} нег)")

    sc_n = neural_scores(df["text"].tolist())
    sc_l = np.array([review_sentiment(t, use_neural=False) for t in df["text"]])
    maj = max(y.mean(), 1 - y.mean())

    res = {"n": int(len(df)), "n_pos": int(y.sum()), "n_neg": int((1 - y).sum()),
           "majority_baseline_acc": round(float(maj), 3)}
    for name, sc in [("neural", sc_n), ("lexicon", sc_l)]:
        pred = (sc > 0).astype(int)
        res[name] = {
            "ROC_AUC": round(float(roc_auc_score(y, sc)), 3),
            "F1_macro": round(float(f1_score(y, pred, average="macro")), 3),
            "accuracy": round(float(accuracy_score(y, pred)), 3),
            "recall_neg": round(float(recall_score(y, pred, pos_label=0)), 3),
            "recall_pos": round(float(recall_score(y, pred, pos_label=1)), 3),
        }
        print(f"  {name:8} ROC-AUC={res[name]['ROC_AUC']}  F1={res[name]['F1_macro']}  "
              f"acc={res[name]['accuracy']}  recall_neg={res[name]['recall_neg']}")
    print(f"  majority baseline acc = {res['majority_baseline_acc']}")

    with open(os.path.join(BASE, "..", "reports", "absa_balanced_metrics.json"),
              "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\nreports/absa_balanced_metrics.json")


if __name__ == "__main__":
    main()
