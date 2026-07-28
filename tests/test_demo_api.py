"""Тесты HTTP-границы демо. Сеть не используется: LLM подменяется заглушкой."""

import json
import random
from unittest import mock

import pytest

import demo_api
import hybrid_coordinator
import knowledge


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


FACTS = [
    {"id": 1, "text": "Бюджет проекта 2 850 000 руб, потрачено 1 767 000 руб."},
    {"id": 2, "text": "Подрядчик Игорь обещал закончить электрику до 18 мая."},
    {"id": 3, "text": "Согласована доплата 12 000 руб за полную замену проводки."},
]


def _llm_returning(payload):
    return lambda *a, **k: json.dumps(payload, ensure_ascii=False)


def test_assistant_answers_with_sources(client):
    reply = {"answered": True, "source_ids": [1],
             "answer": "Потрачено 1 767 000 руб из бюджета 2 850 000 руб."}
    with mock.patch.object(hybrid_coordinator, "call_llm", _llm_returning(reply)):
        body = client.post("/api/assistant/ask",
                           json={"question": "Сколько потрачено?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is True
    assert body["source_ids"] == [1]
    assert body["quotes"] == [FACTS[0]["text"]]


def test_assistant_rejects_invented_numbers(client):
    """Сумма, которой нет в источнике, не должна доехать до пользователя."""
    reply = {"answered": True, "source_ids": [1],
             "answer": "Потрачено 1 767 000 руб, остаток 1 083 000 руб."}
    with mock.patch.object(hybrid_coordinator, "call_llm", _llm_returning(reply)):
        body = client.post("/api/assistant/ask",
                           json={"question": "Сколько осталось?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is False
    assert not body["answer"]
    assert "1083000" in body["reason"]


def test_assistant_rejects_unknown_fact_reference(client):
    reply = {"answered": True, "source_ids": [99],
             "answer": "Об этом написано в документах проекта."}
    with mock.patch.object(hybrid_coordinator, "call_llm", _llm_returning(reply)):
        body = client.post("/api/assistant/ask",
                           json={"question": "А что по гарантии?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is False
    assert not body["answer"]


def test_assistant_admits_missing_data(client):
    reply = {"answered": False, "source_ids": [], "answer": "",
             "reason": "в фактах проекта нет информации о гарантии"}
    with mock.patch.object(hybrid_coordinator, "call_llm", _llm_returning(reply)):
        body = client.post("/api/assistant/ask",
                           json={"question": "Какая гарантия?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is False
    assert "гаранти" in body["reason"].lower()


def test_assistant_requires_question_and_facts(client):
    assert client.post("/api/assistant/ask",
                       json={"facts": FACTS}).status_code == 400
    assert client.post("/api/assistant/ask",
                       json={"question": "Сколько?"}).status_code == 400


def test_assistant_reports_failure_without_inventing(client):
    def broken_llm(*_args, **_kwargs):
        raise RuntimeError("LLM недоступна")

    with mock.patch.object(hybrid_coordinator, "call_llm", broken_llm):
        response = client.post("/api/assistant/ask",
                               json={"question": "Сколько потрачено?",
                                     "facts": FACTS})

    assert response.status_code == 502
    assert response.get_json()["answered"] is False


KNOW = [{"stage": "Электромонтаж", "kind": "документы",
         "text": "До оплаты этапа запрашивают акт скрытых работ и фотофиксацию трасс."},
        {"stage": "Стяжка пола", "kind": "порядок",
         "text": "Цементной стяжке нужно около четырёх недель до укладки покрытия."}]


def _with_knowledge(reply, fragments=KNOW):
    """Подменяем и поиск, и LLM: тесты не должны ходить в сеть."""
    return (mock.patch.object(knowledge, "search", lambda *a, **k: (fragments, "lexical")),
            mock.patch.object(hybrid_coordinator, "call_llm", _llm_returning(reply)))


def test_assistant_proposes_action_for_confirmation(client):
    reply = {"answered": True, "source_ids": [2],
             "answer": "Перед приёмкой запросите акт скрытых работ.",
             "proposed_action": {"title": "Запросить акт скрытых работ",
                                 "why": "без него состав работ не доказать"}}
    search_patch, llm_patch = _with_knowledge(reply)
    with search_patch, llm_patch:
        body = client.post("/api/assistant/ask",
                           json={"question": "Что перед приёмкой электрики?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is True
    assert body["proposed_action"]["title"] == "Запросить акт скрытых работ"
    assert body["proposed_action"]["status"] == "pending", (
        "действие остаётся предложением до подтверждения человеком")
    assert body["knowledge_used"] == ["Электромонтаж", "Стяжка пола"]


def test_assistant_allows_numbers_taken_from_knowledge(client):
    """Число из базы знаний — законный источник, а не выдумка."""
    fragments = [{"stage": "Стяжка пола", "kind": "порядок",
                  "text": "Цементной стяжке нужно около 28 дней до укладки покрытия."}]
    reply = {"answered": True, "source_ids": [1],
             "answer": "Плитку кладут через 28 дней после заливки стяжки.",
             "proposed_action": {"title": "", "why": ""}}

    search_patch, llm_patch = _with_knowledge(reply, fragments)
    with search_patch, llm_patch:
        body = client.post("/api/assistant/ask",
                           json={"question": "Когда класть плитку?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is True, "28 взято из знаний, это не выдуманное число"
    assert body["proposed_action"] is None, "пустой заголовок — действия нет"


def test_assistant_rejects_number_absent_from_both_sources(client):
    reply = {"answered": True, "source_ids": [1],
             "answer": "Готовность проекта 87 процентов.",
             "proposed_action": {"title": "", "why": ""}}
    search_patch, llm_patch = _with_knowledge(reply)
    with search_patch, llm_patch:
        body = client.post("/api/assistant/ask",
                           json={"question": "Какая готовность?",
                                 "facts": FACTS}).get_json()

    assert body["answered"] is False
    assert "87" in body["reason"]


def test_knowledge_lexical_fallback_finds_stage():
    found = knowledge._lexical("что проверить при приёмке электромонтажа",
                               knowledge.load_fragments())
    found.sort(key=lambda pair: pair[0], reverse=True)
    assert found, "запасной поиск обязан что-то находить"
    assert found[0][1]["stage"] == "Электромонтаж"
