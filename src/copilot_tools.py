from __future__ import annotations
import os
import re
import sys

import pandas as pd

sys.path.append(os.path.dirname(__file__))
from clean_prices import to_canonical

BASE = os.path.dirname(__file__)
MIN_SAMPLE = 5

_DF = pd.read_csv(os.path.join(BASE, "..", "data", "processed", "clean_prices.csv"))
_CORR = _DF.groupby("canonical_work")["price"].agg(
    p10=lambda s: s.quantile(0.10),
    p50="median",
    p90=lambda s: s.quantile(0.90),
    n="count",
)
_SOURCE = (f"рыночная база FRAME: {len(_DF)} цен, {_DF['source'].nunique()} компаний, "
           f"{_DF['region'].nunique()} городов")


def _num(x):
    x = re.sub(r"[^\d.,]", "", str(x)).replace(",", ".")
    try:
        return float(x)
    except ValueError:
        return None


def parse_estimate(text: str) -> dict:
    lines, errors = [], []
    for i, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        parts = [p.strip() for p in raw.split(";")]
        if len(parts) < 2:
            errors.append({"line": i, "reason": "меньше двух полей"})
            continue
        name = parts[0]
        qty = _num(parts[1]) if len(parts) >= 3 else 1.0
        price = _num(parts[2]) if len(parts) >= 3 else _num(parts[1])
        if not name or price is None or qty is None:
            errors.append({"line": i, "reason": "не удалось прочитать число"})
            continue
        work, category, _, _ = to_canonical(name)
        lines.append({
            "line": i,
            "raw_name": name,
            "canonical_work": work,
            "category": category,
            "quantity": qty,
            "unit_price": price,
            "amount": round(qty * price, 2),
            "recognized": work is not None,
        })
    return {"lines": lines, "errors": errors,
            "n_lines": len(lines), "n_recognized": sum(l["recognized"] for l in lines)}


def get_market_corridor(canonical_work: str) -> dict:
    if canonical_work not in _CORR.index:
        return {"status": "abstain",
                "reason": "работа отсутствует в рыночной базе FRAME",
                "canonical_work": canonical_work}
    row = _CORR.loc[canonical_work]
    if int(row.n) < MIN_SAMPLE:
        return {"status": "abstain",
                "reason": f"недостаточно наблюдений: {int(row.n)} < {MIN_SAMPLE}",
                "canonical_work": canonical_work, "sample_size": int(row.n)}
    return {"status": "ok",
            "canonical_work": canonical_work,
            "p10": round(float(row.p10), 2),
            "median": round(float(row.p50), 2),
            "p90": round(float(row.p90), 2),
            "sample_size": int(row.n),
            "source": _SOURCE}


def check_arithmetic(lines: list[dict], declared_total: float | None = None) -> dict:
    issues = []
    computed = 0.0
    for l in lines:
        expected = round(l["quantity"] * l["unit_price"], 2)
        if abs(expected - l.get("amount", expected)) > 0.01:
            issues.append({"line": l["line"], "kind": "line_mismatch",
                           "declared": l.get("amount"), "expected": expected})
        computed += expected

    seen = {}
    for l in lines:
        key = (l["canonical_work"], l["unit_price"]) if l["recognized"] else None
        if key is None:
            continue
        if key in seen:
            issues.append({"line": l["line"], "kind": "possible_duplicate",
                           "same_as_line": seen[key],
                           "work": l["canonical_work"]})
        else:
            seen[key] = l["line"]

    computed = round(computed, 2)
    if declared_total is not None and abs(declared_total - computed) > 0.01:
        issues.append({"kind": "total_mismatch",
                       "declared": declared_total, "expected": computed})
    return {"computed_total": computed, "declared_total": declared_total,
            "issues": issues, "n_issues": len(issues)}


def compare_versions(old_text: str, new_text: str) -> dict:
    old = {l["raw_name"]: l for l in parse_estimate(old_text)["lines"]}
    new = {l["raw_name"]: l for l in parse_estimate(new_text)["lines"]}

    added = [new[k] for k in new if k not in old]
    removed = [old[k] for k in old if k not in new]
    changed = []
    for k in new:
        if k not in old:
            continue
        o, n = old[k], new[k]
        if o["unit_price"] != n["unit_price"] or o["quantity"] != n["quantity"]:
            changed.append({
                "raw_name": k,
                "price_before": o["unit_price"], "price_after": n["unit_price"],
                "qty_before": o["quantity"], "qty_after": n["quantity"],
                "amount_delta": round(n["amount"] - o["amount"], 2),
            })

    total_before = round(sum(l["amount"] for l in old.values()), 2)
    total_after = round(sum(l["amount"] for l in new.values()), 2)
    return {"added": added, "removed": removed, "changed": changed,
            "total_before": total_before, "total_after": total_after,
            "total_delta": round(total_after - total_before, 2)}


def search_project_documents(query: str) -> dict:
    return {"status": "not_available",
            "reason": "корпус документов проекта (договор, ТЗ, приложения) "
                      "появляется только внутри платформы; вне её искать не в чем",
            "query": query,
            "roadmap_stage": 2}


