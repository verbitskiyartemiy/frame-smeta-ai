"""
Разведочный анализ данных (EDA) по датасету смет.

ЧТО ДЕЛАЕТ
----------
Смотрит на данные "глазами": строит графики распределения цен и того, как цена
зависит от региона, класса ремонта и категории работ. Все графики сохраняются
в reports/figures/*.png, а короткая текстовая сводка — в reports/eda_summary.md.

ЗАЧЕМ
-----
На конкурсе критерий "Data Science" требует показать понимание данных.
EDA — это первый обязательный шаг любого ML-проекта: прежде чем обучать модель,
надо понять, что вообще лежит в данных.
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # без окон — просто сохраняем картинки в файлы
import matplotlib.pyplot as plt

# --- пути ---
HERE = os.path.dirname(__file__)
DATA_PATH = os.path.abspath(os.path.join(HERE, "..", "data", "raw", "smeta_dataset.csv"))
FIG_DIR = os.path.abspath(os.path.join(HERE, "..", "reports", "figures"))
REPORT_PATH = os.path.abspath(os.path.join(HERE, "..", "reports", "eda_summary.md"))
os.makedirs(FIG_DIR, exist_ok=True)

# Единый аккуратный стиль графиков.
plt.rcParams.update({
    "figure.dpi": 120,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
ACCENT = "#4f46e5"


def save(fig, name: str):
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  сохранён график: reports/figures/{name}")


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Загружено строк: {len(df):,}, колонок: {df.shape[1]}")

    # Порядок категорий для красивых осей.
    region_order = ["Регион", "Крупный город", "Город-миллионник",
                    "Санкт-Петербург", "Москва"]
    quality_order = ["Эконом", "Стандарт", "Комфорт", "Премиум"]

    # --- График 1: распределение цены за единицу работы ---
    fig, ax = plt.subplots(figsize=(7, 4))
    # обрежем длинный хвост для читаемости (99-й перцентиль)
    clip = df["unit_price"].quantile(0.99)
    ax.hist(df.loc[df["unit_price"] <= clip, "unit_price"], bins=50, color=ACCENT, alpha=0.85)
    ax.set_title("Распределение цены за единицу работы")
    ax.set_xlabel("Цена за единицу, ₽")
    ax.set_ylabel("Количество позиций")
    save(fig, "01_unit_price_hist.png")

    # --- График 2: полная стоимость сметы по квартире ---
    per_apt = df.groupby("apartment_id")["line_cost"].sum() / 1000  # в тыс. ₽
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(per_apt, bins=40, color="#0ea5e9", alpha=0.85)
    ax.axvline(per_apt.median(), color="#ef4444", linestyle="--",
               label=f"медиана {per_apt.median():,.0f} тыс. ₽")
    ax.set_title("Полная стоимость ремонта по квартире")
    ax.set_xlabel("Стоимость сметы, тыс. ₽")
    ax.set_ylabel("Количество квартир")
    ax.legend()
    save(fig, "02_total_estimate_hist.png")

    # --- График 3: средняя цена по регионам ---
    by_region = df.groupby("region")["unit_price"].mean().reindex(region_order)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(by_region.index, by_region.values, color=ACCENT, alpha=0.85)
    ax.set_title("Средняя цена за единицу по регионам")
    ax.set_ylabel("Средняя цена, ₽")
    ax.set_xticks(range(len(by_region)))
    ax.set_xticklabels(by_region.index, rotation=20, ha="right")
    for i, v in enumerate(by_region.values):
        ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    save(fig, "03_price_by_region.png")

    # --- График 4: средняя цена по классу ремонта ---
    by_quality = df.groupby("quality_class")["unit_price"].mean().reindex(quality_order)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(by_quality.index, by_quality.values, color="#10b981", alpha=0.85)
    ax.set_title("Средняя цена за единицу по классу ремонта")
    ax.set_ylabel("Средняя цена, ₽")
    for i, v in enumerate(by_quality.values):
        ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    save(fig, "04_price_by_quality.png")

    # --- График 5: средняя цена по категориям работ ---
    by_cat = df.groupby("work_category")["unit_price"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(by_cat.index, by_cat.values, color="#f59e0b", alpha=0.9)
    ax.set_title("Средняя цена за единицу по категориям работ")
    ax.set_xlabel("Средняя цена, ₽")
    save(fig, "05_price_by_category.png")

    # --- График 6: площадь квартиры vs стоимость сметы ---
    apt = df.groupby("apartment_id").agg(
        area_m2=("area_m2", "first"),
        total=("line_cost", "sum"),
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(apt["area_m2"], apt["total"] / 1000, s=14, color=ACCENT, alpha=0.4)
    ax.set_title("Чем больше площадь — тем дороже ремонт")
    ax.set_xlabel("Площадь квартиры, м²")
    ax.set_ylabel("Стоимость сметы, тыс. ₽")
    save(fig, "06_area_vs_total.png")

    # --- Текстовая сводка ---
    corr = apt["area_m2"].corr(apt["total"])
    lines = [
        "# EDA — краткая сводка\n",
        f"- Всего позиций смет: **{len(df):,}**",
        f"- Квартир: **{df['apartment_id'].nunique()}**, видов работ: **{df['work_name'].nunique()}**",
        f"- Средняя цена за единицу: **{df['unit_price'].mean():,.0f} ₽**, медиана: **{df['unit_price'].median():,.0f} ₽**",
        f"- Медианная стоимость сметы по квартире: **{per_apt.median():,.0f} тыс. ₽**",
        f"- Связь «площадь → стоимость сметы»: корреляция **{corr:.2f}** (сильная положительная)\n",
        "## Средняя цена за единицу по регионам",
        by_region.round(0).to_frame("₽").to_markdown(),
        "\n## Средняя цена за единицу по классу ремонта",
        by_quality.round(0).to_frame("₽").to_markdown(),
    ]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nСводка сохранена: reports/eda_summary.md")

    # Короткий вывод в консоль
    print("\n--- Ключевые цифры ---")
    print(f"Средняя цена/ед.: {df['unit_price'].mean():,.0f} ₽")
    print(f"Медианная смета:  {per_apt.median():,.0f} тыс. ₽")
    print(f"Корреляция площадь→стоимость: {corr:.2f}")
    print("Цена Москва / Регион:",
          f"{by_region['Москва']:,.0f} / {by_region['Регион']:,.0f} ₽",
          f"(в {by_region['Москва']/by_region['Регион']:.2f} раза дороже)")


if __name__ == "__main__":
    main()
