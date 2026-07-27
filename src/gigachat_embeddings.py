from __future__ import annotations
import hashlib
import time
import json
import os

import numpy as np
import requests

BASE = os.path.dirname(__file__)
CACHE = os.path.abspath(os.path.join(BASE, "..", "data", "processed", "emb_cache.json"))
API = "https://api.giga.chat/v1/embeddings"
BATCH = 12
RETRIES = 4


def _key(text: str, model: str) -> str:
    return hashlib.sha1(f"{model}::{text}".encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def embed(texts: list[str], model: str | None = None,
          use_cache: bool = True) -> np.ndarray:
    from llm_coordinator import _gigachat_token, load_env

    load_env()
    model = model or os.environ.get("LLM_EMBED_MODEL", "Embeddings")
    verify = os.environ.get("LLM_VERIFY_SSL", "0") == "1"

    cache = _load_cache() if use_cache else {}
    missing = [t for t in texts if _key(t, model) not in cache]

    if missing:
        auth = os.environ.get("LLM_AUTH_KEY")
        if not auth:
            raise RuntimeError("LLM_AUTH_KEY не задан — эмбеддинги недоступны")
        token = _gigachat_token(auth, os.environ.get("LLM_SCOPE",
                                                     "GIGACHAT_API_PERS"), verify)
        headers = {"Authorization": f"Bearer {token}",
                   "Content-Type": "application/json"}
        for i in range(0, len(missing), BATCH):
            chunk = missing[i:i + BATCH]
            for attempt in range(RETRIES):
                try:
                    base = os.environ.get("GIGACHAT_EMBEDDINGS_API_BASE")
                    url = base.rstrip("/") + "/embeddings" if base else API
                    r = requests.post(url, headers=headers,
                                      json={"model": model, "input": chunk},
                                      verify=verify, timeout=120)
                    r.raise_for_status()
                    break
                except requests.RequestException:
                    if attempt == RETRIES - 1:
                        raise
                    time.sleep(1.5 * (attempt + 1))
            for item, text in zip(r.json()["data"], chunk):
                cache[_key(text, model)] = item["embedding"]
            if use_cache:
                _save_cache(cache)

    vecs = np.array([cache[_key(t, model)] for t in texts], dtype=float)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.maximum(norms, 1e-9)


def main():
    v = embed(["затянули сроки работ", "опоздали на неделю", "цена выросла вдвое"])
    print("размерность:", v.shape)
    sim = v @ v.T
    print("близость «затянули сроки» ↔ «опоздали на неделю»:", round(float(sim[0, 1]), 3))
    print("близость «затянули сроки» ↔ «цена выросла вдвое»:", round(float(sim[0, 2]), 3))


if __name__ == "__main__":
    main()
