from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(__file__)

CANDIDATES = [
    "cointegrated/rubert-tiny-sentiment-balanced",
    "seara/rubert-tiny2-russian-sentiment",
    "blanchefort/rubert-base-cased-sentiment",
]


def score_texts(model_name, texts):
    from transformers import pipeline
    pipe = pipeline("text-classification", model=model_name, device=-1, top_k=None)
    out = []
    for res in pipe(texts, truncation=True, max_length=256, batch_size=16):
        d = {r["label"].lower(): r["score"] for r in res}
        out.append(d.get("positive", 0.0) - d.get("negative", 0.0))
    return np.array(out)


def to_class(x, thr=0.15):
    return np.where(x > thr, 1, np.where(x < -thr, -1, 0))


def main():
    df = pd.read_csv(os.path.join(BASE, "..", "data", "reviews", "gold_labeled.csv"))
    texts = df["clause"].tolist()
    y3 = df["sentiment_true"].to_numpy()
    polar_mask = y3 != 0

    results = {}
    for name in CANDIDATES:
        try:
            sc = score_texts(name, texts)
        except Exception as e:
            print(f"[SKIP] {name}: {type(e).__name__}: {str(e)[:80]}")
            continue
        cls = to_class(sc)
        acc3 = float((cls == y3).mean())
        pol = float((np.sign(sc[polar_mask]) == y3[polar_mask]).mean())
        results[name] = {"acc_3class": round(acc3, 3), "polarity_acc": round(pol, 3)}
        print(f"{name:45} acc3={acc3:.3f}  polarity={pol:.3f}")

    best = max(results, key=lambda k: results[k]["polarity_acc"])
    results["best"] = best
    print(f"\nЛучшая модель: {best}")
    with open(os.path.join(BASE, "..", "reports", "sentiment_model_selection.json"),
              "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
