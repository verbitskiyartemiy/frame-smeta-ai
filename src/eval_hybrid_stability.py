"""Несколько live-прогонов гибридного координатора для оценки стабильности."""

from __future__ import annotations

import json
import os
import statistics
import sys

from eval_hybrid_coordinator import (
    build_rule_baseline,
    evaluate,
    load_gold,
)
from hybrid_coordinator import analyze_hybrid
from llm_coordinator import load_dialog


BASE = os.path.dirname(__file__)
OUT = os.path.abspath(
    os.path.join(BASE, "..", "reports", "hybrid_coordinator_stability.json")
)


def summary(values: list[float]) -> dict:
    return {
        "mean": round(statistics.mean(values), 3),
        "std": round(statistics.pstdev(values), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
    }


def main() -> None:
    runs_count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    messages = load_dialog()
    gold = load_gold()
    baseline = evaluate(
        build_rule_baseline(messages), gold["events"], messages
    )
    runs = []
    for run_index in range(runs_count):
        result = analyze_hybrid(messages, use_embeddings=True)
        metrics = evaluate(result["events"], gold["events"], messages)
        row = {
            "run": run_index + 1,
            "mode": result["mode"],
            "elapsed_sec": result["elapsed_sec"],
            "event_detection": metrics["event_detection"],
            "multi_message_linkage": metrics["multi_message_linkage"],
            "workflow_state": metrics["workflow_state"],
            "amount": metrics["amount"],
            "source_grounding_rate": metrics["source_grounding_rate"],
            "missed": metrics["missed"],
            "spurious": metrics["spurious"],
            "validation_errors": result["errors"],
        }
        runs.append(row)
        print(
            f"run {run_index + 1}: mode={result['mode']} "
            f"F1={metrics['event_detection']['f1']} "
            f"linkage={metrics['multi_message_linkage']['accuracy']} "
            f"state={metrics['workflow_state']['accuracy']} "
            f"time={result['elapsed_sec']}s"
        )

    report = {
        "run_count": runs_count,
        "corpus": {
            **gold["metadata"],
            "n_messages": len(messages),
            "n_events": len(gold["events"]),
        },
        "rules_baseline": baseline,
        "hybrid_summary": {
            "event_f1": summary([
                run["event_detection"]["f1"] for run in runs
            ]),
            "linkage_accuracy": summary([
                run["multi_message_linkage"]["accuracy"] for run in runs
            ]),
            "workflow_state_accuracy": summary([
                run["workflow_state"]["accuracy"] for run in runs
            ]),
            "source_grounding_rate": summary([
                run["source_grounding_rate"] for run in runs
            ]),
            "elapsed_sec": summary([
                run["elapsed_sec"] for run in runs
            ]),
        },
        "runs": runs,
    }
    with open(OUT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(f"\n{OUT}")


if __name__ == "__main__":
    main()
