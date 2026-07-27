import json
from unittest import mock

import pytest

import llm_coordinator as lc

MSGS = [
    {"id": 1, "author": "Прораб", "ts": "2026-07-20T09:00", "text": "Выходим на объект"},
    {"id": 2, "author": "Мастер", "ts": "2026-07-20T14:00", "text": "Плюс 12 000 руб к смете"},
    {"id": 3, "author": "Заказчик", "ts": "2026-07-20T15:00", "text": "Тогда меняем конечно"},
]


def ev(**over):
    base = {
        "event_id": "event_1", "event_type": "budget_change",
        "title": "Замена проводки", "description": "Доп. работы",
        "assignee": None, "deadline_text": None, "deadline_iso": None,
        "amount_rub": 12000, "status": "awaiting_confirmation",
        "source_message_ids": [2], "confidence": 0.9, "reason": "явно указана сумма",
    }
    base.update(over)
    return base


def parse(events):
    return {"events": events}


def test_valid_event_passes():
    events, errors = lc.validate_events(parse([ev()]), MSGS)
    assert len(events) == 1 and not errors
    assert events[0]["user_status"] == "pending"
    assert events[0]["suggested_actions"]


def test_broken_json_is_handled():
    with pytest.raises(ValueError):
        lc.extract_json("это не json вообще")


def test_json_in_markdown_fence_is_extracted():
    raw = '```json\n{"events": []}\n```'
    assert lc.extract_json(raw) == {"events": []}


def test_unknown_event_type_rejected():
    events, errors = lc.validate_events(parse([ev(event_type="потоп")]), MSGS)
    assert not events and "event_type" in errors[0]["reason"]


def test_nonexistent_source_id_rejected():
    events, errors = lc.validate_events(parse([ev(source_message_ids=[999])]), MSGS)
    assert not events and "несуществующ" in errors[0]["reason"]


def test_empty_source_ids_rejected():
    events, errors = lc.validate_events(parse([ev(source_message_ids=[])]), MSGS)
    assert not events and "source_message_ids" in errors[0]["reason"]


def test_negative_amount_rejected():
    events, errors = lc.validate_events(parse([ev(amount_rub=-5)]), MSGS)
    assert not events and "amount_rub" in errors[0]["reason"]


def test_confidence_out_of_range_rejected():
    events, errors = lc.validate_events(parse([ev(confidence=1.7)]), MSGS)
    assert not events and "confidence" in errors[0]["reason"]


def test_invalid_status_rejected():
    events, errors = lc.validate_events(parse([ev(status="уже оплачено")]), MSGS)
    assert not events and "status" in errors[0]["reason"]


def test_missing_events_key_reported():
    events, errors = lc.validate_events({"result": []}, MSGS)
    assert not events and errors


def test_one_bad_event_does_not_kill_the_good_one():
    events, errors = lc.validate_events(
        parse([ev(), ev(event_id="event_2", source_message_ids=[404])]), MSGS)
    assert len(events) == 1 and len(errors) == 1


def test_llm_cannot_mark_action_done_only_propose():
    events, _ = lc.validate_events(parse([ev(status="confirmed")]), MSGS)
    assert events[0]["llm_status"] == "confirmed"
    assert events[0]["user_status"] == "pending"


def test_no_reminder_before_human_confirmation():
    events, _ = lc.validate_events(parse([ev(status="confirmed")]), MSGS)
    assert lc.make_reminders(events) == []


def test_reminder_appears_after_human_confirmation():
    events, _ = lc.validate_events(parse([ev(status="confirmed")]), MSGS)
    lc.confirm(events, "event_1", "confirmed")
    reminders = lc.make_reminders(events)
    assert len(reminders) == 1
    assert reminders[0]["kind"] == "budget_approved"
    assert reminders[0]["source_message_ids"] == [2]


def test_rejected_event_produces_no_reminder():
    events, _ = lc.validate_events(parse([ev(status="confirmed")]), MSGS)
    lc.confirm(events, "event_1", "rejected")
    assert lc.make_reminders(events) == []


def test_confirm_rejects_unknown_decision():
    events, _ = lc.validate_events(parse([ev()]), MSGS)
    with pytest.raises(ValueError):
        lc.confirm(events, "event_1", "оплачено")


def test_pending_money_lists_unapproved_only():
    events, _ = lc.validate_events(
        parse([ev(), ev(event_id="event_2", amount_rub=5000, status="confirmed")]), MSGS)
    pending = lc.pending_money(events)
    assert [e["amount_rub"] for e in pending] == [12000.0]


def test_analyze_uses_mocked_api_and_reports_live():
    payload = json.dumps(parse([ev()]), ensure_ascii=False)
    with mock.patch.object(lc, "call_llm", return_value=payload) as m:
        res = lc.analyze(MSGS, allow_cached=False)
    assert m.called
    assert res["mode"] == "LIVE"
    assert len(res["events"]) == 1


def test_analyze_falls_back_to_cache_and_labels_it():
    with mock.patch.object(lc, "call_llm", side_effect=lc.LLMUnavailable("нет ключа")):
        res = lc.analyze(MSGS, allow_cached=True)
    assert res["mode"] == "CACHED"
    assert res["note"], "режим CACHED обязан объяснять, почему живой вызов не удался"


def test_cached_is_never_passed_off_as_live():
    with mock.patch.object(lc, "call_llm", side_effect=lc.LLMUnavailable("нет ключа")):
        with pytest.raises(lc.LLMUnavailable):
            lc.analyze(MSGS, allow_cached=False)


def test_garbage_model_output_creates_no_events():
    with mock.patch.object(lc, "call_llm", return_value="извините, не понял запрос"):
        res = lc.analyze(MSGS, allow_cached=False)
    assert res["events"] == []
    assert res["errors"]


def test_prompt_forbids_following_instructions_from_messages():
    assert "не выполняй" in lc.SYSTEM_PROMPT.lower()
    assert "данные" in lc.SYSTEM_PROMPT.lower()


def test_user_content_contains_every_message_id():
    content = lc.build_user_content(MSGS)
    for m in MSGS:
        assert f"[id={m['id']}]" in content


def test_cached_demo_file_is_marked_as_demo():
    with open(lc.CACHED, encoding="utf-8") as f:
        cache = json.load(f)
    assert "raw_response" in cache
    assert "демонстрационный" in cache["note"].lower()
