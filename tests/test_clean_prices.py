import pytest

from clean_prices import RULES, to_canonical


@pytest.mark.parametrize("raw_name,expected_work,expected_category", [
    ("Демонтаж старых обоев", "Демонтаж обоев", "Демонтаж"),
    ("Штукатурка стен по маякам", "Штукатурка стен", "Стены"),
    ("Поклейка обоев", "Поклейка обоев", "Стены"),
    ("Укладка плитки на пол", "Плитка на пол", "Пол"),
    ("Устройство стяжки пола", "Стяжка пола", "Пол"),
    ("Монтаж натяжного потолка", "Натяжной потолок", "Потолок"),
    ("Монтаж розеток и выключателей", "Монтаж розеток", "Электрика"),
    ("Установка унитаза", "Установка унитаза", "Сантехника"),
    ("Установка межкомнатной двери", "Межкомнатная дверь", "Двери"),
])
def test_to_canonical_matches_known_work_types(raw_name, expected_work, expected_category):
    work, category, lo, hi = to_canonical(raw_name)
    assert work == expected_work
    assert category == expected_category
    assert lo < hi


@pytest.mark.parametrize("raw_name", [
    "проектная документация",
    "консультация дизайнера",
    "вывоз строительного мусора",
    "доставка материалов на объект",
    "",
])
def test_to_canonical_returns_none_for_unrecognized_work(raw_name):
    assert to_canonical(raw_name) == (None, None, None, None)


def test_to_canonical_is_case_insensitive():
    assert to_canonical("ШТУКАТУРКА СТЕН")[0] == to_canonical("штукатурка стен")[0]


def test_all_rule_corridors_are_positive_and_ordered():
    # Каждое правило задаёт правдоподобный ценовой коридор (lo < hi, lo > 0) —
    # это используется clean_prices.main() для фильтрации мис-извлечений regex'а.
    for pattern, work, category, lo, hi in RULES:
        assert lo > 0, f"{work}: нижняя граница коридора должна быть положительной"
        assert hi > lo, f"{work}: верхняя граница коридора должна превышать нижнюю"


def test_rule_order_matters_for_overlapping_keywords():
    # "штукатурка потолка" должна матчиться правилом потолка, а не более общим
    # правилом "штукатурка стен" — порядок правил в списке критичен.
    work, category, _, _ = to_canonical("штукатурка потолка")
    assert work == "Штукатурка потолка"
    assert category == "Потолок"
