"""Насколько хорош рыночный коридор — то, что реально показывается в продукте.

MAPE отвечает на вопрос «какая цена правильная». Продукт этот вопрос не задаёт:
он показывает диапазон и спрашивает «попадает ли ваша цена в рынок». Поэтому
и мерить надо другим:

- покрытие: какая доля честных рыночных цен попадает внутрь коридора;
- ложная тревога: сколько нормальных позиций мы зря пометим;
- ширина: насколько коридор узкий, то есть полезный;
- ловимость накрутки: с какого процента завышение выходит за границу.

Всё считается под leave-one-company-out: коридор строится на 21 компании,
проверяется на 22-й, которой пайплайн не видел.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(__file__)
MIN_SAMPLE = 5
INFLATIONS = (1.15, 1.25, 1.50, 2.00)


def corridors(train: pd.DataFrame) -> pd.DataFrame:
    grouped = train.groupby("canonical_work")["price"]
    table = grouped.agg(
        n="count",
        p10=lambda s: s.quantile(0.10),
        p50="median",
        p90=lambda s: s.quantile(0.90),
    )
    return table[table["n"] >= MIN_SAMPLE]


def main() -> None:
    df = pd.read_csv(os.path.join(BASE, "..", "data", "processed", "clean_prices.csv"))

    inside = below = above = 0
    widths: list[float] = []
    covered = skipped = 0
    caught = {f: [0, 0] for f in INFLATIONS}

    for company in sorted(df["source"].unique()):
        train = df[df["source"] != company]
        test = df[df["source"] == company]
        if len(test) < MIN_SAMPLE:
            continue

        table = corridors(train)
        joined = test.join(table, on="canonical_work")
        known = joined.dropna(subset=["p10"])
        skipped += len(joined) - len(known)
        covered += len(known)
        if known.empty:
            continue

        price = known["price"].to_numpy(float)
        lo = known["p10"].to_numpy(float)
        hi = known["p90"].to_numpy(float)
        mid = known["p50"].to_numpy(float)

        inside += int(((price >= lo) & (price <= hi)).sum())
        below += int((price < lo).sum())
        above += int((price > hi).sum())
        widths.extend(((hi - lo) / mid).tolist())

        # Накрутку считаем только на позициях, которые СЕЙЧАС в рынке:
        # иначе засчитаем себе те, что и без завышения были выше коридора.
        honest = (price >= lo) & (price <= hi)
        for factor in INFLATIONS:
            caught[factor][0] += int(honest.sum())
            caught[factor][1] += int((price[honest] * factor > hi[honest]).sum())

    total = inside + below + above
    result = {
        "n_evaluated": total,
        "n_abstained": skipped,
        "abstention_rate": round(skipped / (skipped + covered), 3),
        "coverage": round(inside / total, 3),
        "false_alarm_rate": round((below + above) / total, 3),
        "flagged_above": round(above / total, 3),
        "flagged_below": round(below / total, 3),
        "median_relative_width": round(float(np.median(widths)), 2),
        "inflation_recall": {
            f"+{int((f - 1) * 100)}%": round(c[1] / c[0], 3) if c[0] else None
            for f, c in caught.items()
        },
    }

    print("КАЧЕСТВО КОРИДОРА НА НЕВИДАННОЙ КОМПАНИИ (LOCO, 22 прогона)")
    print("-" * 62)
    print(f"позиций проверено                {total}")
    print(f"честный отказ (нет в справочнике) {result['abstention_rate']*100:.0f}%")
    print()
    print(f"попало внутрь коридора           {result['coverage']*100:.1f}%")
    print(f"  из них помечено выше рынка     {result['flagged_above']*100:.1f}%")
    print(f"  помечено ниже рынка            {result['flagged_below']*100:.1f}%")
    print(f"ложная тревога всего             {result['false_alarm_rate']*100:.1f}%")
    print()
    print(f"медианная ширина коридора        {result['median_relative_width']}x от медианы")
    print()
    print("какую накрутку коридор выводит за верхнюю границу:")
    for label, value in result["inflation_recall"].items():
        print(f"  {label:>6}   ловим {value*100:.0f}%")

    out = os.path.join(BASE, "..", "reports", "corridor_quality.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    print(f"\nОтчёт: {os.path.relpath(out, BASE)}")


if __name__ == "__main__":
    main()
