from __future__ import annotations
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = os.path.dirname(__file__)
REP = os.path.abspath(os.path.join(BASE, "..", "reports"))
FIG = os.path.join(REP, "figures")

BLUE = "#2f6db0"
GREEN = "#2e9e6b"
ORANGE = "#c65b2f"
GREY = "#9aa4ad"

plt.rcParams.update({
    "figure.dpi": 130, "font.size": 12,
    "axes.grid": True, "grid.alpha": 0.22,
    "axes.spines.top": False, "axes.spines.right": False,
})


def ladder():
    d = json.load(open(os.path.join(REP, "baseline_ladder.json"), encoding="utf-8"))
    names = ["Глобальная\nмедиана", "Медиана\nпо работе", "Медиана\nработа+город",
             "Линейная\nрегрессия", "XGBoost\nтюнингованный"]
    keys = ["global_median", "median_by_work", "median_by_work_region",
            "linear_regression", "xgboost"]
    vals = [d[k]["MAPE"][0] for k in keys]
    errs = [d[k]["MAPE"][1] for k in keys]
    colors = [GREY, ORANGE, GREY, GREEN, GREY]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    bars = ax.bar(names, vals, yerr=errs, capsize=5, color=colors, alpha=.92,
                  error_kw={"ecolor": "#555", "lw": 1.2})
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, f"{v:.1f}%",
                ha="center", fontsize=13, fontweight="bold")

    ax.annotate("", xy=(3, 41.5), xytext=(1, 46.5),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=2.2))
    ax.text(2.0, 56, "модель окупается\n−4.9 п.п. при шуме ±0.6",
            ha="center", color=GREEN, fontsize=12.5, fontweight="bold")
    ax.text(4.0, 22, "усложнение\nне окупается\n−0.5 п.п. < шума",
            ha="center", va="center", color=ORANGE, fontsize=12, fontweight="bold")

    ax.set_ylabel("Ошибка предсказания цены, MAPE %")
    ax.set_title("Где моделирование начинает и перестаёт окупаться\n"
                 "5-fold кросс-валидация на одних и тех же фолдах", fontsize=14, pad=14)
    ax.set_ylim(0, 108)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "11_baseline_ladder.png"), bbox_inches="tight")
    plt.close(fig)
    print("  11_baseline_ladder.png")


def three_experiments():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6))

    data = [
        ("Цена работы\n(таблица)",
         ["медиана", "линейная", "XGBoost"], [43.6, 38.7, 38.2],
         "MAPE %, ниже — лучше", [GREY, GREEN, GREY], "ПРОСТОЕ", ORANGE, True),
        ("Тональность отзыва\n(текст)",
         ["baseline", "словарь", "трансформер"], [0.500, 0.870, 0.962],
         "ROC-AUC, выше — лучше", [GREY, GREY, GREEN], "СЛОЖНОЕ", GREEN, False),
        ("Тип события в чате\n(текст)",
         ["baseline", "эмбеддинги", "правила"], [0.356, 0.689, 0.822],
         "Accuracy, выше — лучше", [GREY, GREY, GREEN], "ПРОСТОЕ", ORANGE, False),
    ]

    for ax, (title, labels, vals, ylab, colors, verdict, vcol, lower_better) in zip(axes, data):
        bars = ax.bar(labels, vals, color=colors, alpha=.92)
        for b, v in zip(bars, vals):
            txt = f"{v:.1f}" if lower_better else f"{v:.3f}"
            ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * .03, txt,
                    ha="center", fontsize=11.5, fontweight="bold")
        ax.set_title(title, fontsize=13, pad=10)
        ax.set_ylabel(ylab, fontsize=10.5)
        ax.set_ylim(0, max(vals) * 1.28)
        ax.tick_params(axis="x", labelsize=10.5)
        ax.text(.5, .93, f"победило {verdict}", transform=ax.transAxes,
                ha="center", fontsize=12, fontweight="bold", color=vcol)

    fig.suptitle("Три измеренных эксперимента: сложная модель выиграла один раз из трёх",
                 fontsize=15, y=1.04, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "12_three_experiments.png"), bbox_inches="tight")
    plt.close(fig)
    print("  12_three_experiments.png")


if __name__ == "__main__":
    ladder()
    three_experiments()


def aspect_profile():
    aspects = ["Сроки", "Цена и смета", "Чистота", "Коммуникация", "Гарантия",
               "Профессионализм", "Вежливость", "Честность", "Качество работ"]
    scores = [2.1, 2.8, 3.2, 3.6, 3.9, 4.3, 4.5, 4.6, 4.8]
    colors = ["#c0472f" if s < 3 else "#c07a1e" if s < 4 else "#2e9e6b" for s in scores]

    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.barh(aspects, scores, color=colors, alpha=.92, height=.68)
    for b, s in zip(bars, scores):
        ax.text(s + .08, b.get_y() + b.get_height() / 2, f"{s:.1f}",
                va="center", fontsize=13, fontweight="bold")
    ax.axvline(3, color="#999", ls="--", lw=1.2)
    ax.set_xlim(0, 5.4)
    ax.set_xlabel("Оценка по аспекту (из текста отзывов)", fontsize=12)
    ax.set_title("Профиль мастера: вместо одной звезды — девять сторон\n"
                 "«Плитку кладёт отлично, но срывает сроки» — видно сразу",
                 fontsize=14, pad=14)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "13_aspect_profile.png"), bbox_inches="tight")
    plt.close(fig)
    print("  13_aspect_profile.png")


if __name__ == "__main__":
    aspect_profile()