def create_audit_report(text: str, declared_total: float | None = None) -> dict:
    parsed = parse_estimate(text)
    arith = check_arithmetic(parsed["lines"], declared_total)

    findings, checked, abstained = [], 0, 0
    quoted = fair = 0.0

    for l in parsed["lines"]:
        if not l["recognized"]:
            abstained += 1
            findings.append({
                "line": l["line"], "severity": "unknown",
                "claim": f"позиция «{l['raw_name']}» не распознана — оценка не даётся",
                "source": {"type": "abstention", "reason": "нет каноничной работы"},
            })
            continue

        corr = get_market_corridor(l["canonical_work"])
        if corr["status"] == "abstain":
            abstained += 1
            findings.append({
                "line": l["line"], "severity": "unknown",
                "claim": f"«{l['canonical_work']}»: {corr['reason']}",
                "source": {"type": "abstention", "reason": corr["reason"]},
            })
            continue

        checked += 1
        quoted += l["amount"]
        fair += corr["median"] * l["quantity"]
        deviation = (l["unit_price"] / corr["median"] - 1) * 100

        if l["unit_price"] > corr["p90"]:
            severity = "above_market"
        elif l["unit_price"] < corr["p10"]:
            severity = "below_market"
        else:
            severity = "within_market"

        findings.append({
            "line": l["line"], "severity": severity,
            "claim": (f"«{l['canonical_work']}» — {l['unit_price']:.0f} ₽ при рыночном "
                      f"коридоре {corr['p10']:.0f}–{corr['p90']:.0f} ₽ "
                      f"(отклонение от медианы {deviation:+.0f}%)"),
            "source": {"type": "market_base", "work": l["canonical_work"],
                       "sample_size": corr["sample_size"],
                       "reference": corr["source"]},
        })

    for issue in arith["issues"]:
        findings.append({
            "line": issue.get("line"), "severity": "arithmetic",
            "claim": f"арифметика: {issue['kind']}",
            "source": {"type": "deterministic_check", "detail": issue},
        })

    ungrounded = [f for f in findings if not f.get("source")]
    return {
        "summary": {
            "lines_total": parsed["n_lines"],
            "lines_checked": checked,
            "lines_abstained": abstained,
            "quoted_total_checked": round(quoted, 2),
            "fair_total_checked": round(fair, 2),
            "difference": round(quoted - fair, 2),
            "computed_total": arith["computed_total"],
        },
        "findings": findings,
        "grounding": {
            "n_findings": len(findings),
            "n_ungrounded": len(ungrounded),
            "all_grounded": not ungrounded,
        },
    }


TOOL_SPECS = [
    {
        "name": "parse_estimate",
        "description": "Разбирает текст сметы на позиции: работа, количество, цена, сумма.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        "guarantees": "Нераспознанные строки возвращаются в errors, а не угадываются.",
        "implemented": True,
    },
    {
        "name": "get_market_corridor",
        "description": "Возвращает рыночный коридор P10-P90 и размер выборки по работе.",
        "input_schema": {
            "type": "object",
            "properties": {"canonical_work": {"type": "string"}},
            "required": ["canonical_work"],
        },
        "guarantees": f"Отказ (abstain) при неизвестной работе или выборке < {MIN_SAMPLE}.",
        "implemented": True,
    },
    {
        "name": "check_arithmetic",
        "description": "Пересчитывает строки и итог, ищет дубли позиций.",
        "input_schema": {
            "type": "object",
            "properties": {"lines": {"type": "array"},
                           "declared_total": {"type": "number"}},
            "required": ["lines"],
        },
        "guarantees": "Только детерминированный код: LLM не выполняет денежную арифметику.",
        "implemented": True,
    },
    {
        "name": "compare_versions",
        "description": "Сравнивает две версии сметы: добавленные, удалённые и изменённые позиции.",
        "input_schema": {
            "type": "object",
            "properties": {"old_text": {"type": "string"},
                           "new_text": {"type": "string"}},
            "required": ["old_text", "new_text"],
        },
        "guarantees": "Разделяет добавленное, удалённое и изменённое, не смешивая.",
        "implemented": True,
    },
    {
        "name": "create_audit_report",
        "description": "Собирает аудит сметы: каждое утверждение связано с источником.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"},
                           "declared_total": {"type": "number"}},
            "required": ["text"],
        },
        "guarantees": "Каждый finding несёт поле source; grounding.all_grounded проверяем.",
        "implemented": True,
    },
    {
        "name": "search_project_documents",
        "description": "Ищет подтверждающий фрагмент в договоре, ТЗ и приложениях проекта.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "guarantees": "Ответ должен содержать document_id, страницу и цитату.",
        "implemented": False,
    },
]

TOOL_REGISTRY = {
    "parse_estimate": parse_estimate,
    "get_market_corridor": get_market_corridor,
    "check_arithmetic": check_arithmetic,
    "compare_versions": compare_versions,
    "create_audit_report": create_audit_report,
    "search_project_documents": search_project_documents,
}
