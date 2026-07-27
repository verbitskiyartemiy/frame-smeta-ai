from __future__ import annotations

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.abspath(os.path.join(HERE, "..", "data", "processed", "clean_prices.csv"))
FIG_DIR = os.path.abspath(os.path.join(HERE, "..", "reports", "figures"))
REPORT_PATH = os.path.abspath(os.path.join(HERE, "..", "reports", "eda_summary.md"))
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 120,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
BLUE = "#2f6db0"
ORANGE = "#c65b2f"
GREEN = "#2e9e6b"
MIN_SAMPLE = 5


def save(fig, name: str):
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  сохранён график: reports/figures/{name}")


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Загружено: {len(df)} цен, {df['canonical_work'].nunique()} работ, "
          f"{df['source'].nunique()} компаний, {df['region'].nunique()} городов")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.hist(df["price"], bins=60, color=BLUE, alpha=0.85)
    a1.set_title("Цена за единицу — в рублях")
    a1.set_xlabel("₽")
    a1.set_ylabel("Количество позиций")
    a2.hist(np.log10(df["price"]), bins=60, color=GREEN, alpha=0.85)
    a2.set_title("Та же цена в логарифме — почти симметрична")
    a2.set_xlabel("log10(₽)")
    fig.suptitle("Цены логнормальны: это обоснование обучения на log(price)", y=1.03)
    save(fig, "01_price_distribution.png")

    order = df.groupby("region")["price"].median().sort_values().index
    data = [df.loc[df["region"] == r, "price"].to_numpy() for r in order]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bp = ax.boxplot(data, tick_labels=list(order), showfliers=False,
                    patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor(BLUE)
        patch.set_alpha(0.55)
    ax.set_title("Разброс цен по городам")
    ax.set_ylabel("Цена за единицу, ₽")
    ax.tick_params(axis="x", rotation=25)
    save(fig, "02_price_by_region.png")

    by_cat = df.groupby("category")["price"].median().sort_values()
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.barh(by_cat.index, by_cat.values, color=ORANGE, alpha=0.9)
    for i, v in enumerate(by_cat.values):
        ax.text(v, i, f" {v:,.0f}", va="center", fontsize=9)
    ax.set_title("Медианная цена по категориям работ")
    ax.set_xlabel("₽ за единицу")
    save(fig, "03_price_by_category.png")

    g = df.groupby("canonical_work")["price"]
    spread = (g.quantile(0.90) / g.quantile(0.10)).dropna()
    spread = spread[g.count() >= MIN_SAMPLE].sort_values()
    top = pd.concat([spread.head(7), spread.tail(7)])
    fig, ax = plt.subplots(figsize=(8, 5.5))
    colors = [GREEN if v < spread.median() else ORANGE for v in top.values]
    ax.barh(top.index, top.values, color=colors, alpha=0.9)
    ax.axvline(1.0, color="#888", lw=1)
    for i, v in enumerate(top.values):
        ax.text(v, i, f" ×{v:.1f}", va="center", fontsize=9)
    ax.set_title("Во сколько раз P90 дороже P10 — где рынок непрозрачен")
    ax.set_xlabel("Отношение P90 / P10")
    save(fig, "04_price_spread_by_work.png")

    counts = df["canonical_work"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = [ORANGE if c < MIN_SAMPLE else BLUE for c in counts.values]
    ax.barh(counts.index, counts.values, color=colors, alpha=0.9)
    ax.axvline(MIN_SAMPLE, color=ORANGE, ls="--", lw=1.2,
               label=f"порог надёжности: {MIN_SAMPLE} наблюдений")
    ax.set_title("Сколько наблюдений собрано по каждой работе")
    ax.set_xlabel("Количество цен")
    ax.legend()
    ax.tick_params(axis="y", labelsize=8)
    save(fig, "05_coverage_by_work.png")

    med = df.groupby("source")["price"].median().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(range(len(med)), med.values, color=BLUE, alpha=0.85)
    ax.axhline(df["price"].median(), color=ORANGE, ls="--", lw=1.2,
               label=f"медиана по рынку: {df['price'].median():,.0f} ₽")
    ax.set_title("Медианная цена у каждой из 22 компаний")
    ax.set_ylabel("₽ за единицу")
    ax.set_xlabel("Компании (обезличены, отсортированы по медиане)")
    ax.set_xticks([])
    ax.legend()
    save(fig, "06_price_by_company.png")

    ratio = med.max() / med.min()
    n_thin = int((df["canonical_work"].value_counts() < MIN_SAMPLE).sum())
    lines = [
        "# EDA на реальных собранных данных\n",
        f"- Цен после очистки: **{len(df)}**",
        f"- Видов работ: **{df['canonical_work'].nunique()}**, "
        f"компаний: **{df['source'].nunique()}**, городов: **{df['region'].nunique()}**",
        f"- Медианная цена за единицу: **{df['price'].median():,.0f} ₽**, "
        f"среднее: **{df['price'].mean():,.0f} ₽**",
        f"- Работ с выборкой меньше {MIN_SAMPLE}: **{n_thin}** "
        f"(для них коридор берётся на уровне категории)",
        f"- Самая дорогая компания дороже самой дешёвой по медиане в **{ratio:.1f} раза**\n",
        "## Выводы, которые определили моделирование\n",
        "1. **Цены логнормальны** (график 01) — поэтому модель обучается на `log(price)`, "
        "а ошибки считаются относительными, а не в рублях.",
        "2. **Между компаниями разрыв в "
        f"{ratio:.1f} раза** (график 06) — поэтому валидация делается "
        "leave-one-company-out: случайный сплит завышал бы качество.",
        "3. **Разброс P90/P10 внутри одной работы доходит до "
        f"{spread.max():.1f}×** (график 04) — именно поэтому умеренная накрутка "
        "+25% не детектируется: она тонет в нормальном рыночном разбросе.",
        f"4. **{n_thin} работ имеют меньше {MIN_SAMPLE} наблюдений** (график 05) — "
        "для них система отказывается давать оценку или падает на уровень категории.\n",
        "## Медианная цена по городам\n",
        df.groupby("region")["price"].median().round(0).sort_values()
          .to_frame("₽").to_markdown(),
        "\n## Медианная цена по категориям\n",
        by_cat.round(0).to_frame("₽").to_markdown(),
    ]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nСводка сохранена: reports/eda_summary.md")

    print("\n--- Ключевые цифры ---")
    print(f"Медианная цена: {df['price'].median():,.0f} ₽")
    print(f"Разрыв между компаниями: {ratio:.1f}x")
    print(f"Максимальный разброс P90/P10 внутри работы: {spread.max():.1f}x")
    print(f"Работ с выборкой < {MIN_SAMPLE}: {n_thin}")


if __name__ == "__main__":
    main()
