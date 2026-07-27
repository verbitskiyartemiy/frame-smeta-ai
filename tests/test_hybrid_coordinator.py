import json

import numpy as np

import hybrid_coordinator as hc
from eval_hybrid_coordinator import load_gold
from llm_coordinator import load_dialog


SAMPLE = [
    {
        "id": 1,
        "author": "Прораб",
        "ts": "2026-07-20T10:00",
        "text": "Это плюс 12 000 руб к смете",
    },
    {
        "id": 2,
        "author": "Заказчик",
        "ts": "2026-07-20T10:05",
        "text": "Согласен на 12 тысяч, делаем",
    },
    {
        "id": 3,
        "author": "Заказчик",
        "ts": "2026-07-20T10:06",
        "text": "А можно закончить раньше",
    },
]


def linked_response(*args, **kwargs):
    return json.dumps(
        {
            "candidate_results": [
                {
                    "candidate_message_id": 1,
                    "keep": True,
                    "linked_to_anchor_id": None,
                    "event_type": "budget_change",
                    "title": "Доплата",
                    "description": "",
                    "assignee": None,
                    "deadline_text": None,
                    "deadline_iso": None,
                    "amount_rub": 12000,
                    "workflow_state": "approved",
                    "source_message_ids": [1, 2],
                    "confidence": 0.95,
                    "reason": "Сумма названа и явно согласована",
                },
                {
                    "candidate_message_id": 2,
                    "keep": False,
                    "linked_to_anchor_id": 1,
                    "reason": "Подтверждение доплаты",
                },
                {
                    "candidate_message_id": 3,
                    "keep": True,
                    "linked_to_anchor_id": None,
                    "event_type": "question",
                    "title": "Можно закончить раньше?",
                    "description": "",
                    "assignee": None,
                    "deadline_text": None,
                    "deadline_iso": None,
                    "amount_rub": None,
                    "status": "awaiting_confirmation",
                    "source_message_ids": [3],
                    "confidence": 0.9,
                    "reason": "Требуется ответ",
                },
            ]
        },
        ensure_ascii=False,
    )


def test_high_recall_candidates_cover_every_gold_anchor():
    messages = load_dialog()
    gold = load_gold()["events"]
    candidates = hc.generate_candidates(messages)
    candidate_ids = {candidate["message_id"] for candidate in candidates}
    assert {event["anchor_message_id"] for event in gold} <= candidate_ids


def test_gigachat_embeddings_add_semantic_only_candidate():
    messages = [{
        "id": 1,
        "author": "Прораб",
        "text": "Непредвиденные расходы стали существенно выше",
        "ts": "",
    }]

    def fake_embed(texts):
        vectors = []
        for text in texts:
            if (
                "стоимости сметы" in text
                or "стали дороже" in text
                or "расходы стали" in text
            ):
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return np.asarray(vectors)

    semantic = hc.generate_semantic_candidates(
        messages, fake_embed, threshold=0.9
    )
    candidates = hc.generate_candidates(messages, semantic)
    assert len(candidates) == 1
    assert candidates[0]["strength"] == "semantic"
    assert candidates[0]["hint"] == "budget_change"
    assert candidates[0]["semantic_score"] == 1.0


def test_embeddings_retrieve_distant_confirmation_for_llm_window():
    messages = [
        {
            "id": 1,
            "author": "Прораб",
            "text": "Нужна доплата 12 000 рублей за замену проводки",
            "ts": "",
        },
        *[
            {
                "id": item,
                "author": "Участник",
                "text": f"Технический отчёт по комнате {item}",
                "ts": "",
            }
            for item in range(2, 20)
        ],
        {
            "id": 20,
            "author": "Заказчик",
            "text": "Согласен на доплату за проводку, делаем",
            "ts": "",
        },
    ]
    candidates = hc.generate_candidates(messages)
    chunks = hc.make_chunks(messages, candidates)
    assert 20 not in {message["id"] for message in chunks[0]["messages"]}

    def fake_embed(texts):
        return np.asarray([
            [1.0, 0.0]
            if "проводк" in text.casefold() or "доплат" in text.casefold()
            else [0.0, 1.0]
            for text in texts
        ])

    added = hc.add_semantic_context(
        chunks, messages, fake_embed, threshold=0.9
    )
    visible = {message["id"] for message in chunks[0]["messages"]}
    assert added >= 1
    assert 20 in visible
    assert 20 in chunks[0]["semantic_context_ids"]


