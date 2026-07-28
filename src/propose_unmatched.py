"""Что классификатор предлагает для строк, которые регулярки не разобрали.

Ради этого всё и затевалось. Совпадение с регулярками там, где они и сами
справляются, продукту ничего не даёт: интерес представляют 2 326 названий,
на которых система сейчас молчит.

Скрипт обучается на всей regex-разметке и выдаёт предложения для непонятых
строк. Автоматически проверить их нельзя — эталона нет, поэтому выборка
уверенных предложений выгружается для ручной проверки.
"""

from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(__file__))
from clean_prices import to_canonical
from train_work_classifier import MIN_CLASS, ngram_model

BASE = os.path.dirname(__file__)
THRESHOLDS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
SAMPLE_PER_THRESHOLD = 40
SEED = 42


def main() -> None:
    raw = pd.read_csv(os.path.join(BASE, "..", "data", "real", "raw_prices.csv"))
    raw = raw.dropna(subset=["work_raw"])
    raw["work_raw"] = raw["work_raw"].astype(str).str.strip()
    raw = raw[raw["work_raw"].str.len() >= 4]
    raw["label"] = [to_canonical(n)[0] for n in raw["work_raw"]]
    raw = raw.drop_duplicates(subset=["work_raw"])

    labelled = raw.dropna(subset=["label"])
    unmatched = raw[raw["label"].isna()].copy()

    keep = labelled["label"].value_counts()
    keep = set(keep[keep >= MIN_CLASS].index)
    labelled = labelled[labelled["label"].isin(keep)]

    print(f"Обучающих названий: {len(labelled)}, классов: {len(keep)}")
    print(f"Непонятых названий: {len(unmatched)}\n")

    model = ngram_model()
    model.fit(labelled["work_raw"], labelled["label"])

    proba = model.predict_proba(unmatched["work_raw"])
    unmatched["proposal"] = model.classes_[proba.argmax(axis=1)]
    unmatched["confidence"] = proba.max(axis=1)

    print("СКОЛЬКО НЕПОНЯТЫХ СТРОК ПОЛУЧАЕТ ПРЕДЛОЖЕНИЕ")
    print("-" * 56)
    print(f"{'порог':>7} {'предложений':>13} {'доля непонятых':>16}")
    counts = {}
    for t in THRESHOLDS:
        n = int((unmatched["confidence"] >= t).sum())
        counts[str(t)] = {"n": n, "share": round(n / len(unmatched), 3)}
        print(f"{t:>7.1f} {n:>13} {n/len(unmatched)*100:>15.0f}%")

    rng = pd.Series(range(len(unmatched))).sample(frac=1.0, random_state=SEED)
    sample = (unmatched.iloc[rng.values]
              .query("confidence >= 0.6")
              .head(SAMPLE_PER_THRESHOLD * 2)
              .sort_values("confidence", ascending=False))

    out_csv = os.path.join(BASE, "..", "data", "processed", "unmatched_proposals.csv")
    sample[["work_raw", "proposal", "confidence", "source"]].to_csv(
        out_csv, index=False, encoding="utf-8-sig")

    print(f"\nВЫБОРКА ДЛЯ РУЧНОЙ ПРОВЕРКИ (confidence >= 0.6), {len(sample)} строк")
    print("-" * 96)
    for _, row in sample.iterrows():
        print(f"{row.confidence:.2f}  {row.work_raw[:62]:64s} -> {row.proposal}")

    out_json = os.path.join(BASE, "..", "reports", "unmatched_proposals.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"n_labelled": int(len(labelled)),
                   "n_unmatched": int(len(unmatched)),
                   "proposals_by_threshold": counts,
                   "sample_file": os.path.basename(out_csv)},
                  fh, ensure_ascii=False, indent=1)
    print(f"\nВыборка: {os.path.relpath(out_csv, BASE)}")


if __name__ == "__main__":
    main()
