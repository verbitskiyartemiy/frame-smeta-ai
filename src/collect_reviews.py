from __future__ import annotations
import html
import os
import re
import time

import pandas as pd
import requests

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/125.0 Safari/537.36"),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

LISTINGS = [
    ("https://www.yell.ru/spb/top/remont-kvartir/", "spb"),
    ("https://www.yell.ru/msk/top/remont-kvartir/", "msk"),
]


def get(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def company_review_urls(listing_html, city):
    links = set(re.findall(rf'href="(/{city}/com/[^"]+/reviews/)"', listing_html))
    return sorted("https://www.yell.ru" + l for l in links)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def parse_reviews(page_html, url):
    blocks = re.split(r'itemprop="review"', page_html)[1:]
    rows = []
    for b in blocks:
        m_body = re.search(r'itemprop="reviewBody"[^>]*>(.*?)</', b, re.S)
        if not m_body:
            continue
        text = re.sub(r"\s+", " ", strip_tags(m_body.group(1)))
        if len(text) < 40:
            continue
        m_rate = re.search(r'rating__value">\s*([\d.]+)\s*<', b)
        rating = float(m_rate.group(1)) if m_rate else None
        rows.append({"text": text, "rating": rating, "source": url})
    return rows


def main():
    all_rows = []
    for listing_url, city in LISTINGS:
        try:
            listing = get(listing_url)
        except Exception as e:
            print(f"[SKIP] {listing_url} -> {e}")
            continue
        urls = company_review_urls(listing, city)
        print(f"{city}: компаний с отзывами {len(urls)}")
        for u in urls:
            got = 0
            for page in range(1, 6):
                pu = u if page == 1 else f"{u}?page={page}"
                try:
                    rows = parse_reviews(get(pu), pu)
                except Exception:
                    break
                if not rows:
                    break
                got += len(rows)
                all_rows.extend(rows)
                time.sleep(1.0)
            print(f"  {u.split('/com/')[1][:50]:50} отзывов={got}")

    df = pd.DataFrame(all_rows)
    if len(df):
        df["text_norm"] = df["text"].str.lower().str.strip()
        df = df.drop_duplicates(subset="text_norm").drop(columns="text_norm")
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "reviews"))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "raw_reviews.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nИтого отзывов: {len(df)}")
    if len(df):
        print(f"Средняя длина: {df['text'].str.len().mean():.0f} символов")
        print(f"С оценкой: {df['rating'].notna().sum()}")
        print(f"Распределение оценок:\n{df['rating'].value_counts().sort_index().to_string()}")
    print(f"Файл: {out}")


if __name__ == "__main__":
    main()
