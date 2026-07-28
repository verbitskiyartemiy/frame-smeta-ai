"""Синтетический корпус переписок с разметкой из спецификации.

Ключевое отличие от «сгенерировать диалоги и разметить их моделью»: сначала
в коде задаётся, что именно должно быть в диалоге — тип события, сумма,
номера сообщений, где она названа и где с ней согласились, — и только потом
модель пишет под это живой текст. Метка приходит из спецификации, поэтому
она не зависит от того, что модель «думает» про свой же текст.

Всё, что можно проверить программно, проверяется: сумма обязана стоять в
назначенном сообщении, согласие — в своём, отвлекающее число — вне события.
Диалоги, не прошедшие проверку, отбрасываются, а не чинятся вручную.

Честная граница: корпус остаётся синтетическим, а язык — модельным. Живые
подрядчики пишут хуже и грязнее. И генератор, и извлечение — одно семейство
моделей, поэтому общие слепые зоны возможны.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys

sys.path.append(os.path.dirname(__file__))

import hybrid_coordinator
from llm_coordinator import load_env

BASE = os.path.dirname(__file__)
OUT_PATH = os.path.abspath(
    os.path.join(BASE, "..", "data", "demo", "chat_corpus_generated.json"))

ZONES = ["кухня", "ванная", "спальня", "коридор", "гостиная", "санузел"]
WORKS = ["гидроизоляция", "стяжка пола", "разводка электрики", "штукатурка стен",
         "укладка плитки", "монтаж перегородки", "разводка сантехники",
         "натяжной потолок", "шумоизоляция", "тёплый пол"]
CONTRACTORS = [("Игорь Волков", "Прораб"), ("Марат Хасанов", "Плиточник"),
               ("Алексей Петров", "Прораб"), ("Сергей Ким", "Электрик"),
               ("Дмитрий Орлов", "Сантехник")]

AGREE = ["Хорошо, делаем", "Согласен, приступайте", "Ок, утверждаю",
         "Да, давайте так", "Принято, работайте"]
REFUSE = ["Нет, пока не будем", "Давайте отложим", "Пока откажемся",
          "Не сейчас, вернёмся позже"]
ACCEPT_ASK = ["Прошу принять этап", "Готово, прошу принять работу",
              "Этап закончен, примите пожалуйста"]

SYSTEM = """Ты сценарист. Пишешь реалистичную переписку заказчика и подрядчиков
в чате ремонта квартиры — так, как люди пишут в мессенджере: коротко, живо,
без канцелярита.

Тебе дают режиссёрскую разбивку: сколько реплик, кто говорит и что происходит
в каждой. Разбивка — это указания тебе, а НЕ текст сообщений. Никогда не
переписывай указания в поле text: там должна быть живая реплика человека.

Плохо:  "рабочая деталь по объекту, упомяни число 40"
Хорошо: "Плитку завезли, 40 коробок, сложил в коридоре"

Количество реплик и их порядок менять нельзя. Автор каждой реплики — конкретный
человек с именем, «любой участник» писать нельзя. Где указано вставить точное
число или точную фразу — вставь их дословно внутрь живого текста.

Формат ответа — по одной реплике на строку, три поля через вертикальную черту:

Игорь Волков | Прораб | Плитку завезли, 40 коробок, сложил в коридоре
Вы | Заказчик | Понял, завтра заеду посмотреть

