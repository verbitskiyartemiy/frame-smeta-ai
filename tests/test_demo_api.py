"""Тесты HTTP-границы демо. Сеть не используется: LLM подменяется заглушкой."""

import random
from unittest import mock

import pytest

import demo_api
import hybrid_coordinator


@pytest.fixture
def client():
    demo_api.app.config.update(TESTING=True)
    return demo_api.app.test_client()


CHAIN = [
    {"id": 1, "author": "Игорь", "ts": "2026-05-12",
     "text": "Проводка старая, полная замена будет +12 000 ₽"},
    {"id": 2, "author": "Вы", "ts": "2026-05-12",
     "text": "Это если менять полностью?"},
    {"id": 3, "author": "Игорь", "ts": "2026-05-12",
     "text": "Частично не советую, риск перегрева"},
    {"id": 4, "author": "Вы", "ts": "2026-05-12",
     "text": "Тогда меняем полностью"},
]


def test_health_reports_config_without_secrets(client):
    body = client.get("/api/health").get_json()
    assert body["status"] == "ok"
    assert set(body) >= {"llm_configured", "provider"}
    dumped = str(body)
    assert "LLM_AUTH_KEY" not in dumped
    for value in body.values():
        assert len(str(value)) < 200, "в health не должно быть длинных секретов"


def test_cors_allows_only_local_frontend(client):
    allowed = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5174"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5174"

    foreign = client.get("/api/health", headers={"Origin": "https://example.com"})
    assert foreign.headers.get("Access-Control-Allow-Origin") is None


def test_analyze_reports_rules_only_when_llm_unavailable(client):
    def broken_llm(*_args, **_kwargs):
        raise RuntimeError("LLM недоступна")

    with mock.patch.object(hybrid_coordinator, "call_llm", broken_llm):
        body = client.post("/api/coordinator/analyze",
                           json={"messages": CHAIN,
                                 "use_embeddings": False}).get_json()

    assert body["mode"] == "RULES_ONLY"
    assert body["extraction_backend"] == "rules"
    assert body["retrieval_backend"] == "rules", (
        "без живых embeddings нельзя заявлять gigachat_embeddings")


def test_analyze_keeps_events_grounded_in_real_messages(client):
    def broken_llm(*_args, **_kwargs):
        raise RuntimeError("LLM недоступна")

    with mock.patch.object(hybrid_coordinator, "call_llm", broken_llm):
        body = client.post("/api/coordinator/analyze",
                           json={"messages": CHAIN,
                                 "use_embeddings": False}).get_json()

    known_ids = {m["id"] for m in CHAIN}
    assert body["events"], "rule fallback обязан находить денежное событие"
    for event in body["events"]:
        assert event["source_message_ids"], "событие без источников недопустимо"
        assert set(event["source_message_ids"]) <= known_ids
        assert event["user_status"] == "pending", (
            "модель не может подтвердить действие за человека")


def test_analyze_rejects_message_without_text(client):
    response = client.post("/api/coordinator/analyze",
                           json={"messages": [{"id": 1, "author": "Вы"}]})
    assert response.status_code == 400


def test_estimate_returns_benchmark_and_abstains(client):
    body = client.post("/api/estimate/analyze", json={"lines": [
        {"name": "Штукатурка стен по маякам", "qty": 40, "price": 850},
        {"name": "Монтаж телепорта", "qty": 1, "price": 50000},
    ]}).get_json()

    assert body["coverage"] == {"matched": 1, "total": 2}
    benchmarked = [i for i in body["items"] if i["assessment"] == "benchmarked"]
    assert benchmarked[0]["median_benchmark"] > 0
    assert benchmarked[0]["corridor"]["p10"] < benchmarked[0]["corridor"]["p90"]

    skipped = [i for i in body["items"] if i["assessment"] == "none"]
    assert skipped and skipped[0]["reason"]
    assert "median_benchmark" not in skipped[0], (
        "без сопоставления ориентир выдавать нельзя")


def test_estimate_never_uses_forbidden_wording(client):
    body = client.post("/api/estimate/analyze",
                       json={"lines": [{"name": "Грунтовка стен", "qty": 10,
                                        "price": 120}]}).get_json()
    dumped = str(body).lower()
    for banned in ("переплат", "мошенн", "справедливая цена", "завысил"):
        assert banned not in dumped


def test_estimate_invariants_hold_on_randomised_prices(client):
    """Демо генерирует случайные цены — вердикт должен оставаться согласованным."""
    rng = random.Random(20260728)
    works = ["Штукатурка стен", "Грунтовка стен", "Стяжка пола",
             "Укладка ламината", "Покраска стен", "Установка ванны",
             "Монтаж системы умного дома", "Прочие работы по объекту"]

    for _ in range(25):
        lines = [{"name": name, "qty": rng.randint(1, 200),
                  "price": round(rng.uniform(30, 9000), 2)}
                 for name in rng.sample(works, 5)]
        body = client.post("/api/estimate/analyze",
                           json={"lines": lines}).get_json()

        for item in body["items"]:
            if item["assessment"] != "benchmarked":
                assert "median_benchmark" not in item
                assert "corridor" not in item
                continue
            corridor = item["corridor"]
            median = item["median_benchmark"]
            assert corridor["p10"] <= median <= corridor["p90"]
            assert item["sample_size"] >= demo_api.MIN_SAMPLE
            expected = round((item["unit_price"] / median - 1) * 100, 1)
            assert item["deviation_pct"] == expected


def test_estimate_requires_payload(client):
    assert client.post("/api/estimate/analyze", json={}).status_code == 400


def test_embeddings_failure_does_not_claim_gigachat_retrieval(client):
    """Если embeddings упали, retrieval нельзя называть gigachat_embeddings."""
    def broken_llm(*_args, **_kwargs):
        raise RuntimeError("LLM недоступна")

    def broken_embed(*_args, **_kwargs):
        raise RuntimeError("embeddings недоступны")

    with mock.patch.object(hybrid_coordinator, "call_llm", broken_llm),             mock.patch("gigachat_embeddings.embed", broken_embed):
        body = client.post("/api/coordinator/analyze",
                           json={"messages": CHAIN,
                                 "use_embeddings": True}).get_json()

    assert body["retrieval_backend"] == "rules"
    assert body["extraction_backend"] == "rules"
    assert body["mode"] == "RULES_ONLY"


def test_simulated_reply_is_marked_as_simulation(client):
    with mock.patch.object(hybrid_coordinator, "call_llm",
                           lambda *a, **k: "  Проводка старая,\n доплата 12 000 руб  "):
        body = client.post("/api/simulate/reply",
                           json={"messages": CHAIN}).get_json()

    assert body["simulated"] is True, "реплику стенда нельзя выдавать за человека"
    assert body["text"] == "Проводка старая, доплата 12 000 руб"


def test_simulated_reply_reports_failure_instead_of_inventing(client):
    def broken_llm(*_args, **_kwargs):
        raise RuntimeError("LLM недоступна")

    with mock.patch.object(hybrid_coordinator, "call_llm", broken_llm):
        response = client.post("/api/simulate/reply", json={"messages": CHAIN})

    assert response.status_code == 502
    assert "text" not in response.get_json(), "без LLM реплику придумывать нельзя"


def test_simulate_rejects_empty_payload(client):
    assert client.post("/api/simulate/reply", json={}).status_code == 400
    assert client.post("/api/simulate/reply",
                       json={"messages": [{"author": "Вы", "text": "   "}]}
                       ).status_code == 400
