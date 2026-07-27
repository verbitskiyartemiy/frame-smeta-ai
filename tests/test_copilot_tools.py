import pytest

from copilot_tools import (TOOL_REGISTRY, TOOL_SPECS, check_arithmetic,
                           compare_versions, create_audit_report,
                           get_market_corridor, parse_estimate,
                           search_project_documents)

SMETA = """Укладка плитки на пол; 20; 3200
Штукатурка стен по маякам; 45; 520
Поклейка обоев; 60; 400"""


def test_parse_reads_all_lines():
    out = parse_estimate(SMETA)
    assert out["n_lines"] == 3
    assert out["n_recognized"] == 3
    assert out["lines"][0]["quantity"] == 20
    assert out["lines"][0]["amount"] == 64000


def test_parse_reports_bad_line_instead_of_guessing():
    out = parse_estimate("Просто текст без цены")
    assert out["n_lines"] == 0
    assert out["errors"] and out["errors"][0]["reason"]


def test_corridor_abstains_on_unknown_work():
    out = get_market_corridor("Монтаж телепорта")
    assert out["status"] == "abstain"
    assert "reason" in out


def test_corridor_returns_sample_size_and_source():
    out = get_market_corridor("Плитка на пол")
    assert out["status"] == "ok"
    assert out["p10"] < out["median"] < out["p90"]
    assert out["sample_size"] >= 5
    assert out["source"]


def test_arithmetic_catches_wrong_total():
    lines = parse_estimate(SMETA)["lines"]
    out = check_arithmetic(lines, declared_total=1.0)
    kinds = [i["kind"] for i in out["issues"]]
    assert "total_mismatch" in kinds
    assert out["computed_total"] == pytest.approx(64000 + 23400 + 24000)


def test_arithmetic_accepts_correct_total():
    lines = parse_estimate(SMETA)["lines"]
    total = sum(l["amount"] for l in lines)
    out = check_arithmetic(lines, declared_total=total)
    assert [i for i in out["issues"] if i["kind"] == "total_mismatch"] == []


def test_arithmetic_flags_duplicate_position():
    lines = parse_estimate(SMETA + "\nУкладка плитки на пол; 20; 3200")["lines"]
    out = check_arithmetic(lines)
    assert any(i["kind"] == "possible_duplicate" for i in out["issues"])


def test_compare_versions_splits_change_types():
    new = SMETA.replace("3200", "3900") + "\nНатяжной потолок; 30; 1900"
    out = compare_versions(SMETA, new)
    assert len(out["added"]) == 1
    assert len(out["changed"]) == 1
    assert out["changed"][0]["price_after"] == 3900
    assert out["total_delta"] > 0


def test_audit_grounds_every_finding():
    out = create_audit_report(SMETA)
    assert out["findings"]
    assert out["grounding"]["all_grounded"]
    for f in out["findings"]:
        assert f["source"]


def test_audit_abstains_instead_of_inventing():
    out = create_audit_report("Монтаж телепорта; 1; 999999")
    assert out["summary"]["lines_checked"] == 0
    assert out["summary"]["lines_abstained"] == 1
    assert out["findings"][0]["severity"] == "unknown"


def test_audit_flags_above_market_price():
    out = create_audit_report("Укладка плитки на пол; 20; 3200")
    assert out["findings"][0]["severity"] == "above_market"
    assert out["findings"][0]["source"]["type"] == "market_base"


def test_document_search_declares_itself_unavailable():
    out = search_project_documents("гарантийные обязательства")
    assert out["status"] == "not_available"
    assert out["roadmap_stage"] == 2


def test_every_spec_has_registry_entry_and_guarantee():
    for spec in TOOL_SPECS:
        assert spec["name"] in TOOL_REGISTRY
        assert spec["guarantees"]
        assert "input_schema" in spec
    assert len(TOOL_SPECS) == len(TOOL_REGISTRY)


def test_unimplemented_tools_are_declared_honestly():
    unimplemented = [s["name"] for s in TOOL_SPECS if not s["implemented"]]
    assert unimplemented == ["search_project_documents"]
