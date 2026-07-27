import os

import numpy as np
import pandas as pd
import pytest

from clean_prices import to_canonical
from train_model import FEATURES, empirical_corridor, kfold_eval, make_pipe
from sklearn.linear_model import LinearRegression

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                    "clean_prices.csv")


@pytest.fixture(scope="module")
def df():
    if not os.path.exists(DATA):
        pytest.skip("нет data/processed/clean_prices.csv")
    return pd.read_csv(DATA)


def test_dataset_shape(df):
    assert len(df) > 1000
    for col in FEATURES + ["price"]:
        assert col in df.columns
    assert df["price"].gt(0).all()

    required = ["canonical_work", "category", "region", "source"]
    assert not df[required].isna().any().any()


def test_missing_unit_stays_within_known_share(df):
    missing = df["unit"].isna().mean()
    assert missing < 0.15, (
        f"доля строк без единицы измерения выросла до {missing:.1%}; "
        "скрапер перестал доставать колонку единиц"
    )


def test_train_predict_roundtrip(df):
    pipe = make_pipe(LinearRegression())
    pipe.fit(df[FEATURES], np.log(df["price"]))
    pred = np.exp(pipe.predict(df[FEATURES]))

    assert len(pred) == len(df)
    assert np.isfinite(pred).all()
    assert (pred > 0).all()


def test_unseen_category_does_not_crash(df):
    pipe = make_pipe(LinearRegression())
    pipe.fit(df[FEATURES], np.log(df["price"]))

    row = df[FEATURES].iloc[[0]].copy()
    row["source"] = "компания-которой-не-было"
    row["region"] = "Владивосток"

    pred = np.exp(pipe.predict(row))
    assert np.isfinite(pred).all() and pred[0] > 0


def test_cv_reports_sane_metrics(df):
    sample = df.sample(400, random_state=0)
    cv = kfold_eval(sample, LinearRegression, k=3)

    for key in ("MAE", "MAPE", "R2"):
        mean, std = cv[key]
        assert np.isfinite(mean) and np.isfinite(std)
        assert std >= 0
    assert cv["MAPE"][0] > 0


def test_estimate_line_gets_verdict(df):
    corridor = empirical_corridor(df)
    work, _, _, _ = to_canonical("Укладка плитки на пол")
    assert work is not None

    row = df[df["canonical_work"] == work].iloc[0]
    lo, hi = corridor(row)
    assert lo < hi

    assert not (lo <= hi * 50 <= hi)
    assert lo <= float(np.sqrt(lo * hi)) <= hi
