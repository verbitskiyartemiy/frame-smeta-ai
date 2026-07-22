from __future__ import annotations
import html
import os
import re
import time

import pandas as pd
import requests

H = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"),
     "Accept-Language": "ru-RU,ru;q=0.9"}

CATEGORIES = [
    "https://otzyvru.com/remont-kvartir",
    "https://otzyvru.com/stroitelnaya-kompaniya",
    "https://otzyvru.com/remont-pod-klyuch",
]


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=H, timeout=25)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(3 * (i + 1))
    return None


def parse_page(t):
    rows = []
    for b in re.split(r'class="commentbox"', t)[1:]:
        w = re.search(r"width:\s*(\d+)px", b)
        if not w:
            continue
        runs = re.findall(r">([^<>]{50,})<", b)
        if not runs:
            continue
        text = html.unescape(max(runs, key=len)).strip()
        text = re.sub(r"\s+", " ", text)
        if len(text) < 60:
            continue
        rows.append({"text": text, "star_width": int(w.group(1))})
    return rows


def main():
    all_rows = []
    for cat in CATEGORIES:
        for page in range(1, 21):
            url = cat if page == 1 else f"{cat}?page={page}"
            t = fetch(url)
            if not t:
                break
            rows = parse_page(t)
            if not rows:
                break
            all_rows.extend(rows)
            print(f"{cat.split('/')[-1]:22} page {page:2}: {len(rows)} отзывов")
            time.sleep(2.0)

    df = pd.DataFrame(all_rows)
    if len(df):
        df["tn"] = df["text"].str.lower()
        df = df.drop_duplicates(subset="tn").drop(columns="tn")
        wmax = df["star_width"].max()
        df["rating"] = (df["star_width"] / wmax * 5).round(1)
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "reviews"))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "otzyvru_reviews.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nВсего: {len(df)}")
    if len(df):
        print("Ширины звёзд:", sorted(df["star_width"].unique()))
        print("Распределение оценок:")
        print(df["rating"].value_counts().sort_index().to_string())
    print(f"Файл: {out}")


if __name__ == "__main__":
    main()
