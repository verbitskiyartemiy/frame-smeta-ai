from __future__ import annotations
import json
import os
import sys

sys.path.append(os.path.dirname(__file__))
from coordinator import classify_event
from llm_coordinator import analyze, load_dialog

BASE = os.path.dirname(__file__)
OUT = os.path.abspath(os.path.join(BASE, "..", "reports", "llm_coordinator_metrics.json"))

RU2EN = {
    "задача": "task",
    "решение": "decision",
    "финансовое_согласование": "budget_change",
    "запрос_приёмки": "acceptance_request",
    "риск": "risk",
    "вопрос": "question",
}


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return round(p, 3), round(r, 3), round(f, 3)


def gold_pairs(messages):
    return {(m["id"], RU2EN[m["event_type"]])
            for m in messages if m["event_type"] in RU2EN}


def eval_llm(events, messages):
    gold = gold_pairs(messages)
    gold_ids = {i for i, _ in gold}

    predicted, grounded, hallucinated = set(), 0, 0
    valid_ids = {m["id"] for m in messages}
    for e in events:
        src = e["source_message_ids"]
        if src and all(s in valid_ids for s in src):
            grounded += 1
        else:
            hallucinated += 1
        for s in src:
            predicted.add((s, e["event_type"]))

    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    p, r, f = prf(tp, fp, fn)

    covered_ids = {i for i, _ in predicted}
    id_tp = len(covered_ids & gold_ids)
    id_p, id_r, id_f = prf(id_tp, len(covered_ids - gold_ids),
                           len(gold_ids - covered_ids))

    return {
        "n_events": len(events),
        "exact_pair": {"precision": p, "recall": r, "f1": f,
                       "tp": tp, "fp": fp, "fn": fn},
        "message_level": {"precision": id_p, "recall": id_r, "f1": id_f},
        "source_grounding_rate": round(grounded / len(events), 3) if events else 0.0,
        "hallucinated_events": hallucinated,
        "missed": sorted(gold - predicted),
        "spurious": sorted(predicted - gold),
    }


def eval_rules(messages):
    gold = gold_pairs(messages)
    predicted = set()
    for m in messages:
        label, _ = classify_event(m["text"])
        if label in RU2EN:
            predicted.add((m["id"], RU2EN[label]))
    tp = len(predicted & gold)
    p, r, f = prf(tp, len(predicted - gold), len(gold - predicted))
    return {"n_events": len(predicted),
            "exact_pair": {"precision": p, "recall": r, "f1": f,
                           "tp": tp, "fp": len(predicted - gold),
                           "fn": len(gold - predicted)}}


BUDGET_GOLD = {
    34000: {"approved": True, "proposal": 8, "confirmation": 9},
    12000: {"approved": True, "proposal": 18, "confirmation": 21},
    246000: {"approved": False, "proposal": 31, "confirmation": None},
    8500: {"approved": False, "proposal": 40, "confirmation": None},
}


def eval_budget_linkage(events):
    found, correct, rows = 0, 0, []
    for amount, gold in BUDGET_GOLD.items():
        ev = next((e for e in events
                   if e["event_type"] == "budget_change"
                   and e.get("amount_rub")
                   and abs(e["amount_rub"] - amount) < 1), None)
        if ev is None:
            rows.append({"amount": amount, "gold_approved": gold["approved"],
                         "verdict": "не найдено"})
            continue
        found += 1
        said = ev["llm_status"] == "confirmed"
        ok = said == gold["approved"]
        correct += ok
        rows.append({"amount": amount, "gold_approved": gold["approved"],
                     "llm_approved": said, "correct": ok,
                     "source_message_ids": ev["source_message_ids"],
                     "verdict": "верно" if ok else "неверно"})
    return {
        "n_budget_events_in_gold": len(BUDGET_GOLD),
        "found_by_llm": found,
        "approval_correct": correct,
        "approval_accuracy_on_found": round(correct / found, 3) if found else 0.0,
        "rules_can_do_this": False,
        "note": "Rule-based baseline такую задачу не решает в принципе: он проверяет "
                "лишь наличие ЛЮБОГО последующего сообщения класса «решение» и не "
                "связывает согласие с конкретной суммой.",
        "detail": rows,
    }


def main():
    live = "--live" in sys.argv
    messages = load_dialog()

    res = analyze(messages, allow_cached=not live)
    if live and res["mode"] != "LIVE":
        print("Живой вызов не удался, а запрошен --live. Метрики не записаны.")
        return

    llm = eval_llm(res["events"], messages)
    rules = eval_rules(messages)

    print(f"Режим прогона: {res['mode']}")
    print(f"Размеченный диалог: {len(messages)} сообщений, "
          f"{len(gold_pairs(messages))} событий в разметке\n")

    print("--- Точность извлечения событий (пара «сообщение + тип») ---")
    print(f"  {'система':<22}{'precision':>10}{'recall':>9}{'f1':>7}")
    for name, block in (("rule-based baseline", rules["exact_pair"]),
                        ("LLM-координатор", llm["exact_pair"])):
        print(f"  {name:<22}{block['precision']:>10}{block['recall']:>9}{block['f1']:>7}")

    budget = eval_budget_linkage(res["events"])
    print("\n--- Связывание «сумма → согласована ли» (правила это не умеют) ---")
    for r in budget["detail"]:
        gold = "согласовано" if r["gold_approved"] else "НЕ согласовано"
        amt = f"{r['amount']:,}".replace(",", " ")
        if r["verdict"] == "не найдено":
            print(f"  {amt:>9} ₽  разметка: {gold:<15} LLM: не нашла")
        else:
            llm_said = "согласовано" if r["llm_approved"] else "НЕ согласовано"
            print(f"  {amt:>9} ₽  разметка: {gold:<15} LLM: {llm_said:<15} "
                  f"{r['verdict']}  источник {r['source_message_ids']}")
    print(f"  найдено {budget['found_by_llm']} из {budget['n_budget_events_in_gold']}, "
          f"статус верен у {budget['approval_correct']} из {budget['found_by_llm']}")

    print(f"\n--- Проверки надёжности LLM ---")
    print(f"  событий предложено:            {llm['n_events']}")
    print(f"  доля со ссылками на сообщения: {llm['source_grounding_rate']}")
    print(f"  событий без валидных ссылок:   {llm['hallucinated_events']}")
    print(f"  отклонено валидацией кода:     {len(res['errors'])}")

    if llm["missed"]:
        print(f"\n  Пропущено LLM ({len(llm['missed'])}):")
        for mid, et in llm["missed"][:10]:
            print(f"    #{mid} {et}")
    if llm["spurious"]:
        print(f"\n  Лишнее у LLM ({len(llm['spurious'])}):")
        for mid, et in llm["spurious"][:10]:
            print(f"    #{mid} {et}")

    out = {
        "run_mode": res["mode"],
        "corpus": {
            "path": "data/demo/chat_dialog.json",
            "n_messages": len(messages),
            "origin": "synthetic",
            "warning": "Диалог написан и размечен автором проекта и использовался "
                       "при разработке промпта. Это проверка работоспособности "
                       "пайплайна, а НЕ оценка качества production-системы. "
                       "Для честной оценки нужен независимый корпус реальных "
                       "переписок, которого вне платформы не существует.",
        },
        "rule_based_baseline": rules,
        "llm_coordinator": llm,
        "budget_approval_linkage": budget,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nreports/llm_coordinator_metrics.json")


if __name__ == "__main__":
    main()
