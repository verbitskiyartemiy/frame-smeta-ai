from __future__ import annotations
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from absa import get_neural_sentiment, lexicon_sentiment

BASE = os.path.dirname(__file__)

GOLD = [
    ("Коммуникация", 1), ("нет", 1), ("Вежливость", 1), ("нет", 1), ("нет", 1),
    ("нет", 0), ("нет", 1), ("нет", 0), ("нет", 1), ("нет", 1),
    ("Коммуникация", 0), ("нет", 1), ("нет", 1), ("Гарантия и недочёты", 1), ("нет", 1),
    ("Коммуникация", 1), ("Качество работ", 0), ("Цена и смета", 1), ("Качество работ", 1), ("Качество работ", 1),
    ("Качество работ", 1), ("нет", 0), ("Качество работ", 1), ("Качество работ", 1), ("нет", 1),
    ("Качество работ", 1), ("Гарантия и недочёты", 1), ("Качество работ", 1), ("Качество работ", 1), ("Профессионализм", 1),
    ("Качество работ", 1), ("нет", 1), ("Качество работ", 1), ("Цена и смета", 1), ("Сроки", 1),
    ("нет", 1), ("Качество работ", 1), ("нет", 0), ("нет", 0), ("Сроки", 1),
    ("Профессионализм", 1), ("нет", 0), ("Вежливость", 1), ("нет", 1), ("Коммуникация", 1),
    ("Профессионализм", 1), ("Коммуникация", 1), ("Качество работ", 1), ("Профессионализм", 1), ("нет", 0),
    ("Профессионализм", 1), ("нет", 1), ("Профессионализм", -1), ("Профессионализм", 1), ("Профессионализм", 1),
    ("нет", 1), ("нет", 0), ("Профессионализм", 1), ("Гарантия и недочёты", 1), ("нет", 1),
    ("Сроки", 1), ("Сроки", 1), ("Сроки", 1), ("Сроки", 0), ("нет", 1),
    ("Сроки", 1), ("Сроки", 1), ("Сроки", 1), ("Сроки", -1), ("Сроки", 1),
    ("Коммуникация", 1), ("Сроки", 1), ("Гарантия и недочёты", 1), ("Цена и смета", 1), ("нет", 0),
    ("Цена и смета", 1), ("Цена и смета", 1), ("Цена и смета", 1), ("Цена и смета", 1), ("Цена и смета", 1),
    ("Цена и смета", 1), ("Цена и смета", -1), ("нет", 0), ("Цена и смета", 1), ("нет", 1),
    ("Коммуникация", 1), ("Качество работ", 1), ("нет", 1), ("Цена и смета", 1), ("Честность", 1),
    ("Сроки", 1), ("Честность", 1), ("Коммуникация", 1), ("Коммуникация", 1), ("Профессионализм", 1),
    ("Качество работ", 1), ("нет", 0), ("нет", 1), ("Сроки", 1), ("Честность", 1),
    ("Чистота", 1), ("Качество работ", 1), ("нет", 0), ("Качество работ", 1), ("Профессионализм", 1),
    ("Чистота", 1), ("Сроки", 1), ("Чистота", 0),
]


def to_class(x, thr=0.15):
    return 1 if x > thr else (-1 if x < -thr else 0)


def main():
    df = pd.read_csv(os.path.join(BASE, "..", "data", "reviews", "gold_sample.csv"))
    assert len(df) == len(GOLD), f"{len(df)} vs {len(GOLD)}"
    df["aspect_true"] = [g[0] for g in GOLD]
    df["sentiment_true"] = [g[1] for g in GOLD]

    has_aspect = df["aspect_true"] != "нет"
    aspect_acc = float((df.loc[has_aspect, "aspect_pred"] == df.loc[has_aspect, "aspect_true"]).mean())
    false_attr = float((~has_aspect).mean())

    neural_scores = np.array(get_neural_sentiment().score(df["clause"].tolist()))
    df["sentiment_pred"] = neural_scores
    df["senti_neural_cls"] = [to_class(x) for x in neural_scores]
    df["senti_lex_cls"] = df["clause"].map(lambda c: to_class(lexicon_sentiment(c)))

    lab = df[df["sentiment_true"].isin([-1, 0, 1])]
    maj3 = lab["sentiment_true"].value_counts(normalize=True).max()
    acc_n = float((lab["senti_neural_cls"] == lab["sentiment_true"]).mean())
    acc_l = float((lab["senti_lex_cls"] == lab["sentiment_true"]).mean())

    pol = lab[lab["sentiment_true"] != 0]
    maj_pol = pol["sentiment_true"].value_counts(normalize=True).max()
    pol_n = float((np.sign(pol["sentiment_pred"]) == pol["sentiment_true"]).mean())
    pol_l = float((pol["senti_lex_cls"] == pol["sentiment_true"]).mean())
    n_pos = int((pol["sentiment_true"] == 1).sum())
    n_neg = int((pol["sentiment_true"] == -1).sum())

    neg = pol[pol["sentiment_true"] == -1]
    recall_neg_n = float((np.sign(neg["sentiment_pred"]) == -1).mean()) if len(neg) else None
    recall_neg_l = float((neg["senti_lex_cls"] == -1).mean()) if len(neg) else None

    res = {
        "n_gold": len(df),
        "aspect_accuracy_on_aspectful_9class": round(aspect_acc, 3),
        "aspect_random_baseline": round(1 / 9, 3),
        "share_clauses_without_true_aspect": round(false_attr, 3),
        "sentiment_3class": {"neural": round(acc_n, 3), "lexicon": round(acc_l, 3),
                             "majority_baseline": round(float(maj3), 3)},
        "sentiment_polarity": {"neural": round(pol_n, 3), "lexicon": round(pol_l, 3),
                               "majority_baseline": round(float(maj_pol), 3),
                               "n_pos": n_pos, "n_neg": n_neg},
        "negative_recall": {"neural": round(recall_neg_n, 3) if recall_neg_n is not None else None,
                            "lexicon": round(recall_neg_l, 3) if recall_neg_l is not None else None},
    }
    print(json.dumps(res, ensure_ascii=False, indent=2))

    out = os.path.join(BASE, "..", "data", "reviews", "gold_labeled.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    with open(os.path.join(BASE, "..", "reports", "absa_gold_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\nreports/absa_gold_metrics.json")


if __name__ == "__main__":
    main()
