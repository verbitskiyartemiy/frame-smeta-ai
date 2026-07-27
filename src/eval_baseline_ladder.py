from __future__ import annotations
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.model_selection import KFold
from xgboost import XGBRegressor

sys.path.append(os.path.dirname(__file__))
from train_model import FEATURES, make_pipe

BASE = os.path.dirname(__file__)
XGB = dict(n_estimators=400, max_depth=3, learning_rate=0.1,
           subsample=0.9, reg_lambda=2.0, random_state=42)


def score(y_true, pred):
    return (mean_absolute_percentage_error(y_true, pred) * 100,
            r2_score(y_true, pred))


def loco_ladder(df):
    rows = []
    for company in df["source"].unique():
        tr = df[df["source"] != company]
        te = df[df["source"] == company]
        if len(te) < 5:
            continue
        y = te["price"].to_numpy(float)
        fallback = float(tr["price"].median())

        m_w = tr.groupby("canonical_work")["price"].median()
        p_med = te["canonical_work"].map(m_w).fillna(fallback).to_numpy(float)

        pipe = make_pipe(LinearRegression())
        pipe.fit(tr[FEATURES], np.log(tr["price"]))
        p_lin = np.exp(pipe.predict(te[FEATURES]))

        rows.append(score(y, p_med) + score(y, p_lin))

    a = np.array(rows)
    med_better = int((a[:, 2] < a[:, 0]).sum())
    return {
        "n_companies": len(a),
        "median_by_work": {"MAPE": [round(float(a[:, 0].mean()), 1),
                                    round(float(a[:, 0].std()), 1)],
                           "R2": round(float(a[:, 1].mean()), 3)},
        "linear_regression": {"MAPE": [round(float(a[:, 2].mean()), 1),
                                       round(float(a[:, 2].std()), 1)],
                              "R2": round(float(a[:, 3].mean()), 3)},
        "linear_wins_by_mape": med_better,
        "conclusion": (
            "На НОВОЙ компании линейная модель по MAPE не превосходит подстановку "
            f"медианы ({a[:,2].mean():.1f} против {a[:,0].mean():.1f}) и выигрывает "
            f"лишь на {med_better} компаниях из {len(a)}. По R2 она лучше "
            f"({a[:,3].mean():.3f} против {a[:,1].mean():.3f}), то есть лучше "
            "ранжирует, но не точнее в процентах. Выигрыш на случайном CV частично "
            "объясняется тем, что признак source запоминает ценовой уровень компании, "
            "а при domain shift этот признак бесполезен. Вывод для продукта: "
            "в интерфейсе показываем объяснимые рыночные коридоры, а модель даёт "
            "условную оценку на знакомом распределении."
        ),
    }


def main():
    df = pd.read_csv(os.path.join(BASE, "..", "data", "processed", "clean_prices.csv"))
    y = df["price"].to_numpy(float)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    names = ["global_median", "median_by_work", "median_by_work_region",
             "linear_regression", "xgboost"]
    res = {n: [] for n in names}

    for tr, te in kf.split(df):
        d_tr, d_te = df.iloc[tr], df.iloc[te]
        fallback = float(np.median(y[tr]))

        res["global_median"].append(score(y[te], np.full(len(te), fallback)))

        m_w = d_tr.groupby("canonical_work")["price"].median()
        p = d_te["canonical_work"].map(m_w).fillna(fallback).to_numpy(float)
        res["median_by_work"].append(score(y[te], p))

        m_wr = d_tr.groupby(["canonical_work", "region"])["price"].median()
        p = pd.MultiIndex.from_frame(d_te[["canonical_work", "region"]]).map(m_wr)
        p = (pd.Series(p).fillna(d_te["canonical_work"].map(m_w).reset_index(drop=True))
             .fillna(fallback).to_numpy(float))
        res["median_by_work_region"].append(score(y[te], p))

        pipe = make_pipe(LinearRegression())
        pipe.fit(d_tr[FEATURES], np.log(d_tr["price"]))
        res["linear_regression"].append(score(y[te], np.exp(pipe.predict(d_te[FEATURES]))))

        pipe = make_pipe(XGBRegressor(**XGB))
        pipe.fit(d_tr[FEATURES], np.log(d_tr["price"]))
        res["xgboost"].append(score(y[te], np.exp(pipe.predict(d_te[FEATURES]))))

    out = {}
    print(f"{'метод':26} {'MAPE %':>14}   {'R2':>16}")
    print("-" * 60)
    for n in names:
        a = np.array(res[n])
        out[n] = {"MAPE": [round(float(a[:, 0].mean()), 1), round(float(a[:, 0].std()), 1)],
                  "R2": [round(float(a[:, 1].mean()), 3), round(float(a[:, 1].std()), 3)]}
        print(f"{n:26} {a[:,0].mean():7.1f} ± {a[:,0].std():4.1f}   "
              f"{a[:,1].mean():8.3f} ± {a[:,1].std():5.3f}")

    gain_over_median = out["median_by_work"]["MAPE"][0] - out["linear_regression"]["MAPE"][0]
    noise = out["median_by_work"]["MAPE"][1]
    gain_over_linear = out["linear_regression"]["MAPE"][0] - out["xgboost"]["MAPE"][0]
    noise_lin = out["linear_regression"]["MAPE"][1]

    out["verdict"] = {
        "gain_linear_over_median_pp": round(float(gain_over_median), 1),
        "fold_noise_median_pp": noise,
        "modelling_pays_off": bool(gain_over_median > noise),
        "gain_xgb_over_linear_pp": round(float(gain_over_linear), 1),
        "fold_noise_linear_pp": noise_lin,
        "complexity_pays_off": bool(gain_over_linear > noise_lin),
        "conclusion": (
            "Моделирование окупается: линейная регрессия бьёт подстановку медианы "
            f"по виду работы на {gain_over_median:.1f} п.п. MAPE при межфолдовом "
            f"разбросе {noise} п.п. Дальнейшее усложнение не окупается: XGBoost "
            f"выигрывает у линейной {gain_over_linear:.1f} п.п. при разбросе "
            f"{noise_lin} п.п. Ручная медиана по паре работа+город работает ХУЖЕ "
            "медианы по работе — ячейки пустеют, а линейная модель оценивает "
            "эффект города по всем работам сразу."
        ),
    }

    print("\n" + out["verdict"]["conclusion"])

    loco = loco_ladder(df)
    out["loco_ladder"] = loco
    print(f"\n--- Тот же вопрос при domain shift (LOCO, {loco['n_companies']} компаний) ---")
    print(f"  медиана по работе: MAPE {loco['median_by_work']['MAPE'][0]} "
          f"± {loco['median_by_work']['MAPE'][1]}   R2 {loco['median_by_work']['R2']}")
    print(f"  линейная модель:   MAPE {loco['linear_regression']['MAPE'][0]} "
          f"± {loco['linear_regression']['MAPE'][1]}   R2 {loco['linear_regression']['R2']}")
    print("\n" + loco["conclusion"])

    path = os.path.abspath(os.path.join(BASE, "..", "reports", "baseline_ladder.json"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nreports/baseline_ladder.json")


if __name__ == "__main__":
    main()
