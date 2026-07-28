"""Экспертная база по ремонту и поиск по ней.

Это второй источник для ассистента. Первый — факты конкретного проекта, они
целиком помещаются в запрос. База знаний ведёт себя иначе: она растёт с каждым
видом работ, поэтому по ней ищем, а не отдаём целиком.

Поиск делает эмбеддинги GigaChat. Если они недоступны, включается запасной
вариант на пересечении слов: он хуже, но лучше молчания, и вызывающая сторона
узнаёт, каким способом получен результат.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.append(os.path.dirname(__file__))

BASE = os.path.dirname(__file__)
KNOWLEDGE_PATH = os.path.join(BASE, "..", "data", "knowledge", "renovation.json")
TOP_K = 4
MIN_SCORE = 0.15

_FRAGMENTS: list[dict] | None = None
_VECTORS: list[list[float]] | None = None


def load_fragments() -> list[dict]:
    global _FRAGMENTS
    if _FRAGMENTS is None:
        with open(KNOWLEDGE_PATH, encoding="utf-8") as fh:
            _FRAGMENTS = json.load(fh)["fragments"]
    return _FRAGMENTS


def _searchable(fragment: dict) -> str:
    return f"{fragment['stage']}. {fragment['kind']}. {fragment['text']}"


def _tokens(text: str) -> set[str]:
    # Обрезаем окончания грубо: «приёмки» и «приёмка» должны совпасть.
    return {w[:6] for w in re.findall(r"[а-яёa-z]{4,}", text.lower())}


def _lexical(question: str, fragments: list[dict]) -> list[tuple[float, dict]]:
    query = _tokens(question)
    if not query:
        return []
    scored = []
    for fragment in fragments:
        words = _tokens(_searchable(fragment))
        overlap = len(query & words)
        if overlap:
            scored.append((overlap / len(query), fragment))
    return scored


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def search(question: str, top_k: int = TOP_K) -> tuple[list[dict], str]:
    """Возвращает подходящие фрагменты и способ, которым они найдены."""
    fragments = load_fragments()
    if not question.strip():
        return [], "none"

    global _VECTORS
    try:
        import gigachat_embeddings

        if _VECTORS is None:
            _VECTORS = gigachat_embeddings.embed(
                [_searchable(f) for f in fragments])
        query_vec = gigachat_embeddings.embed([question])[0]
        scored = [(_cosine(query_vec, vec), fragment)
                  for vec, fragment in zip(_VECTORS, fragments)]
        backend = "gigachat_embeddings"
    except Exception:
        scored = _lexical(question, fragments)
        backend = "lexical"

    scored.sort(key=lambda pair: pair[0], reverse=True)
    picked = [fragment for score, fragment in scored[:top_k] if score >= MIN_SCORE]
    return picked, backend if picked else "none"
