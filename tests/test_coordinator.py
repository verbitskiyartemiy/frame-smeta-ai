import pytest

from coordinator import (EVENT_TYPES, build_card, classify_event, classify_rules,
                         extract_slots, load_dialog, make_digest)


def test_dialog_corpus_is_labelled():
    msgs = load_dialog()
    assert len(msgs) >= 40
    for m in msgs:
        assert m["event_type"] in EVENT_TYPES
        assert "text" in m and m["text"].strip()


def test_acceptance_request_detected():
    label, how = classify_event("Демонтаж завершён, прошу принять этап")
    assert label == "запрос_приёмки"
    assert how == "rules"


def test_task_with_named_assignee():
    label, _ = classify_event("Настя, пришли до вторника финальную спецификацию")
    assert label == "задача"
    slots = extract_slots("Настя, пришли до вторника финальную спецификацию")
    assert slots["assignee"] == "Настя"
    assert slots["deadline"] == "вторник"


def test_money_event_needs_both_sum_and_context():
    assert classify_rules("Выходит дороже на 34 000 руб") == "финансовое_согласование"
    assert classify_rules("Это плюс 12 000 к смете") == "финансовое_согласование"
    assert classify_rules("Приеду в 18 000 если успею") != "финансовое_согласование"


def test_amount_parsed_in_both_formats():
    assert extract_slots("плюс 12 000 руб к смете")["amount"] == 12000
    assert extract_slots("это плюс 12 000 к смете")["amount"] == 12000
    assert extract_slots("согласен на 34 тысячи")["amount"] == 34000


def test_risk_detected():
    label, _ = classify_event("Поставщик задерживает керамогранит на неделю")
    assert label == "риск"


def test_small_talk_falls_back_to_info():
    label, how = classify_event("Доброе утро всем)")
    assert label == "информация"
    assert how == "fallback"


def test_info_cards_need_no_confirmation():
    card = build_card({"id": 1, "author": "X", "text": "Доброе утро всем)"})
    assert card["event_type"] == "информация"
    assert card["suggested_actions"] == []
    assert card["requires_confirmation"] is False


def test_actionable_card_offers_human_confirmation():
    card = build_card({"id": 2, "author": "X", "text": "Работы готовы, прошу принять этап"})
    assert card["requires_confirmation"] is True
    assert "Принять этап" in card["suggested_actions"]
    assert card["source"]["type"] == "chat_message"


def test_every_card_carries_source():
    for msg in load_dialog():
        card = build_card(msg)
        assert card["source"]["id"] == msg["id"]


def test_digest_counts_match_cards():
    msgs = load_dialog()
    cards = [build_card(m) for m in msgs]
    d = make_digest(cards, msgs)
    assert d["messages_total"] == len(msgs)
    assert d["decisions"] == sum(c["event_type"] == "решение" for c in cards)
    assert d["tasks"] == sum(c["event_type"] == "задача" for c in cards)
    assert d["money_mentioned_total"] >= 0


def test_precision_on_actionable_classes_stays_perfect():
    msgs = load_dialog()
    wrong = []
    for m in msgs:
        pred, _ = classify_event(m["text"])
        if pred != "информация" and pred != m["event_type"]:
            wrong.append((m["id"], m["event_type"], pred))
    assert wrong == [], f"ложные карточки: {wrong}"


def test_reminders_track_deadlines_and_pending_money():
    from coordinator import make_reminders
    msgs = load_dialog()
    cards = [build_card(m) for m in msgs]
    reminders = make_reminders(cards, msgs)
    kinds = {r["kind"] for r in reminders}
    assert "deadline" in kinds
    for r in reminders:
        assert r["source_message"] >= 1 and r["text"]