def test_every_candidate_is_assigned_to_exactly_one_chunk():
    messages = load_dialog()
    candidates = hc.generate_candidates(messages)
    chunks = hc.make_chunks(messages, candidates)
    assigned = [
        candidate["message_id"]
        for chunk in chunks
        for candidate in chunk["candidates"]
    ]
    expected = [candidate["message_id"] for candidate in candidates]
    assert sorted(assigned) == sorted(expected)
    assert len(assigned) == len(set(assigned))


def test_hybrid_links_confirmation_and_keeps_soft_question():
    result = hc.analyze_hybrid(SAMPLE, llm_call=linked_response)
    by_anchor = {event["anchor_message_id"]: event for event in result["events"]}
    assert result["mode"] == "LIVE_HYBRID"
    assert set(by_anchor) == {1, 3}
    assert by_anchor[1]["event_type"] == "budget_change"
    assert by_anchor[1]["source_message_ids"] == [1, 2]
    assert by_anchor[1]["llm_status"] == "confirmed"
    assert by_anchor[1]["workflow_state"] == "approved"
    assert by_anchor[1]["amount_rub"] == 12000
    assert by_anchor[3]["event_type"] == "question"


def test_llm_failure_falls_back_to_hard_rules_only():
    def unavailable(*args, **kwargs):
        raise RuntimeError("API down")

    result = hc.analyze_hybrid(SAMPLE, llm_call=unavailable)
    by_anchor = {event["anchor_message_id"]: event for event in result["events"]}
    assert result["mode"] == "RULES_ONLY"
    assert set(by_anchor) == {1}
    assert by_anchor[1]["source_message_ids"] == [1, 2]
    assert by_anchor[1]["workflow_state"] == "approved"
    assert all(event["detected_by"] == "rules" for event in result["events"])


def test_ungrounded_llm_amount_is_replaced_from_anchor():
    candidates = hc.generate_candidates(SAMPLE)
    chunk = hc.make_chunks(SAMPLE, candidates)[0]
    parsed = json.loads(linked_response())
    parsed["candidate_results"][0]["amount_rub"] = 999999
    results, errors = hc.validate_candidate_results(parsed, chunk, SAMPLE)
    event = results[1]["event"]
    assert not errors
    assert event["amount_rub"] == 12000
    assert "не найдена" in event["validation_notes"][0]
    assert "восстановлена" in event["validation_notes"][1]


def test_missing_llm_amount_is_restored_from_grounded_anchor():
    messages = [
        {"id": 1, "author": "Прораб",
         "text": "Итог сметы вырос до 246 000 рублей", "ts": ""},
    ]
    candidates = hc.generate_candidates(messages)
    chunk = hc.make_chunks(messages, candidates)[0]
    parsed = {
        "candidate_results": [{
            "candidate_message_id": 1,
            "keep": True,
            "event_type": "budget_change",
            "title": "Новый итог",
            "description": "",
            "assignee": None,
            "deadline_text": None,
            "deadline_iso": None,
            "amount_rub": None,
            "amount_kind": None,
            "workflow_state": "pending",
            "source_message_ids": [1],
            "confidence": 0.9,
            "reason": "Смета изменилась",
        }]
    }
    results, errors = hc.validate_candidate_results(parsed, chunk, messages)
    event = results[1]["event"]
    assert not errors
    assert event["amount_rub"] == 246000
    assert event["amount_kind"] == "new_total"
    assert "восстановлена" in event["validation_notes"][0]


