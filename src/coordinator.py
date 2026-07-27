from __future__ import annotations
import functools
import json
import os
import re

import numpy as np

BASE = os.path.dirname(__file__)
DIALOG = os.path.join(BASE, "..", "data", "demo", "chat_dialog.json")

EVENT_TYPES = ["вопрос", "задача", "решение", "финансовое_согласование",
               "запрос_приёмки", "риск", "информация"]

ANCHORS = {
    "вопрос": [
        "а можно перенести розетку на другую стену",
        "когда будет готова новая версия сметы",
        "насколько это критично для срока",
        "сколько действует гарантия",
    ],
    "задача": [
        "пришли пожалуйста до четверга новую раскладку",
        "нужно до понедельника определиться с моделью",
        "надо заказать двери до пятницы",
        "нужно исправить розетку",
    ],
    "решение": [
        "хорошо, согласен, делаем",
        "этап принимаю",
        "давайте возьмём другой вариант",
        "тогда меняем конечно",
    ],
    "финансовое_согласование": [
        "выходит дороже на 34 000 рублей",
        "это плюс 12 000 к смете",
        "итог сметы вырос до 246 000 рублей",
        "замена даст экономию 8 500 рублей",
    ],
    "запрос_приёмки": [
        "работы завершены, прошу принять этап",
        "демонтаж закончен, фото приложил",
        "разводка готова, прошу принять",
    ],
    "риск": [
        "поставщик задерживает материал на неделю",
        "на складе нет нужного профиля, возможны задержки",
        "старая проводка, пожарный риск",
        "если будет сыро, штукатурка будет сохнуть дольше",
    ],
    "информация": [
        "сегодня выходим на объект",
        "доброе утро всем",
        "отправила файл на почту",
        "работы идут по плану",
    ],
}

DEADLINE_STEMS = ("понедельник", "вторник", "сред", "четверг", "пятниц",
                  "суббот", "воскресень", "выходн", "завтра", "сегодня")

STAGES = ("демонтаж", "штробление", "электрика", "сантехника", "укладка плитки",
          "плитк", "потолок", "штукатурка", "двери", "разводка", "затирк")

ROOMS = ("кухня", "кухне", "санузел", "санузле", "ванная", "ванной", "спальня",
         "спальне", "коридор", "коридоре")

NOT_NAMES = {"хорошо", "ок", "понял", "поняла", "отлично", "да", "нет", "спасибо",
             "конечно", "супер", "ясно", "принято", "добрый", "доброе", "здравствуйте"}


def _norm_stage(s: str) -> str:
    return {"плитк": "укладка плитки", "разводка": "электрика",
            "затирк": "укладка плитки"}.get(s, s)


def extract_slots(text: str) -> dict:
    low = text.lower()
    slots = {}

    m = re.search(r"(\d[\d\s]{2,})\s*(?:руб|₽|р\.)", low)
    if not m:
        m2 = re.search(r"(\d+)\s*(?:тыс|тысяч)", low)
        if m2:
            slots["amount"] = int(m2.group(1)) * 1000
    else:
        slots["amount"] = int(re.sub(r"\s", "", m.group(1)))

    for d in DEADLINE_STEMS:
        if d in low:
            slots["deadline"] = d
            break

    for s in STAGES:
        if s in low:
            slots["stage"] = _norm_stage(s)
            break

    for r in ROOMS:
        if r in low:
            slots["room"] = {"кухне": "кухня", "санузле": "санузел",
                             "ванной": "ванная", "спальне": "спальня",
                             "коридоре": "коридор"}.get(r, r)
            break

    m = re.match(r"\s*([А-ЯЁ][а-яё]+)\s*,", text)
    if m and m.group(1).lower() not in NOT_NAMES:
        slots["assignee"] = m.group(1)

    return slots


def classify_rules(text: str) -> str | None:
    low = text.lower()

    if re.search(r"прошу\s+принять|принять\s+этап", low):
        return "запрос_приёмки"
    if re.search(r"задерж|сдвигается|не\s+успе|на\s+складе\s+нет|нет\s+в\s+наличии|"
                 r"пожарн|риск|дольше\s+сохнуть", low):
        return "риск"
    if re.search(r"\d[\d\s]{2,}\s*(?:руб|₽)|\d+\s*тыс", low) and \
       re.search(r"дороже|плюс|вырос|экономи|смет", low):
        return "финансовое_согласование"
    if re.search(r"^[А-ЯЁ][а-яё]+\s*,\s*(?:пришли|сделай|отправь|подготовь)", text) or \
       re.search(r"нужно\s+до\b|надо\s+заказать|нужно\s+заказать|нужно\s+исправить|"
                 r"пришли\s+пожалуйста|нужно\s+определиться", low):
        return "задача"
    if re.search(r"\bсогласен\b|принимаю|давайте\s+|тогда\s+меняем|решили", low):
        return "решение"
    if "?" in text:
        return "вопрос"
    return None


class EventMatcher:
    def __init__(self, threshold: float = 0.35):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.threshold = threshold
        self._labels, phrases = [], []
        for label, items in ANCHORS.items():
            for a in items:
                self._labels.append(label)
                phrases.append(a)
        self._emb = self.model.encode(phrases, normalize_embeddings=True)

    def classify(self, text: str) -> tuple[str | None, float]:
        q = self.model.encode([text], normalize_embeddings=True)[0]
        sims = self._emb @ q
        best = int(np.argmax(sims))
        score = float(sims[best])
        if score < self.threshold:
            return None, score
        return self._labels[best], score


