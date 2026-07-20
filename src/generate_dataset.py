from __future__ import annotations

import os
import numpy as np
import pandas as pd

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

WORKS = [
    dict(name="Демонтаж обоев",              category="Демонтаж",    unit="м2",  base_price=90,   qty_driver="wall",    prob=0.55),
    dict(name="Демонтаж плитки",             category="Демонтаж",    unit="м2",  base_price=260,  qty_driver="floor",   prob=0.45),
    dict(name="Демонтаж стяжки",             category="Демонтаж",    unit="м2",  base_price=300,  qty_driver="floor",   prob=0.30),
    dict(name="Демонтаж перегородки",        category="Демонтаж",    unit="м2",  base_price=420,  qty_driver="rooms",   prob=0.35),

    dict(name="Штукатурка стен по маякам",   category="Стены",       unit="м2",  base_price=560,  qty_driver="wall",    prob=0.75),
    dict(name="Шпаклёвка стен",              category="Стены",       unit="м2",  base_price=350,  qty_driver="wall",    prob=0.80),
    dict(name="Грунтовка стен",              category="Стены",       unit="м2",  base_price=60,   qty_driver="wall",    prob=0.85),
    dict(name="Возведение перегородки ГКЛ",  category="Стены",       unit="м2",  base_price=820,  qty_driver="rooms",   prob=0.40),
    dict(name="Поклейка обоев",              category="Стены",       unit="м2",  base_price=400,  qty_driver="wall",    prob=0.55),
    dict(name="Покраска стен",               category="Стены",       unit="м2",  base_price=350,  qty_driver="wall",    prob=0.45),
    dict(name="Укладка плитки на стену",     category="Стены",       unit="м2",  base_price=1500, qty_driver="wall",    prob=0.40),

    dict(name="Стяжка пола",                 category="Пол",         unit="м2",  base_price=700,  qty_driver="floor",   prob=0.70),
    dict(name="Наливной пол",                category="Пол",         unit="м2",  base_price=500,  qty_driver="floor",   prob=0.40),
    dict(name="Укладка ламината",            category="Пол",         unit="м2",  base_price=450,  qty_driver="floor",   prob=0.55),
    dict(name="Укладка плитки на пол",       category="Пол",         unit="м2",  base_price=1300, qty_driver="floor",   prob=0.45),
    dict(name="Установка плинтуса",          category="Пол",         unit="мп",  base_price=250,  qty_driver="floor",   prob=0.70),

    dict(name="Штукатурка потолка",          category="Потолок",     unit="м2",  base_price=620,  qty_driver="ceiling", prob=0.50),
    dict(name="Натяжной потолок",            category="Потолок",     unit="м2",  base_price=550,  qty_driver="ceiling", prob=0.55),
    dict(name="Потолок из ГКЛ",              category="Потолок",     unit="м2",  base_price=1000, qty_driver="ceiling", prob=0.35),
    dict(name="Покраска потолка",            category="Потолок",     unit="м2",  base_price=300,  qty_driver="ceiling", prob=0.50),

    dict(name="Штробление под проводку",     category="Электрика",   unit="мп",  base_price=300,  qty_driver="points",  prob=0.70),
    dict(name="Прокладка кабеля",            category="Электрика",   unit="мп",  base_price=120,  qty_driver="points",  prob=0.75),
    dict(name="Монтаж розеток/выключателей", category="Электрика",   unit="шт",  base_price=350,  qty_driver="points",  prob=0.80),
    dict(name="Монтаж светильников",         category="Электрика",   unit="шт",  base_price=600,  qty_driver="rooms",   prob=0.65),
    dict(name="Сборка электрощита",          category="Электрика",   unit="шт",  base_price=6000, qty_driver="fixed",   prob=0.55),

    dict(name="Разводка труб (точка)",       category="Сантехника",  unit="точка", base_price=2500, qty_driver="points", prob=0.65),
    dict(name="Установка смесителя",         category="Сантехника",  unit="шт",  base_price=1500, qty_driver="fixed",   prob=0.60),
    dict(name="Установка унитаза",           category="Сантехника",  unit="шт",  base_price=2500, qty_driver="fixed",   prob=0.55),
    dict(name="Установка ванны",             category="Сантехника",  unit="шт",  base_price=3500, qty_driver="fixed",   prob=0.35),
    dict(name="Установка раковины",          category="Сантехника",  unit="шт",  base_price=2000, qty_driver="fixed",   prob=0.50),

    dict(name="Установка межкомнатной двери",category="Двери",       unit="шт",  base_price=3500, qty_driver="rooms",   prob=0.55),
    dict(name="Установка входной двери",     category="Двери",       unit="шт",  base_price=5000, qty_driver="fixed",   prob=0.30),
    dict(name="Монтаж откосов",              category="Двери",       unit="мп",  base_price=700,  qty_driver="rooms",   prob=0.40),
]

