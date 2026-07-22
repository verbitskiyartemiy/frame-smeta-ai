from __future__ import annotations
import functools
import re

import numpy as np

ASPECTS = {
    "Сроки": [
        "сделали быстро и в срок", "затянули сроки работ", "опоздали на неделю",
        "закончили вовремя по графику", "работа заняла больше времени чем обещали",
    ],
    "Качество работ": [
        "качество работ отличное", "положили плитку ровно и аккуратно",
        "кривые стены пришлось переделывать", "брак в работе", "сделано на совесть без нареканий",
    ],
    "Цена и смета": [
        "цена соответствовала смете", "накрутили цену в процессе",
        "вышло дороже чем договаривались", "адекватные расценки без переплат",
        "смета выросла в два раза",
    ],
    "Чистота": [
        "убрали за собой мусор", "оставили грязь и пыль по всей квартире",
        "работали аккуратно не мусорили", "строительный мусор не вывезли",
    ],
    "Коммуникация": [
        "всегда на связи отвечали на вопросы", "не брали трубку пропадали",
        "держали в курсе хода работ", "сложно было дозвониться до бригадира",
        "присылали фотоотчёты каждый день",
    ],
    "Профессионализм": [
        "опытные мастера знают своё дело", "непрофессиональный подход",
        "грамотно посоветовали материалы", "видно что специалисты с опытом",
        "делали неумело без понимания",
    ],
    "Честность": [
        "честные ребята без обмана", "обманули с материалами",
        "все договорённости соблюдали", "исчезли с предоплатой",
        "прозрачно отчитывались за расходы",
    ],
    "Гарантия и недочёты": [
        "устранили недочёты по гарантии", "отказались исправлять косяки",
        "вернулись и бесплатно всё поправили", "на претензии не реагировали",
    ],
    "Вежливость": [
        "вежливые и приятные в общении", "хамили и грубили",
        "тактичные доброжелательные мастера", "разговаривали по-хамски",
    ],
}

POS_WORDS = set("""отличн хорош прекрасн супер доволен довольн рекоменд качествен аккуратн
быстр вовремя срок професси вежлив честн порядочн грамотн ответствен добросовестн
понравил спасибо благодар молодц идеальн чист убрал прозрачн адекватн""".split())

NEG_WORDS = set("""плох ужасн кошмар недоволь разочаров брак крив грязь мусор хам груб
обман кинул исчез пропал затянул опоздал сорвал дорож накрут переплат косяк недодел
переделыв халтур непрофесси безответствен жалоб испорти сломал""".split())

NEGATIONS = ("не ", "ни ", "нет ", "без ")


def split_clauses(text: str) -> list[str]:
    parts = re.split(r"[.!?;]+|\s+(?:но|однако|зато|хотя|а вот)\s+", text)
    return [p.strip() for p in parts if p and len(p.strip()) >= 15]


class AspectMatcher:
    def __init__(self, threshold: float = 0.42):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.threshold = threshold
        self._labels, phrases = [], []
        for aspect, anchor_list in ASPECTS.items():
            for a in anchor_list:
                self._labels.append(aspect)
                phrases.append(a)
        self._emb = self.model.encode(phrases, normalize_embeddings=True)

    def match(self, clause: str) -> list[tuple[str, float]]:
        q = self.model.encode([clause], normalize_embeddings=True)[0]
        sims = self._emb @ q
        best = {}
        for label, s in zip(self._labels, sims):
            if s >= self.threshold and s > best.get(label, 0):
                best[label] = float(s)
        return sorted(best.items(), key=lambda x: -x[1])[:3]


SENTIMENT_MODEL = "blanchefort/rubert-base-cased-sentiment"


class NeuralSentiment:
    def __init__(self):
        from transformers import pipeline
        self.pipe = pipeline(
            "text-classification",
            model=SENTIMENT_MODEL,
            device=-1, top_k=None,
        )

    def score(self, texts: list[str]) -> list[float]:
        out = []
        for res in self.pipe(texts, truncation=True, max_length=256, batch_size=16):
            d = {r["label"].lower(): r["score"] for r in res}
            out.append(d.get("positive", 0.0) - d.get("negative", 0.0))
        return out


def lexicon_sentiment(clause: str) -> float:
    s = clause.lower()
    score = 0
    for stem in POS_WORDS:
        for m in re.finditer(stem, s):
            start = max(0, m.start() - 12)
            neg = any(n in s[start:m.start()] for n in NEGATIONS)
            score += -1 if neg else 1
    for stem in NEG_WORDS:
        for m in re.finditer(stem, s):
            start = max(0, m.start() - 12)
            neg = any(n in s[start:m.start()] for n in NEGATIONS)
            score += 1 if neg else -1
    return float(np.clip(score, -3, 3)) / 3.0


@functools.lru_cache(maxsize=1)
def get_aspect_matcher() -> AspectMatcher:
    return AspectMatcher()


@functools.lru_cache(maxsize=1)
def get_neural_sentiment() -> NeuralSentiment:
    return NeuralSentiment()


def analyze_review(text: str, use_neural: bool = True) -> dict:
    clauses = split_clauses(text)
    if not clauses:
        return {}
    matcher = get_aspect_matcher()
    if use_neural:
        sentiments = get_neural_sentiment().score(clauses)
    else:
        sentiments = [lexicon_sentiment(c) for c in clauses]
    per_aspect = {}
    for clause, senti in zip(clauses, sentiments):
        for aspect, sim in matcher.match(clause):
            per_aspect.setdefault(aspect, []).append(senti)
    return {a: float(np.mean(v)) for a, v in per_aspect.items()}


def review_sentiment(text: str, use_neural: bool = True) -> float:
    clauses = split_clauses(text)
    if not clauses:
        return 0.0
    if use_neural:
        return float(np.mean(get_neural_sentiment().score(clauses)))
    return float(np.mean([lexicon_sentiment(c) for c in clauses]))
