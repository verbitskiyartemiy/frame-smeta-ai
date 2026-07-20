from __future__ import annotations
import io
import re
import os
import time
import pandas as pd
import requests

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/125.0 Safari/537.36"),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

SOURCES = [
    ("https://titanremont.ru/price", "Москва"),
    ("https://stroyremdizayn.ru/cena-remonta-i-otdelki-kvartir-pod-klyuch/", "Москва"),
    ("https://kronotech.ru/prays-shtukaturka-sten", "Москва"),
    ("https://remont-uroven.ru/price.html", "Москва"),
    ("https://remont-f.ru/remont-kvartir-pod-kluch/price.php", "Москва"),
    ("https://remonty-msk.ru/price/", "Москва"),
    ("https://profiremontnik.ru/tseny/otdelochnye-raboty/", "Москва"),
    ("https://www.remontstroyka.ru/tseny/prays-list-na-raboty.php", "Москва"),
    ("https://remont-novostroiki.ru/prays-list-na-remont-kvartir/", "Москва"),
    ("https://aqremont.ru/price", "Москва"),
    ("https://www.prorabneva.ru/price", "СПб"),
    ("https://otdelka-spb.ru/prajjs/", "СПб"),
    ("https://restroymaster.ru/services/otdelochnye-raboty/", "СПб"),
    ("https://razvitiee.com/services/otdelochnye-raboty/prays-list-na-otdelochnye-raboty/", "СПб"),
    ("https://www.stroikahome.ru/prays-otdelka.html", "СПб"),
    ("https://spb.optimumbuilding.ru/otdelka", "СПб"),
    ("https://etalon-house.spb.ru/uslugi/czeny-na-otdelochnye-raboty/", "СПб"),
    ("https://remont-nsk54.ru/prajs_list", "Новосибирск"),
    ("https://nsk.365rem.ru/ceni-na-otdelochnie-raboti.asp", "Новосибирск"),
    ("https://remo154.ru/price_otdelka.php", "Новосибирск"),
    ("https://mastercity54.ru/prices/", "Новосибирск"),
    ("https://kazan.365rem.ru/ceni-na-otdelochnie-raboti.asp", "Казань"),
    ("https://remo116.ru/price_otdelka.php", "Казань"),
    ("https://altair-kzn.ru/price-na-remont-kvartir", "Казань"),
    ("https://kazan.garantstroikompleks.ru/prajs-list", "Казань"),
    ("https://nn.365rem.ru/ceni-na-otdelochnie-raboti.asp", "Нижний Новгород"),
    ("https://remo152.ru/price_otdelka.php", "Нижний Новгород"),
    ("https://nn.korona-remont.ru/prices", "Нижний Новгород"),
    ("https://krasnodar.365rem.ru/ceni-na-otdelochnie-raboti.asp", "Краснодар"),
    ("https://printsipremonta.ru/prais-list/", "Екатеринбург"),
]

UNIT_MAP = {
    "м2": "м2", "м²": "м2", "кв.м": "м2", "кв. м": "м2", "м.кв": "м2", "m2": "м2",
    "м.п.": "мп", "мп": "мп", "м/п": "мп", "пог.м": "мп", "пог. м": "мп", "п.м": "мп",
    "шт": "шт", "шт.": "шт", "штука": "шт",
    "точка": "точка", "точ": "точка",
    "компл": "компл", "компл.": "компл", "комплект": "компл",
}
UNIT_TOKENS = list(UNIT_MAP.keys())


def norm_unit(cell) -> str | None:
    s = str(cell).strip().lower().replace(" ", "")
    for tok in sorted(UNIT_MAP, key=len, reverse=True):
        if tok.replace(" ", "") in s:
            return UNIT_MAP[tok]
    return None


def parse_price(cell):
    s = str(cell).replace("\xa0", " ").replace(" ", " ")
    m = re.search(r"(\d[\d ]{0,8}\d|\d{2,6})", s)
    if not m:
        return None
    num = m.group(1).replace(" ", "")
    try:
        v = float(num)
    except ValueError:
        return None
    if v < 30 or v > 100000:
        return None
    return v


def col_score_price(series) -> float:
    vals = [parse_price(x) for x in series]
    return sum(v is not None for v in vals) / max(1, len(vals))


def col_score_unit(series) -> float:
    vals = [norm_unit(x) for x in series]
    return sum(v is not None for v in vals) / max(1, len(vals))


def extract_from_table(df: pd.DataFrame, url: str, region: str) -> list[dict]:
    if df.shape[1] < 2 or df.shape[0] < 2:
        return []
    df = df.astype(str)
    ncol = df.shape[1]

    price_scores = [col_score_price(df.iloc[:, i]) for i in range(ncol)]
    price_col = int(max(range(ncol), key=lambda i: price_scores[i]))
    if price_scores[price_col] < 0.4:
        return []

    unit_scores = [col_score_unit(df.iloc[:, i]) if i != price_col else 0
                   for i in range(ncol)]
    unit_col = int(max(range(ncol), key=lambda i: unit_scores[i]))
    has_unit = unit_scores[unit_col] > 0.3

    def text_score(series):
        return sum(len(re.sub(r"[\d ,.\-]", "", str(x))) > 3 for x in series) / max(1, len(series))
    name_scores = [text_score(df.iloc[:, i]) if i not in (price_col,) else 0
                   for i in range(ncol)]
    name_col = int(max(range(ncol), key=lambda i: name_scores[i]))

    rows = []
    for _, r in df.iterrows():
        work = str(r.iloc[name_col]).strip()
        price = parse_price(r.iloc[price_col])
        unit = norm_unit(r.iloc[unit_col]) if has_unit else norm_unit(r.iloc[price_col]) or norm_unit(work)
        if not work or price is None or len(work) < 4:
            continue
        if re.fullmatch(r"[\d ,.\-]+", work):
            continue
        rows.append({"work_raw": work, "unit_raw": unit, "price": price,
                     "region": region, "source": url})
    return rows


def main():
    all_rows = []
    for url, region in SOURCES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.encoding = resp.apparent_encoding or "utf-8"
            tables = pd.read_html(io.StringIO(resp.text))
        except Exception as e:
            print(f"[SKIP] {url} -> {type(e).__name__}: {str(e)[:80]}")
            continue
        rows = []
        for t in tables:
            rows.extend(extract_from_table(t, url, region))
        print(f"[OK]   {region:7} {url[:55]:55} таблиц={len(tables):2}  строк={len(rows)}")
        all_rows.extend(rows)
        time.sleep(1)

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["work_raw", "unit_raw", "price", "region"])
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "real"))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "raw_prices.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")

    print("\n===== ИТОГ =====")
    print(f"Собрано строк: {len(df)}")
    if len(df):
        print(f"Компаний-источников: {df['source'].nunique()}")
        print("По регионам:", df.groupby("region").size().to_dict())
        print(f"Диапазон цен: {df['price'].min():.0f} — {df['price'].max():.0f} руб")
        print(f"Файл: {out}")


if __name__ == "__main__":
    main()