REGIONS = {
    "Москва":            1.35,
    "Санкт-Петербург":   1.20,
    "Город-миллионник":  1.00,
    "Крупный город":     0.90,
    "Регион":            0.78,
}
REGION_PROBS = [0.22, 0.13, 0.25, 0.20, 0.20]

QUALITY = {
    "Эконом":   0.80,
    "Стандарт": 1.00,
    "Комфорт":  1.25,
    "Премиум":  1.60,
}
QUALITY_PROBS = [0.30, 0.40, 0.20, 0.10]

PRICE_NOISE_SIGMA = 0.10


def make_apartment(apt_id: int) -> dict:
    rooms = int(rng.choice([1, 2, 3, 4], p=[0.30, 0.38, 0.24, 0.08]))
    base_area = {1: 38, 2: 55, 3: 75, 4: 100}[rooms]
    area = float(np.round(rng.normal(base_area, base_area * 0.12), 1))
    area = max(25.0, area)

    region = rng.choice(list(REGIONS.keys()), p=REGION_PROBS)
    quality = rng.choice(list(QUALITY.keys()), p=QUALITY_PROBS)
    return dict(apartment_id=apt_id, rooms=rooms, area_m2=area,
                region=region, quality_class=quality)


def quantity_for(work: dict, apt: dict) -> float:
    area = apt["area_m2"]
    rooms = apt["rooms"]
    wall_area = area * 2.7
    ceiling_area = area
    points = rooms * 6 + 8

    driver = work["qty_driver"]
    if driver == "wall":
        base = wall_area
    elif driver in ("floor", "ceiling"):
        base = area if driver == "floor" else ceiling_area
    elif driver == "rooms":
        base = rooms * rng.uniform(0.8, 1.4)
    elif driver == "points":
        base = points
    else:
        base = rng.integers(1, 3)

    factor = rng.uniform(0.5, 1.0) if driver in ("wall", "floor", "ceiling") else 1.0
    qty = base * factor
    if work["unit"] in ("шт", "точка"):
        return float(max(1, round(qty)))
    return float(np.round(qty, 1))


def fair_unit_price(work: dict, apt: dict) -> float:
    price = work["base_price"]
    price *= REGIONS[apt["region"]]
    price *= QUALITY[apt["quality_class"]]
    price *= float(rng.lognormal(mean=0.0, sigma=PRICE_NOISE_SIGMA))
    return float(np.round(price, 2))


def build_dataset(n_apartments: int = 600) -> pd.DataFrame:
    rows = []
    for apt_id in range(1, n_apartments + 1):
        apt = make_apartment(apt_id)
        for work in WORKS:
            if rng.random() > work["prob"]:
                continue
            qty = quantity_for(work, apt)
            unit_price = fair_unit_price(work, apt)
            rows.append({
                **apt,
                "work_category": work["category"],
                "work_name": work["name"],
                "unit": work["unit"],
                "quantity": qty,
                "unit_price": unit_price,
                "line_cost": float(np.round(qty * unit_price, 2)),
            })
    df = pd.DataFrame(rows)
    cols = ["apartment_id", "region", "quality_class", "area_m2", "rooms",
            "work_category", "work_name", "unit", "quantity",
            "unit_price", "line_cost"]
    return df[cols]


def main():
    df = build_dataset(n_apartments=600)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "smeta_dataset.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Сохранено: {out_path}")
    print(f"Строк (позиций смет): {len(df):,}")
    print(f"Квартир: {df['apartment_id'].nunique()}")
    print(f"Уникальных работ: {df['work_name'].nunique()}")
    print(f"Средняя цена за единицу: {df['unit_price'].mean():,.0f} руб")
    print("\nСредняя смета по квартире (руб):")
    per_apt = df.groupby("apartment_id")["line_cost"].sum()
    print(f"  медиана: {per_apt.median():,.0f} | среднее: {per_apt.mean():,.0f}")
    print("\nРаспределение по регионам:")
    print(df.groupby("region")["unit_price"].mean().round(0).to_string())
    print("\nПервые строки:")
    print(df.head(8).to_string(index=False))


if __name__ == "__main__":
    main()
