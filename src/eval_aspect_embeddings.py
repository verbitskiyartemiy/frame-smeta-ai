from __future__ import annotations
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from absa import ASPECTS, split_clauses
from eval_gold import GOLD
from gigachat_embeddings import embed

BASE = os.path.dirname(__file__)
REV = os.path.join(BASE, "..", "data", "reviews")
OUT = os.path.abspath(os.path.join(BASE, "..", "reports", "aspect_embeddings.json"))
LABELS = list(ASPECTS)


def gold_clauses():
    df = pd.read_csv(os.path.join(REV, "gold_sample.csv"))
    n = min(len(df), len(GOLD))
    clauses = [str(c) for c in df["clause"].tolist()[:n]]
    labels = [g[0] for g in GOLD][:n]
    return clauses, labels


def anchor_matrix(vecs):
    labels, idx = [], []
    for aspect, phrases in ASPECTS.items():
        for _ in phrases:
            labels.append(aspect)
    return labels


def classify(clause_vecs, anchor_vecs, anchor_labels, threshold):
    preds = []
    for v in clause_vecs:
        sims = anchor_vecs @ v
        best = int(np.argmax(sims))
        preds.append(anchor_labels[best] if sims[best] >= threshold else "нет")
    return preds


def score(preds, gold_labels):
    aspectful = [(p, g) for p, g in zip(preds, gold_labels) if g != "нет"]
    on_aspectful = sum(p == g for p, g in aspectful) / len(aspectful) if aspectful else 0.0
    overall = sum(p == g for p, g in zip(preds, gold_labels)) / len(gold_labels)
    said_aspect = [(p, g) for p, g in zip(preds, gold_labels) if p != "нет"]
    precision = sum(p == g for p, g in said_aspect) / len(said_aspect) if said_aspect else 0.0
    return {"accuracy_on_aspectful": round(on_aspectful, 3),
            "overall_accuracy": round(overall, 3),
            "precision_when_assigned": round(precision, 3),
            "n_assigned": len(said_aspect)}


def main():
    clauses, gold_labels = gold_clauses()
    n_aspectful = sum(g != "нет" for g in gold_labels)

    phrases, anchor_labels = [], []
    for aspect, items in ASPECTS.items():
        for p in items:
            phrases.append(p)
            anchor_labels.append(aspect)

    print(f"Клауз в gold-наборе: {len(clauses)}, из них с аспектом: {n_aspectful}")
    print(f"Якорных фраз: {len(phrases)}, классов: {len(LABELS)}\n")

    print("Запрашиваю эмбеддинги GigaChat...")
    anchor_vecs = embed(phrases)
    clause_vecs = embed(clauses)

    results = {}
    print(f"\n{'порог':>6} {'на аспектных':>14} {'точность когда назначил':>25} {'назначено':>11}")
    best = None
    for thr in (0.0, 0.60, 0.65, 0.70, 0.75, 0.80):
        preds = classify(clause_vecs, anchor_vecs, anchor_labels, thr)
        s = score(preds, gold_labels)
        results[f"threshold_{thr}"] = s
        print(f"{thr:>6.2f} {s['accuracy_on_aspectful']:>14} "
              f"{s['precision_when_assigned']:>25} {s['n_assigned']:>11}")
        if best is None or s["accuracy_on_aspectful"] > best[1]["accuracy_on_aspectful"]:
            best = (thr, s)

    baseline = 0.513
    random_baseline = round(1 / len(LABELS), 3)
    gain = round(best[1]["accuracy_on_aspectful"] - baseline, 3)

    print(f"\nЛучший порог: {best[0]} -> accuracy на аспектных клаузах "
          f"{best[1]['accuracy_on_aspectful']}")
    print(f"MiniLM (прежний результат):  {baseline}")
    print(f"Случайный выбор из {len(LABELS)}:       {random_baseline}")
    print(f"Разница с MiniLM: {gain:+.3f}")

    verdict = ("GigaChat-эмбеддинги заметно лучше — имеет смысл заменить MiniLM"
               if gain >= 0.08 else
               "Выигрыш в пределах шума на выборке такого размера — "
               "замена не обоснована")
    print(f"\nВывод: {verdict}")

    out = {
        "task": "привязка клаузы отзыва к одному из 9 аспектов",
        "gold_set": {"n_clauses": len(clauses), "n_aspectful": n_aspectful,
                     "source": "yell.ru, разметка вручную (src/eval_gold.py)"},
        "n_classes": len(LABELS),
        "random_baseline": random_baseline,
        "minilm_previous": baseline,
        "gigachat_by_threshold": results,
        "gigachat_best": {"threshold": best[0], **best[1]},
        "gain_over_minilm": gain,
        "verdict": verdict,
        "caveat": "Gold-набор мал (около 100 клауз) и размечен автором. "
                  "Порог подобран на нём же, отдельного hold-out нет — "
                  "результат стоит читать как ориентир, а не как честную "
                  "оценку на новых данных.",
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nreports/aspect_embeddings.json")


if __name__ == "__main__":
    main()
