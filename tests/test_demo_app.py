import pytest
from unittest import mock

from demo_app import _num, analyze, analyze_chat, parse_chat, parse_line


@pytest.mark.parametrize("raw,expected", [
    ("3200", 3200.0),
    ("3 200", 3200.0),
    ("3200,50", 3200.5),
    ("1 234.56", 1234.56),
    ("abc", None),
    ("", None),
])
def test_num_parses_prices_with_spaces_and_commas(raw, expected):
    assert _num(raw) == expected


def test_parse_line_with_qty_and_price():
    assert parse_line("Укладка плитки на пол; 20; 3200") == ("Укладка плитки на пол", 20.0, 3200.0)


def test_parse_line_without_qty_defaults_to_one():
    assert parse_line("Поклейка обоев; 400") == ("Поклейка обоев", 1.0, 400.0)


def test_parse_line_rejects_single_field():
    assert parse_line("только название") is None


def test_parse_line_rejects_missing_price():
    assert parse_line("Название работы; 20; ") is None


def test_parse_line_rejects_empty_string():
    assert parse_line("") is None


def test_analyze_flags_price_above_market_corridor():
    # "Поклейка обоев" — распознанный вид работ с достаточным числом реальных
    # цен; 100000 руб/ед заведомо выше p90 по рынку.
    table, summary = analyze("Поклейка обоев; 1; 100000")
    assert "завышено" in table.iloc[0]["Вердикт"]
    assert "Распознано позиций: **1**" in summary


def test_analyze_accepts_price_within_market_corridor():
    table, summary = analyze("Поклейка обоев; 1; 400")
    assert "в норме" in table.iloc[0]["Вердикт"]


def test_analyze_flags_unrecognized_work_as_no_data():
    table, summary = analyze("Консультация дизайнера; 1; 5000")
    assert table.iloc[0]["Вердикт"] == "❔ нет данных"


def test_analyze_skips_blank_and_unparseable_lines():
    table, summary = analyze("\nтолько название\nПоклейка обоев; 1; 400\n")
    assert len(table) == 1


def test_parse_chat_assigns_ids_and_authors():
    messages = parse_chat("Заказчик: Когда закончите\nПрораб: До пятницы")
    assert [message["id"] for message in messages] == [1, 2]
    assert messages[0]["author"] == "Заказчик"
    assert messages[1]["text"] == "До пятницы"


def test_chat_demo_shows_grounded_card_and_mode():
    fake = {
        "mode": "LIVE_HYBRID",
        "events": [{
            "event_id": "event_1",
            "event_type": "budget_change",
            "title": "Доплата",
            "assignee": None,
            "deadline_text": None,
            "amount_rub": 12000.0,
            "amount_kind": "increase",
            "workflow_state": "approved",
            "source_message_ids": [1, 2],
            "suggested_actions": ["Согласовать сумму"],
            "detected_by": "rules+llm",
        }],
        "errors": [],
        "stats": {"candidates": 2},
        "elapsed_sec": 1.2,
    }
    text = "Прораб: Плюс 12 000 к смете\nЗаказчик: Согласен"
    with mock.patch("hybrid_coordinator.analyze_hybrid", return_value=fake):
        table, summary = analyze_chat(text)
    assert len(table) == 1
    assert "#1" in table.iloc[0]["Исходные сообщения"]
    assert "+12 000 ₽" in table.iloc[0]["Поля"]
    assert "GigaChat + правила" in summary