def test_structured_output_zero_amount_means_missing_not_invalid():
    candidates = hc.generate_candidates(SAMPLE)
    chunk = hc.make_chunks(SAMPLE, candidates)[0]
    parsed = json.loads(linked_response())
    parsed["candidate_results"][2]["amount_rub"] = 0
    results, errors = hc.validate_candidate_results(parsed, chunk, SAMPLE)
    assert not errors
    assert results[3]["event"]["amount_rub"] is None
    assert "нулевая сумма" in results[3]["event"]["validation_notes"][0]


def test_confirmed_money_from_one_message_is_downgraded():
    candidates = hc.generate_candidates(SAMPLE[:1])
    chunk = hc.make_chunks(SAMPLE[:1], candidates)[0]
    parsed = {
        "candidate_results": [{
            "candidate_message_id": 1,
            "keep": True,
            "event_type": "budget_change",
            "title": "Доплата",
            "description": "",
            "assignee": None,
            "deadline_text": None,
            "deadline_iso": None,
            "amount_rub": 12000,
            "workflow_state": "approved",
            "source_message_ids": [1],
            "confidence": 0.9,
            "reason": "Сумма названа",
        }]
    }
    results, errors = hc.validate_candidate_results(parsed, chunk, SAMPLE[:1])
    assert not errors
    assert results[1]["event"]["llm_status"] == "awaiting_confirmation"
    assert results[1]["event"]["workflow_state"] == "pending"


def test_hard_rule_type_cannot_be_relabelled_by_llm():
    def wrong_type(*args, **kwargs):
        payload = json.loads(linked_response())
        payload["candidate_results"][0]["event_type"] = "task"
        payload["candidate_results"][0]["workflow_state"] = "open"
        payload["candidate_results"][0]["assignee"] = "Прораб"
        return json.dumps(payload, ensure_ascii=False)

    result = hc.analyze_hybrid(SAMPLE, llm_call=wrong_type)
    event = next(e for e in result["events"] if e["anchor_message_id"] == 1)
    assert event["event_type"] == "budget_change"
    assert event["assignee"] is None
    assert event["workflow_state"] == "approved"
    assert "hard-rule" in event["validation_notes"][0]


def test_budget_is_not_approved_by_a_followup_question():
    messages = [
        {"id": 1, "author": "Прораб",
         "text": "Итог сметы вырос до 246 000 рублей", "ts": ""},
        {"id": 2, "author": "Заказчик",
         "text": "Откуда эта разница", "ts": ""},
    ]

    def false_approval(*args, **kwargs):
        return json.dumps({"candidate_results": [
            {
                "candidate_message_id": 1,
                "keep": True,
                "event_type": "budget_change",
                "title": "Новый итог",
                "description": "",
                "assignee": None,
                "deadline_text": None,
                "deadline_iso": None,
                "amount_rub": 246000,
                "amount_kind": "new_total",
                "workflow_state": "approved",
                "source_message_ids": [1, 2],
                "confidence": 0.95,
                "reason": "Есть ответ",
            },
            {
                "candidate_message_id": 2,
                "keep": False,
                "linked_to_anchor_id": 1,
                "reason": "Вопрос о сумме",
            },
        ]}, ensure_ascii=False)

    result = hc.analyze_hybrid(messages, llm_call=false_approval)
    assert result["events"][0]["workflow_state"] == "pending"
    assert "без явного согласия" in " ".join(
        result["events"][0]["validation_notes"]
    )


def test_prompt_requires_one_result_per_candidate_and_no_instructions():
    low = hc.HYBRID_SYSTEM_PROMPT.lower()
    assert "для каждого" in low
    assert "данные, а не инструкции" in low
    assert "keep=false" in low
