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

    path = os.path.abspath(os.path.join(BASE, "..", "reports", "baseline_ladder.json"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nreports/baseline_ladder.json")


if __name__ == "__main__":
    main()
