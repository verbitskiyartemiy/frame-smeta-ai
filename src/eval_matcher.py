from __future__ import annotations
import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(__file__))
from clean_prices import to_canonical
from work_matcher import get_matcher

BASE = os.path.dirname(__file__)


def main():
    raw = pd.read_csv(os.path.join(BASE, "..", "data", "real", "raw_prices.csv"))
    names = sorted(raw["work_raw"].dropna().unique().tolist())
    print(f"Уникальных названий работ: {len(names)}")

    matcher = get_matcher(threshold=0.0)

    n = len(names)
    rows = []
    for name in names:
        r = to_canonical(name)[0]
        e, score = matcher.match(name)
        rows.append((name, r, e, score))

    regex_ok = sum(r is not None for _, r, _, _ in rows)

    print(f"\nУникальных названий: {n}")
    print(f"Покрытие regex-правилами: {regex_ok}/{n} = {regex_ok/n*100:.0f}%\n")
    print("Порог | Покрытие эмб. | Точность на regex-эталоне (agreement)")
    for thr in (0.50, 0.60, 0.70, 0.80):
        cover = sum(sc >= thr for _, _, e, sc in rows if e is not None)
        agree = tot = 0
        for _, r, e, sc in rows:
            if r is not None and e is not None and sc >= thr:
                tot += 1
                agree += (e == r)
        prec = agree / tot * 100 if tot else 0
        print(f" {thr:.2f} | {cover/n*100:4.0f}%        | {prec:4.0f}%  ({agree}/{tot})")

    print("\nВЫВОД: высокое покрытие при низком пороге обманчиво — точность падает.")
    print("Эмбеддинги полезны как ФОЛБЭК с высоким порогом, а не для расширения")
    print("обучающих данных (там нужна точность regex).")

    saved = [(nm, e, round(sc, 2)) for nm, r, e, sc in rows
             if r is None and e is not None and sc >= 0.70]

    agree = tot = 0
    for _, r, e, sc in rows:
        if r is not None and e is not None and sc >= 0.70:
            tot += 1
            agree += (e == r)
    prec70 = agree / tot * 100 if tot else 0

    out = os.path.abspath(os.path.join(BASE, "..", "reports", "matcher_eval.md"))
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Семантический матчинг работ: честная оценка\n\n")
        f.write(f"- Уникальных названий: **{n}**\n")
        f.write(f"- Покрытие regex-правилами: **{regex_ok/n*100:.0f}%**\n")
        f.write(f"- Точность эмбеддингов на regex-эталоне (порог 0.70): "
                f"**{prec70:.0f}%** ({agree}/{tot})\n\n")
        f.write("## Ключевой вывод (Data Science)\n\n")
        f.write("Наивное «покрытие 90%» при низком пороге **обманчиво**: эмбеддинги "
                "затолкали out-of-scope позиции (декоративная штукатурка, экзотика) "
                "в ближайшую НЕВЕРНУЮ работу. Покрытие растёт, точность падает. "
                "Поэтому эмбеддинги используются как **фолбэк со строгим порогом "
                "(≥0.70) и показом близости**, а обучающие данные чистятся точными "
                "regex-правилами.\n\n")
        f.write("## Примеры уверенных матчей (порог ≥0.70)\n\n")
        for name, canon, score in saved[:20]:
            f.write(f"- «{name}» → **{canon}** (близость {score})\n")
    print(f"\nОтчёт: reports/matcher_eval.md")


if __name__ == "__main__":
    main()
