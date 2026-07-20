import pytest

from demo_app import _num, analyze, parse_line


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