Никаких других строк, заголовков и нумерации. Заказчика всегда зови «Вы»."""

# Слова из режиссёрской разбивки: если они доехали до текста реплики, модель
# переписала указание вместо того, чтобы его исполнить.
ECHO_MARKERS = ("упомяни", "рабочая реплика", "любой участник", "любого участника",
                "не как стоимость", "без сумм", "бытовом смысле", "дословно",
                "реплика без", "участник:")

def parse_lines(raw: str) -> list[dict]:
    """Разбор построчного формата. JSON здесь хрупок: живой текст с кавычками
    регулярно ломает разбор, а потери на этом доходили до трети выборки."""
    messages = []
    for line in str(raw).splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        author, role, text = (p.strip() for p in parts)
        text = " ".join(text.split())
        if author and text:
            messages.append({"author": author, "role": role, "text": text})
    return messages


def make_spec(rng: random.Random, kind: str) -> dict:
    """Спецификация диалога. Здесь рождается разметка, а не в модели."""
    zone = rng.choice(ZONES)
    work = rng.choice(WORKS)
    author, role = rng.choice(CONTRACTORS)
    filler_before = rng.randint(1, 3)
    filler_mid = rng.randint(1, 3)

    spec = {"kind": kind, "zone": zone, "work": work,
            "contractor": author, "role": role, "events": []}

    if kind == "budget_split":
        amount = rng.choice([8000, 12000, 15500, 23000, 31000, 47000])
        distractor = rng.choice([12, 24, 45, 68, 110])
        agree = rng.choice(AGREE)
        amount_at = filler_before + 1
        agree_at = amount_at + filler_mid + 1
        spec["amount"] = amount
        spec["distractor"] = distractor
        spec["marker"] = agree
        spec["n_messages"] = agree_at
        spec["amount_at"] = amount_at
        spec["marker_at"] = agree_at
        spec["events"] = [{"anchor_message_id": amount_at,
                           "event_type": "budget_change",
                           "source_message_ids": [amount_at, agree_at],
                           "workflow_state": "approved",
                           "amount_rub": float(amount),
                           "amount_kind": "increase"}]

    elif kind == "budget_refused":
        amount = rng.choice([9000, 18000, 26000, 39000])
        distractor = rng.choice([8, 30, 51, 96])
        refuse = rng.choice(REFUSE)
        amount_at = filler_before + 1
        refuse_at = amount_at + filler_mid + 1
        spec["amount"] = amount
        spec["distractor"] = distractor
        spec["marker"] = refuse
        spec["n_messages"] = refuse_at
        spec["amount_at"] = amount_at
        spec["marker_at"] = refuse_at
        spec["events"] = [{"anchor_message_id": amount_at,
                           "event_type": "budget_change",
                           "source_message_ids": [amount_at, refuse_at],
                           "workflow_state": "rejected",
                           "amount_rub": float(amount),
                           "amount_kind": "increase"}]

    elif kind == "acceptance_answered":
        ask = rng.choice(ACCEPT_ASK)
        agree = rng.choice(AGREE)
        ask_at = filler_before + 1
        agree_at = ask_at + filler_mid + 1
        spec["marker"] = ask
        spec["second_marker"] = agree
        spec["n_messages"] = agree_at
        spec["marker_at"] = ask_at
        spec["second_marker_at"] = agree_at
        spec["events"] = [{"anchor_message_id": ask_at,
                           "event_type": "acceptance_request",
                           "source_message_ids": [ask_at, agree_at],
                           "workflow_state": "accepted"}]

    elif kind == "acceptance_open":
        ask = rng.choice(ACCEPT_ASK)
        ask_at = filler_before + 1
        spec["marker"] = ask
        spec["n_messages"] = ask_at + rng.randint(0, 1)
        spec["marker_at"] = ask_at
        spec["events"] = [{"anchor_message_id": ask_at,
                           "event_type": "acceptance_request",
                           "source_message_ids": [ask_at],
                           "workflow_state": "pending"}]

    else:  # quiet — рабочая переписка без событий, проверяет ложные срабатывания
        spec["n_messages"] = rng.randint(4, 6)
        spec["distractor"] = rng.choice([15, 40, 120])

    return spec


def build_plan(spec: dict) -> str:
    worker = spec["contractor"]
    lines = [f"Объект: {spec['zone']}, идут работы «{spec['work']}».",
             f"Участники: {worker} — {spec['role']}; Вы — заказчик.",
             f"Реплик ровно {spec['n_messages']}.", "",
             "Разбивка по репликам:"]

    for i in range(1, spec["n_messages"] + 1):
        if i == spec.get("amount_at"):
            lines.append(f"{i}. Говорит {worker}. Вскрылась проблема, работа "
                         f"выходит дороже. Он называет доплату — число "
                         f"{spec['amount']} должно стоять в тексте цифрами, "
                         f"со словом «руб». Коротко объясняет причину.")
        elif i == spec.get("marker_at"):
            if spec["kind"] in ("acceptance_answered", "acceptance_open"):
                lines.append(f"{i}. Говорит {worker}. Этап закончен, зовёт "
                             f"принимать. Реплика начинается фразой "
                             f"«{spec['marker']}», дальше пара слов по делу.")
            else:
                lines.append(f"{i}. Говорит заказчик. Реплика начинается фразой "
                             f"«{spec['marker']}», дальше пара слов по делу.")
        elif i == spec.get("second_marker_at"):
            lines.append(f"{i}. Говорит заказчик. Реплика начинается фразой "
                         f"«{spec['second_marker']}», дальше пара слов по делу.")
        elif i == 1 and spec.get("distractor"):
            lines.append(f"{i}. Говорит {worker}. Бытовая деталь про ход работ, "
                         f"где число {spec['distractor']} — это метры, штуки "
                         f"или часы. Про деньги в этой реплике ни слова.")
        else:
            speaker = worker if i % 2 else "заказчик"
            lines.append(f"{i}. Говорит {speaker}. Обычный рабочий обмен: "
                         f"материалы, доступ на объект, фото, время приезда. "
                         f"Ни сумм, ни согласований, ни приёмки.")

    lines.append("")
    lines.append("Других сумм в рублях в переписке быть не должно.")
    return "\n".join(lines)


def digits(text: str) -> set[str]:
    return {re.sub(r"\s", "", m) for m in re.findall(r"\d[\d\s]*", text)}


def find_only(messages: list[dict], needle: str, as_number: bool) -> int | list[int]:
    """Индекс единственного сообщения с искомым. Список — если их несколько."""
    hits = []
    for i, message in enumerate(messages, start=1):
        found = (needle in digits(message["text"]) if as_number
                 else needle.lower() in message["text"].lower())
        if found:
            hits.append(i)
    return hits[0] if len(hits) == 1 else hits


def resolve(spec: dict, messages: list[dict]) -> tuple[list[dict] | None, str]:
    """Достраивает разметку по фактическим позициям в тексте.

    Спецификация решает, какое событие и с какой суммой должно быть. Где именно
    оно оказалось, определяет точный поиск строки — не модель и не разметчик.
    Неоднозначность считается браком образца.
    """
    for message in messages:
        low = message["text"].lower()
        echoed = [m for m in ECHO_MARKERS if m in low]
        if echoed:
            return None, f"в тексте осталось указание: {echoed[0]}"
        if len(message["text"]) < 12:
            return None, "реплика короче двенадцати символов"
    if any("участник" in m["author"].lower() for m in messages):
        return None, "автор не назван по имени"
    if len(messages) < 3:
        return None, f"слишком короткий диалог: {len(messages)}"

    if spec["kind"] == "quiet":
        money = [i for i, m in enumerate(messages, start=1)
                 if re.search(r"\d[\d\s]{2,}\s*(?:руб|₽)", m["text"], re.I)]
        return ([], "") if not money else (None, f"в тихом диалоге суммы: {money}")

    marker_at = find_only(messages, spec["marker"], False)
    if isinstance(marker_at, list):
        return None, f"фраза-маркер встречается {len(marker_at)} раз"

    if spec.get("amount"):
        amount_at = find_only(messages, str(spec["amount"]), True)
        if isinstance(amount_at, list):
            return None, f"сумма встречается {len(amount_at)} раз"
        if amount_at >= marker_at:
            return None, "ответ пришёл раньше суммы"
        sources = [amount_at, marker_at]
        anchor = amount_at
    elif spec.get("second_marker"):
        second_at = find_only(messages, spec["second_marker"], False)
        if isinstance(second_at, list):
            return None, f"вторая фраза встречается {len(second_at)} раз"
        if second_at <= marker_at:
            return None, "согласие раньше запроса"
        sources = [marker_at, second_at]
        anchor = marker_at
    else:
        sources = [marker_at]
        anchor = marker_at

    # Реплики-наполнители не должны решать судьбу доплаты. Модель регулярно
    # вписывает туда «подождём с доплатой», и тогда размеченный workflow_state
    # расходится с тем, что прочитает человек. Такой образец бракуем.
    for i, message in enumerate(messages, start=1):
        if i in sources:
            continue
        low = message["text"].lower()
        if any(w in low for w in ("доплат", "согласов", "утвержд", "одобр")):
            return None, f"наполнитель {i} решает судьбу доплаты"
        for phrase in AGREE + REFUSE:
            if phrase.lower() in low:
                return None, f"наполнитель {i} содержит ответ «{phrase}»"

    event = dict(spec["events"][0])
    event["anchor_message_id"] = anchor
    event["source_message_ids"] = sources
    return [event], ""


def generate(count: int, seed: int) -> dict:
    rng = random.Random(seed)
    kinds = ["budget_split", "budget_refused", "acceptance_answered",
             "acceptance_open", "quiet"]
    dialogs, rejected = [], []

    for index in range(count):
        spec = make_spec(rng, kinds[index % len(kinds)])
        try:
            raw = hybrid_coordinator.call_llm(
                build_plan(spec), temperature=0.8, system_prompt=SYSTEM)
            messages = parse_lines(raw)
        except Exception as exc:
            rejected.append({"kind": spec["kind"],
                             "reason": f"{type(exc).__name__}: {exc}"})
            continue

        clean = [{"id": i, "author": m["author"], "role": m["role"], "text": m["text"]}
                 for i, m in enumerate(messages, start=1)]

        events, problem = resolve(spec, clean)
        if events is None:
            rejected.append({"kind": spec["kind"], "reason": problem})
            continue

        dialogs.append({"id": f"d{index:03d}", "kind": spec["kind"],
                        "messages": clean, "events": events})
        print(f"  [{len(dialogs):3d}] {spec['kind']:20s} "
              f"{len(clean)} сообщ., событий {len(spec['events'])}", flush=True)

    return {
        "metadata": {
            "origin": "synthetic",
            "annotation": "from specification",
            "note": "Разметка задана в коде до генерации текста. Модель писала "
                    "текст под спецификацию, не размечала его.",
            "verified": "сумма и фразы-маркеры проверены программно; "
                        "непрошедшие образцы отброшены",
            "warning": "Язык модельный, живые подрядчики пишут грязнее. "
                       "Генератор и извлечение — одно семейство моделей, "
                       "общие слепые зоны возможны.",
            "seed": seed,
            "requested": count,
            "accepted": len(dialogs),
            "rejected": len(rejected),
        },
        "dialogs": dialogs,
        "rejected": rejected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260728)
    args = parser.parse_args()

    load_env()
    print(f"Генерирую {args.count} диалогов, seed {args.seed}")
    corpus = generate(args.count, args.seed)

    meta = corpus["metadata"]
    print(f"\nПринято {meta['accepted']}, отброшено {meta['rejected']}")
    for item in corpus["rejected"][:8]:
        print(f"  брак: {item['kind']} — {item['reason']}")

    total_messages = sum(len(d["messages"]) for d in corpus["dialogs"])
    total_events = sum(len(d["events"]) for d in corpus["dialogs"])
    print(f"Сообщений {total_messages}, событий {total_events}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(corpus, fh, ensure_ascii=False, indent=1)
    print(f"Корпус: {os.path.relpath(OUT_PATH, BASE)}")


if __name__ == "__main__":
    main()
