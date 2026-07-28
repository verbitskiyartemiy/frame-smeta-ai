"""Оценка координатора на большом синтетическом корпусе.

Метрика та же, что на исходных 45 сообщениях (eval_hybrid_coordinator.evaluate),
поэтому числа сопоставимы напрямую. Меняется только объём и то, что разметка
здесь получена из спецификации, а не написана вручную автором.

Отдельно считается доля ложных карточек на диалогах без событий: на маленьком
корпусе такой проверки не было вовсе.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.append(os.path.dirname(__file__))

import hybrid_coordinator
from eval_hybrid_coordinator import build_rule_baseline, evaluate
from llm_coordinator import load_env

BASE = os.path.dirname(__file__)
CORPUS_PATH = os.path.abspath(
    os.path.join(BASE, "..", "data", "demo", "chat_corpus_generated.json"))
REPORT_PATH = os.path.abspath(
    os.path.join(BASE, "..", "reports", "corpus_eval.json"))
CACHE_PATH = os.path.abspath(
    os.path.join(BASE, "..", "data", "processed", "corpus_predictions.json"))
PROJECT = "Квартира, ремонт под ключ"

# Корпус задаёт только эти два типа событий. Задачи, вопросы и риски в нём не
# размечены — обычная рабочая переписка полна и того, и другого, — поэтому
# предсказания таких типов не засчитываются ни в плюс, ни в минус.
MEASURED_TYPES = {"budget_change", "acceptance_request"}


def only_measured(events: list[dict]) -> list[dict]:
    return [e for e in events if e.get("event_type") in MEASURED_TYPES]


def totals() -> dict:
    return {"tp": 0, "fp": 0, "fn": 0,
            "linkage_support": 0, "linkage_exact": 0,
            "state_support": 0, "state_correct": 0,
            "amount_support": 0, "amount_correct": 0,
            "grounded": 0, "events": 0,
            "quiet_dialogs": 0, "quiet_false_cards": 0}


def accumulate(acc: dict, metrics: dict, events: list[dict], quiet: bool) -> None:
    detection = metrics["event_detection"]
    acc["tp"] += detection["tp"]
    acc["fp"] += detection["fp"]
    acc["fn"] += detection["fn"]

    linkage = metrics["multi_message_linkage"]
    acc["linkage_support"] += linkage["support"]
    acc["linkage_exact"] += linkage["exact_source_sets"]

    state = metrics["workflow_state"]
    acc["state_support"] += state["support"]
    acc["state_correct"] += state["correct"]

    amount = metrics.get("amount", {})
    acc["amount_support"] += amount.get("support", 0)
    acc["amount_correct"] += amount.get("correct", 0)

    acc["events"] += len(events)
    acc["grounded"] += sum(1 for e in events if e.get("source_message_ids"))

    if quiet:
        acc["quiet_dialogs"] += 1
        acc["quiet_false_cards"] += len(events)


def summarise(acc: dict) -> dict:
    tp, fp, fn = acc["tp"], acc["fp"], acc["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "event_detection": {"precision": round(precision, 3),
                            "recall": round(recall, 3),
                            "f1": round(f1, 3), "tp": tp, "fp": fp, "fn": fn},
        "multi_message_linkage": {
            "support": acc["linkage_support"],
            "exact": acc["linkage_exact"],
            "accuracy": round(acc["linkage_exact"] / acc["linkage_support"], 3)
            if acc["linkage_support"] else None},
        "workflow_state": {
            "support": acc["state_support"], "correct": acc["state_correct"],
            "accuracy": round(acc["state_correct"] / acc["state_support"], 3)
            if acc["state_support"] else None},
        "amount": {
            "support": acc["amount_support"], "correct": acc["amount_correct"],
            "accuracy": round(acc["amount_correct"] / acc["amount_support"], 3)
            if acc["amount_support"] else None},
        "source_grounding_rate": round(acc["grounded"] / acc["events"], 3)
        if acc["events"] else None,
        "quiet": {
            "dialogs": acc["quiet_dialogs"],
            "false_cards": acc["quiet_false_cards"],
            "cards_per_dialog": round(
                acc["quiet_false_cards"] / acc["quiet_dialogs"], 2)
            if acc["quiet_dialogs"] else None},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--refresh", action="store_true",
                        help="прогнать заново, а не пересчитать по кэшу")
    args = parser.parse_args()

    load_env()
    with open(CORPUS_PATH, encoding="utf-8") as fh:
        corpus = json.load(fh)
    dialogs = corpus["dialogs"][:args.limit] if args.limit else corpus["dialogs"]

    cache = {}
    if not args.refresh and os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as fh:
            cache = json.load(fh)
        print(f"Использую сохранённые прогоны: {len(cache)} диалогов\n")

    hybrid_acc, rules_acc = totals(), totals()
    started = time.time()
    failures = []

    print(f"{'диалог':10s} {'тип':20s} {'сообщ':>6s} {'событий':>8s} {'сек':>6s}",
          flush=True)
    for dialog in dialogs:
        messages = dialog["messages"]
        gold = dialog["events"]
        quiet = dialog["kind"] == "quiet"
        began = time.time()

        if dialog["id"] in cache:
            events = cache[dialog["id"]]
        else:
            try:
                result = hybrid_coordinator.analyze_hybrid(
                    messages, project=PROJECT, use_embeddings=True,
                    llm_call=hybrid_coordinator.call_llm)
                events = result["events"]
                cache[dialog["id"]] = events
            except Exception as exc:
                failures.append({"id": dialog["id"], "reason": str(exc)[:120]})
                continue

        events = only_measured(events)
        rules = only_measured(build_rule_baseline(messages))
        accumulate(hybrid_acc, evaluate(events, gold, messages), events, quiet)
        accumulate(rules_acc, evaluate(rules, gold, messages), rules, quiet)

        print(f"{dialog['id']:10s} {dialog['kind']:20s} {len(messages):>6d} "
              f"{len(events):>8d} {time.time() - began:>6.1f}", flush=True)

    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False)

    report = {
        "measured_types": sorted(MEASURED_TYPES),
        "scoring_note": "Задачи, вопросы и риски корпус не размечает, поэтому "
                        "предсказания этих типов исключены из подсчёта.",
        "not_valid_on_this_corpus": {
            "metrics": ["multi_message_linkage", "workflow_state"],
            "why": "Фраза согласия стоит на позиции из спецификации, но между "
                   "ней и суммой генератор успевает вставить другие темы. "
                   "«Ок, утверждаю план на завтра» размечено как согласие на "
                   "доплату, хотя относится к графику. Ручная проверка примеров "
                   "показала, что пайплайн в этих случаях прав, а разметка нет. "
                   "Числа по этим двум метрикам не заявляем.",
        },
        "corpus": {
            "dialogs": len(dialogs),
            "messages": sum(len(d["messages"]) for d in dialogs),
            "events": sum(len(d["events"]) for d in dialogs),
            "annotation": corpus["metadata"]["annotation"],
            "warning": corpus["metadata"]["warning"],
        },
        "hybrid": summarise(hybrid_acc),
        "rules": summarise(rules_acc),
        "elapsed_sec": round(time.time() - started, 1),
        "failures": failures,
    }

    print("\n" + "=" * 66)
    print(f"{'метрика':32s} {'правила':>14s} {'гибрид':>14s}")
    print("-" * 66)
    rows = [
        ("детекция событий, F1", "event_detection", "f1"),
        ("  precision", "event_detection", "precision"),
        ("  recall", "event_detection", "recall"),
        ("связывание реплик", "multi_message_linkage", "accuracy"),
        ("статус согласования", "workflow_state", "accuracy"),
        ("сумма изменения", "amount", "accuracy"),
        ("доля событий с источником", "source_grounding_rate", None),
        ("ложных карточек на тихий диалог", "quiet", "cards_per_dialog"),
    ]
    for label, group, key in rows:
        def cell(block):
            value = block[group] if key is None else block[group][key]
            return "—" if value is None else f"{value:.3f}"
        print(f"{label:32s} {cell(report['rules']):>14s} {cell(report['hybrid']):>14s}")

    print(f"\nдиалогов {report['corpus']['dialogs']}, "
          f"сообщений {report['corpus']['messages']}, "
          f"событий {report['corpus']['events']}, "
          f"{report['elapsed_sec']} c")
    if failures:
        print(f"сбоев анализа: {len(failures)}")

    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"Отчёт: {os.path.relpath(REPORT_PATH, BASE)}")


if __name__ == "__main__":
    main()
