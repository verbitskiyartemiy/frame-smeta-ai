import pandas as pd

from train_model import empirical_corridor


def _toy_df():
    return pd.DataFrame({
        "canonical_work": ["A"] * 6 + ["B"] * 2 + ["C"] * 6,
        "category": ["cat1"] * 6 + ["cat2"] * 2 + ["cat2"] * 6,
        "price": [100, 110, 90, 105, 95, 120, 200, 210, 500, 510, 490, 505, 495, 520],
    })


def test_corridor_uses_work_level_quantiles_when_enough_samples():
    df = _toy_df()
    corridor = empirical_corridor(df)
    lo, hi = corridor(pd.Series({"canonical_work": "A", "category": "cat1"}))
    work_a = df[df.canonical_work == "A"]["price"]
    assert lo == work_a.quantile(0.10)
    assert hi == work_a.quantile(0.90)


def test_corridor_falls_back_to_category_when_work_has_few_samples():
    # "B" has only 2 rows (< 5) so the corridor must fall back to the
    # category-level (cat2) quantiles rather than B's own noisy quantiles.
    df = _toy_df()
    corridor = empirical_corridor(df)
    lo, hi = corridor(pd.Series({"canonical_work": "B", "category": "cat2"}))
    cat2 = df[df.category == "cat2"]["price"]
    assert lo == cat2.quantile(0.10)
    assert hi == cat2.quantile(0.90)


def test_corridor_lo_below_hi_for_every_work():
    df = _toy_df()
    corridor = empirical_corridor(df)
    for work, category in df[["canonical_work", "category"]].drop_duplicates().itertuples(index=False):
        lo, hi = corridor(pd.Series({"canonical_work": work, "category": category}))
        assert lo < hi