@functools.lru_cache(maxsize=1)
def get_matcher() -> EventMatcher:
    return EventMatcher()


def classify_event(text: str) -> tuple[str, str]:
    r = classify_rules(text)
    if r is not None:
        return r, "rules"
    return "информация", "fallback"


def classify_with_embeddings(text: str) -> tuple[str, str]:
    r = classify_rules(text)
    if r is not None:
        return r, "rules"
    label, _ = get_matcher().classify(text)
    return (label or "информация"), "embeddings"


def build_card(msg: dict) -> dict:
    label, how = classify_event(msg["text"])
    slots = extract_slots(msg["text"])
    actions = {
        "запрос_приёмки": ["Принять этап", "Запросить исправления", "Задать вопрос"],
        "задача": ["Создать задачу", "Изменить срок", "Отклонить"],
        "финансовое_согласование": ["Согласовать сумму", "Запросить обоснование"],
        "решение": ["Записать в протокол"],
        "риск": ["Взять на контроль", "Запросить план Б"],
        "вопрос": ["Ответить", "Назначить ответственного"],
        "информация": [],
    }[label]
    return {
        "message_id": msg["id"],
        "author": msg["author"],
        "event_type": label,
        "detected_by": how,
        "slots": slots,
        "suggested_actions": actions,
        "requires_confirmation": bool(actions),
        "source": {"type": "chat_message", "id": msg["id"], "ts": msg.get("ts")},
    }


def load_dialog(path: str = DIALOG) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["messages"]


def make_digest(cards: list[dict], messages: list[dict]) -> dict:
    by = lambda t: [c for c in cards if c["event_type"] == t]
    unanswered = []
    for c in by("вопрос"):
        later = [m for m in messages if m["id"] > c["message_id"]
                 and m["author"] != c["author"]]
        if not later:
            unanswered.append(c["message_id"])
    money = [c["slots"]["amount"] for c in cards if "amount" in c["slots"]]
    return {
        "messages_total": len(messages),
        "cards_created": len([c for c in cards if c["requires_confirmation"]]),
        "decisions": len(by("решение")),
        "tasks": len(by("задача")),
        "questions": len(by("вопрос")),
        "questions_without_reply": unanswered,
        "acceptance_requests": len(by("запрос_приёмки")),
        "risks": len(by("риск")),
        "money_events": len(money),
        "money_mentioned_total": sum(money),
    }


def make_reminders(cards: list[dict], messages: list[dict]) -> list[dict]:
    reminders = []
    for c in cards:
        if c["event_type"] == "задача" and "deadline" in c["slots"]:
            reminders.append({
                "kind": "deadline",
                "text": f"Задача из сообщения #{c['message_id']} "
                        f"({c['slots'].get('stage', 'без этапа')}): "
                        f"срок — {c['slots']['deadline']}",
                "source_message": c["message_id"],
            })
        if c["event_type"] == "запрос_приёмки":
            accepted = any(
                m["id"] > c["message_id"] and m["event_type"] == "решение"
                for m in messages)
            if not accepted:
                reminders.append({
                    "kind": "acceptance_pending",
                    "text": f"Этап «{c['slots'].get('stage', '?')}» ждёт приёмки "
                            f"(сообщение #{c['message_id']})",
                    "source_message": c["message_id"],
                })
        if c["event_type"] == "финансовое_согласование" and "amount" in c["slots"]:
            agreed = any(
                m["id"] > c["message_id"] and m["event_type"] == "решение"
                for m in messages)
            if not agreed:
                reminders.append({
                    "kind": "money_pending",
                    "text": f"Изменение бюджета на {c['slots']['amount']:,} ₽ "
                            f"не согласовано (сообщение #{c['message_id']})",
                    "source_message": c["message_id"],
                })
    return reminders


def main():
    messages = load_dialog()
    cards = [build_card(m) for m in messages]
    digest = make_digest(cards, messages)

    print(f"Переписка за период: {digest['messages_total']} сообщений\n")
    print("--- Карточки, требующие подтверждения ---")
    for c in cards:
        if not c["requires_confirmation"]:
            continue
        slots = ", ".join(f"{k}={v}" for k, v in c["slots"].items()) or "—"
        print(f"  #{c['message_id']:>2} [{c['event_type']:<24}] {slots}")
        print(f"      кнопки: {' / '.join(c['suggested_actions'])}   ({c['detected_by']})")

    print("\n--- Сводка за период ---")
    print(f"  решений: {digest['decisions']}   задач: {digest['tasks']}   "
          f"вопросов: {digest['questions']}   рисков: {digest['risks']}")
    print(f"  запросов на приёмку: {digest['acceptance_requests']}")
    print(f"  финансовых событий: {digest['money_events']} "
          f"на сумму {digest['money_mentioned_total']:,} ₽")
    print(f"  вопросов без ответа: {digest['questions_without_reply'] or 'нет'}")

    reminders = make_reminders(cards, messages)
    if reminders:
        print("\n--- Напоминания ---")
        for r in reminders:
            print(f"  [{r['kind']}] {r['text']}")
    print(f"\n  карточек создано: {digest['cards_created']} из {digest['messages_total']} сообщений")


if __name__ == "__main__":
    main()
