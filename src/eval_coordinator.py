from __future__ import annotations
import collections
import json
import os
import sys

sys.path.append(os.path.dirname(__file__))
from coordinator import (EVENT_TYPES, classify_event, classify_rules,
                         classify_with_embeddings, extract_slots,
                         get_matcher, load_dialog)

BASE = os.path.dirname(__file__)
SLOT_KEYS = ("amount", "deadline", "stage", "room", "assignee")


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return round(p, 3), round(r, 3), round(f, 3)


def eval_types(messages):
    gold = [m["event_type"] for m in messages]
    majority = collections.Counter(gold).most_common(1)[0]

    preds = {"rules_plus_fallback": [], "embeddings_only": [],
             "rules_plus_embeddings": []}
    covered = 0
    for m in messages:
        r = classify_rules(m["text"])
        preds["rules_plus_fallback"].append(classify_event(m["text"])[0])
        covered += r is not None
        e, _ = get_matcher().classify(m["text"])
        preds["embeddings_only"].append(e or "информация")
        h, _ = classify_with_embeddings(m["text"])
        preds["rules_plus_embeddings"].append(h)

    out = {
        "n": len(gold),
        "majority_baseline": {"label": majority[0],
                              "accuracy": round(majority[1] / len(gold), 3)},
        "rules_coverage": round(covered / len(gold), 3),
    }
    for name, pr in preds.items():
        acc = sum(a == b for a, b in zip(gold, pr)) / len(gold)
        out[name] = {"accuracy": round(acc, 3)}

    per = {}
    for lab in EVENT_TYPES:
        tp = sum(g == lab and p == lab for g, p in zip(gold, preds["rules_plus_fallback"]))
        fp = sum(g != lab and p == lab for g, p in zip(gold, preds["rules_plus_fallback"]))
        fn = sum(g == lab and p != lab for g, p in zip(gold, preds["rules_plus_fallback"]))
        p, r, f = prf(tp, fp, fn)
        per[lab] = {"support": sum(g == lab for g in gold),
                    "precision": p, "recall": r, "f1": f}
    out["per_class_shipped"] = per

    errors = [{"id": m["id"], "text": m["text"][:70], "gold": g, "pred": p}
              for m, g, p in zip(messages, gold, preds["rules_plus_fallback"]) if g != p]
    out["errors"] = errors
    return out


def eval_slots(messages):
    stats = {k: {"tp": 0, "fp": 0, "fn": 0} for k in SLOT_KEYS}
    for m in messages:
        gold = m.get("slots", {})
        pred = extract_slots(m["text"])
        for k in SLOT_KEYS:
            g, p = gold.get(k), pred.get(k)
            if g is not None and p is not None:
                same = (str(g).lower()[:5] in str(p).lower() or
                        str(p).lower()[:5] in str(g).lower())
                stats[k]["tp" if same else "fp"] += 1
                if not same:
                    stats[k]["fn"] += 1
            elif p is not None:
                stats[k]["fp"] += 1
            elif g is not None:
                stats[k]["fn"] += 1

    out = {}
    for k, s in stats.items():
        p, r, f = prf(s["tp"], s["fp"], s["fn"])
        out[k] = {"precision": p, "recall": r, "f1": f, **s}
    micro_tp = sum(s["tp"] for s in stats.values())
    micro_fp = sum(s["fp"] for s in stats.values())
    micro_fn = sum(s["fn"] for s in stats.values())
    p, r, f = prf(micro_tp, micro_fp, micro_fn)
    out["micro"] = {"precision": p, "recall": r, "f1": f}
    return out


def main():
    messages = load_dialog()
    types = eval_types(messages)
    slots = eval_slots(messages)

    print(f"Сообщений в размеченном диалоге: {types['n']}")
    print(f"Мажоритарный baseline ('{types['majority_baseline']['label']}'): "
          f"{types['majority_baseline']['accuracy']}\n")
    print("--- Точность определения типа события ---")
    for name in ("rules_plus_fallback", "embeddings_only", "rules_plus_embeddings"):
        print(f"  {name:16} accuracy = {types[name]['accuracy']}")
    print(f"  (правила срабатывают на {types['rules_coverage']:.0%} сообщений, "
          f"остальные уходят в фолбэк)")

    print("\n--- Гибрид по классам ---")
    print(f"  {'класс':<26}{'n':>3}  {'precision':>9}{'recall':>8}{'f1':>7}")
    for lab, v in types["per_class_shipped"].items():
        print(f"  {lab:<26}{v['support']:>3}  {v['precision']:>9}{v['recall']:>8}{v['f1']:>7}")

    print("\n--- Извлечение полей ---")
    print(f"  {'поле':<12}{'precision':>10}{'recall':>8}{'f1':>7}")
    for k in SLOT_KEYS:
        v = slots[k]
        print(f"  {k:<12}{v['precision']:>10}{v['recall']:>8}{v['f1']:>7}")
    print(f"  {'micro':<12}{slots['micro']['precision']:>10}"
          f"{slots['micro']['recall']:>8}{slots['micro']['f1']:>7}")

    print(f"\n--- Ошибки классификации ({len(types['errors'])}) ---")
    for e in types["errors"]:
        print(f"  #{e['id']:>2} ждали {e['gold']:<24} получили {e['pred']}")
        print(f"      «{e['text']}»")

    res = {"event_type": types, "slots": slots,
           "corpus": {"origin": "synthetic",
                      "note": "Диалог написан и размечен автором. Реальных "
                              "переписок вне платформы не существует. Это проверка "
                              "работоспособности пайплайна, а не оценка на "
                              "продакшн-данных."}}
    path = os.path.abspath(os.path.join(BASE, "..", "reports", "coordinator_metrics.json"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"\nreports/coordinator_metrics.json")


if __name__ == "__main__":
    main()
