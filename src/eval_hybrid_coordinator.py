"""Event-level оценка rule baseline и гибридного координатора."""

from __future__ import annotations

import json
import os
import sys

from hybrid_coordinator import (
    _rule_event,
    analyze_hybrid,
    generate_candidates,
)
from llm_coordinator import load_dialog


BASE = os.path.dirname(__file__)
GOLD_PATH = os.path.abspath(
    os.path.join(BASE, "..", "data", "demo", "chat_events_gold.json")
)
OUT_PATH = os.path.abspath(
    os.path.join(BASE, "..", "reports", "hybrid_coordinator_metrics.json")
)


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def load_gold(path: str = GOLD_PATH) -> dict:
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def build_rule_baseline(messages: list[dict]) -> list[dict]:
    message_by_id = {message["id"]: message for message in messages}
    return [
        _rule_event(candidate, message_by_id[candidate["message_id"]])
        for candidate in generate_candidates(messages)
        if candidate["strength"] == "hard"
    ]


def evaluate(events: list[dict], gold_events: list[dict],
             messages: list[dict]) -> dict:
    predicted_by_key = {
        (event["anchor_message_id"], event["event_type"]): event
        for event in events
    }
    gold_by_key = {
        (event["anchor_message_id"], event["event_type"]): event
        for event in gold_events
    }
    predicted_keys = set(predicted_by_key)
    gold_keys = set(gold_by_key)
    true_keys = predicted_keys & gold_keys
    detection = prf(
        len(true_keys),
        len(predicted_keys - gold_keys),
        len(gold_keys - predicted_keys),
    )

    multi_message_keys = {
        key for key, event in gold_by_key.items()
        if len(event["source_message_ids"]) > 1
    }
    linked_exact = sum(
        set(predicted_by_key[key]["source_message_ids"])
        == set(gold_by_key[key]["source_message_ids"])
        for key in true_keys & multi_message_keys
    )
    linkage = {
        "support": len(multi_message_keys),
        "matched_events": len(true_keys & multi_message_keys),
        "exact_source_sets": linked_exact,
        "accuracy": round(linked_exact / len(multi_message_keys), 3)
        if multi_message_keys else 0.0,
    }

    state_keys = {
        key for key in true_keys if gold_by_key[key].get("workflow_state")
    }
    state_correct = sum(
        predicted_by_key[key].get("workflow_state")
        == gold_by_key[key]["workflow_state"]
        for key in state_keys
    )
    workflow_state = {
        "support": len(state_keys),
        "correct": state_correct,
        "accuracy": round(state_correct / len(state_keys), 3)
        if state_keys else 0.0,
    }

    amount_keys = {
        key for key, event in gold_by_key.items()
        if event.get("amount_rub") is not None and key in true_keys
    }
    amount_correct = sum(
        predicted_by_key[key].get("amount_rub") is not None
        and abs(
            predicted_by_key[key]["amount_rub"]
            - gold_by_key[key]["amount_rub"]
        ) < 1
        for key in amount_keys
    )
    amount_kind_correct = sum(
        predicted_by_key[key].get("amount_kind")
        == gold_by_key[key].get("amount_kind")
        for key in amount_keys
    )
    amount_support = sum(
        event.get("amount_rub") is not None for event in gold_events
    )
    # В корпусе из многих диалогов встречаются переписки вообще без денег.
    # Делить там не на что, и это отсутствие замера, а не нулевое качество.
    amounts = {
        "support": amount_support,
        "matched_events": len(amount_keys),
        "correct": amount_correct,
        "accuracy": round(amount_correct / amount_support, 3)
        if amount_support else None,
        "kind_correct": amount_kind_correct,
        "kind_accuracy": round(amount_kind_correct / amount_support, 3)
        if amount_support else None,
    }

    valid_message_ids = {message["id"] for message in messages}
    grounded = sum(
        bool(event.get("source_message_ids"))
        and all(
            source_id in valid_message_ids
            for source_id in event["source_message_ids"]
        )
        for event in events
    )
    return {
        "n_events": len(events),
        "event_detection": detection,
        "multi_message_linkage": linkage,
        "workflow_state": workflow_state,
        "amount": amounts,
        "source_grounding_rate": round(grounded / len(events), 3)
        if events else 0.0,
        "missed": [
            {"anchor_message_id": anchor, "event_type": event_type}
            for anchor, event_type in sorted(gold_keys - predicted_keys)
        ],
        "spurious": [
            {"anchor_message_id": anchor, "event_type": event_type}
            for anchor, event_type in sorted(predicted_keys - gold_keys)
        ],
    }


def _print_row(name: str, metrics: dict) -> None:
    block = metrics["event_detection"]
    linkage = metrics["multi_message_linkage"]
    print(
        f"{name:<18}{block['precision']:>10}{block['recall']:>9}"
        f"{block['f1']:>7}{linkage['accuracy']:>11}"
        f"{metrics['workflow_state']['accuracy']:>10}"
    )


def main() -> None:
    messages = load_dialog()
    gold = load_gold()
    baseline_events = build_rule_baseline(messages)
    hybrid_result = analyze_hybrid(messages, use_embeddings=True)

    baseline = evaluate(baseline_events, gold["events"], messages)
    hybrid = evaluate(hybrid_result["events"], gold["events"], messages)

    print(
        f"Event-level gold: {len(gold['events'])} событий, "
        f"{len(messages)} сообщений\n"
    )
    print(
        f"{'система':<18}{'precision':>10}{'recall':>9}{'f1':>7}"
        f"{'linkage':>11}{'state':>10}"
    )
    _print_row("rules", baseline)
    _print_row("hybrid", hybrid)
    print(
        f"\nРежим hybrid: {hybrid_result['mode']}; "
        f"live chunks {hybrid_result['stats']['live_chunks']}/"
        f"{hybrid_result['stats']['chunks']}; "
        f"кандидатов {hybrid_result['stats']['candidates']}"
    )
    print(
        f"Суммы hybrid: {hybrid['amount']['correct']}/"
        f"{hybrid['amount']['support']}; "
        f"grounding: {hybrid['source_grounding_rate']}"
    )
    if hybrid["missed"]:
        print(f"Пропущено hybrid: {hybrid['missed']}")
    if hybrid["spurious"]:
        print(f"Лишнее hybrid: {hybrid['spurious']}")
    if hybrid_result["errors"]:
        print("Ошибки hybrid:")
        for error in hybrid_result["errors"][:10]:
            print(f"  chunk {error.get('chunk')}: {error['reason']}")

    report = {
        "run_mode": hybrid_result["mode"],
        "corpus": {
            **gold["metadata"],
            "path": "data/demo/chat_events_gold.json",
            "n_messages": len(messages),
            "n_events": len(gold["events"]),
        },
        "evaluation_unit": (
            "event key = anchor_message_id + event_type; related messages "
            "are measured separately by exact linkage"
        ),
        "rules": baseline,
        "hybrid": hybrid,
        "hybrid_runtime": {
            **hybrid_result["stats"],
            "elapsed_sec": hybrid_result["elapsed_sec"],
            "validation_errors": len(hybrid_result["errors"]),
            "errors": hybrid_result["errors"],
            "suppressed_candidates": len(
                hybrid_result["suppressed_candidates"]
            ),
        },
    }
    with open(OUT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print("\nreports/hybrid_coordinator_metrics.json")


if __name__ == "__main__":
    main()
