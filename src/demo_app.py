from __future__ import annotations
import os
import re
import sys

import pandas as pd

sys.path.append(os.path.dirname(__file__))
from clean_prices import to_canonical

BASE = os.path.dirname(__file__)
DF = pd.read_csv(os.path.join(BASE, "..", "data", "processed", "clean_prices.csv"))

CORR = DF.groupby("canonical_work")["price"].agg(
    p10=lambda s: s.quantile(0.10),
    p50="median",
    p90=lambda s: s.quantile(0.90),
    n="count",
)

EXAMPLE = """Укладка плитки на пол; 20; 3200
Штукатурка стен по маякам; 45; 520
Поклейка обоев; 60; 400
Монтаж розеток и выключателей; 15; 350
Стяжка пола; 30; 700
Натяжной потолок; 30; 1900"""

EXAMPLE_REVIEWS = """Мастер опоздал на неделю и постоянно пропадал, не отвечал на звонки. Но плитку положил идеально, качество отличное. После работы оставили кучу мусора.

Отличная бригада, сделали всё в срок. Цена не изменилась от сметы, все договорённости соблюдали. Рекомендую!

Качество хорошее, но смета выросла в полтора раза в процессе работы. На претензии реагировали неохотно, недочёты устраняли со скрипом."""

EXAMPLE_CHAT = """Мастер Алексей: Обнаружили старую проводку в стене, её надо менять. Это плюс 12 000 к смете
Заказчик: А без замены никак? Что будет если оставить
Прораб Игорь: Оставлять нельзя, алюминий, пожарный риск
Заказчик: Тогда меняем конечно
Мастер Алексей: Разводка электрики в кухне готова, прошу принять
Заказчик: Приеду вечером посмотрю
Заказчик: Посмотрел электрику, одна розетка не там где на плане. Нужно исправить
Мастер Алексей: Исправим сегодня, там немного
Прораб Игорь: Смету обновил, итог вырос до 246 000 рублей
Заказчик: Это больше чем мы обсуждали. Откуда разница"""


def _num(x: str):
    x = re.sub(r"[^\d.,]", "", str(x)).replace(",", ".")
    try:
        return float(x)
    except ValueError:
        return None


def parse_line(line: str):
    parts = [p.strip() for p in line.split(";")]
    if len(parts) >= 3:
        name, qty, price = parts[0], _num(parts[1]) or 1.0, _num(parts[2])
    elif len(parts) == 2:
        name, qty, price = parts[0], 1.0, _num(parts[1])
    else:
        return None
    if not name or price is None:
        return None
    return name, qty, price


def analyze(text: str):
    rows = []
    total_quoted = total_fair = 0.0
    flagged = recognized = 0

    for line in text.splitlines():
        if not line.strip():
            continue
        parsed = parse_line(line)
        if parsed is None:
            continue
        name, qty, price = parsed
        work = to_canonical(name)[0]

        if work is None or work not in CORR.index:
            rows.append([name, "не распознано", f"{qty:g}", f"{price:,.0f}",
                         "—", "—", "❔ нет данных"])
            continue

        recognized += 1
        c = CORR.loc[work]
        lo, mid, hi = float(c.p10), float(c.p50), float(c.p90)
        dev = (price / mid - 1) * 100
        if price > hi:
            verdict, flagged = "⚠️ завышено", flagged + 1
        elif price < lo:
            verdict, flagged = "⚠️ занижено", flagged + 1
        else:
            verdict = "✅ в норме"
        total_quoted += price * qty
        total_fair += mid * qty
        rows.append([name, work, f"{qty:g}", f"{price:,.0f}",
                     f"{lo:,.0f}–{hi:,.0f}", f"{dev:+.0f}%", verdict])

    table = pd.DataFrame(rows, columns=[
        "Позиция в смете", "Распознано как", "Кол-во", "Цена/ед, ₽",
        "Рынок P10–P90, ₽", "Отклонение", "Вердикт"])

    if recognized == 0:
        summary = "### Не удалось распознать ни одной позиции.\nФормат строки: `Название работы; количество; цена за единицу`"
    else:
        overpay = total_quoted - total_fair
        summary = (
            f"### Итог по смете\n"
            f"- Распознано позиций: **{recognized}**\n"
            f"- 🚩 Помечено как аномальные: **{flagged}**\n"
            f"- Сумма по смете: **{total_quoted:,.0f} ₽**\n"
            f"- Медианный рыночный ориентир: **{total_fair:,.0f} ₽**\n"
            f"- Разница: **{overpay:+,.0f} ₽** "
            f"({'выше медианного ориентира' if overpay > 0 else 'ниже медианы'})"
        )
    return table, summary


def analyze_reviews(text: str):
    from absa import analyze_review
    import numpy as np
    reviews = [r.strip() for r in text.split("\n\n") if r.strip()]
    if not reviews:
        return pd.DataFrame(), "Вставьте отзывы (пустая строка — разделитель)."
    agg = {}
    for r in reviews:
        for aspect, score in analyze_review(r).items():
            agg.setdefault(aspect, []).append(score)
    rows = []
    for aspect, scores in sorted(agg.items(), key=lambda x: np.mean(x[1])):
        m = float(np.mean(scores))
        stars = round((m + 1) / 2 * 4 + 1, 1)
        bar = "🟩" * round((m + 1) / 2 * 10) + "🟥" * (10 - round((m + 1) / 2 * 10))
        rows.append([aspect, f"{stars:.1f} / 5", bar, len(scores)])
    table = pd.DataFrame(rows, columns=["Аспект", "Оценка", "Профиль", "Упоминаний"])
    summary = (f"### Профиль мастера по {len(reviews)} отзывам\n"
               f"Затронуто аспектов: **{len(agg)}** из 9. "
               f"Оценки извлечены нейросетью из текста — их не накрутить звёздами.")
    return table, summary


def parse_chat(text: str) -> list[dict]:
    messages = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            author, message = line.split(":", 1)
        else:
            author, message = "Участник", line
        if not message.strip():
            continue
        messages.append({
            "id": len(messages) + 1,
            "author": author.strip() or "Участник",
            "text": message.strip(),
            "ts": "",
        })
    return messages


def analyze_chat(text: str):
    from hybrid_coordinator import analyze_hybrid

    messages = parse_chat(text)
    if not messages:
        return pd.DataFrame(), "Вставьте переписку в формате `Имя: сообщение`."
    result = analyze_hybrid(messages, use_embeddings=True)
    message_by_id = {message["id"]: message for message in messages}
    rows = []
    for event in result["events"]:
        fields = []
        if event.get("assignee"):
            fields.append(f"кто: {event['assignee']}")
        if event.get("deadline_text"):
            fields.append(f"срок: {event['deadline_text']}")
        if event.get("amount_rub"):
            direction = {
                "increase": "+",
                "decrease": "−",
                "new_total": "итог ",
                "unspecified": "",
                None: "",
            }[event.get("amount_kind")]
            amount = f"{event['amount_rub']:,.0f}".replace(",", " ")
            fields.append(f"сумма: {direction}{amount} ₽")
        quotes = " / ".join(
            f"#{source_id} «{message_by_id[source_id]['text']}»"
            for source_id in event["source_message_ids"]
        )
        rows.append([
            event["event_id"],
            event["event_type"],
            event["title"],
            " · ".join(fields) or "—",
            event["workflow_state"],
            quotes,
            " / ".join(event["suggested_actions"]),
            event["detected_by"],
        ])
    table = pd.DataFrame(rows, columns=[
        "ID", "Тип", "Карточка", "Поля", "Состояние",
        "Исходные сообщения", "Действия после подтверждения", "Метод",
    ])
    mode = {
        "LIVE_HYBRID": "GigaChat + правила",
        "PARTIAL_HYBRID": "частично GigaChat, частично fallback",
        "RULES_ONLY": "rule fallback — API недоступен",
    }[result["mode"]]
    summary = (
        f"### Найдено карточек: **{len(result['events'])}**\n"
        f"- Режим: **{mode}**\n"
        f"- Сообщений: {len(messages)}, кандидатов: "
        f"{result['stats']['candidates']} "
        f"(semantic-only: {result['stats'].get('semantic_candidates', 0)})\n"
        f"- Обработка: {result['elapsed_sec']} с\n"
        f"- Каждая карточка содержит исходные сообщения; действия выполняются "
        f"только после подтверждения человеком."
    )
    if result["errors"]:
        summary += (
            f"\n- Валидатор/фолбэк: {len(result['errors'])} замечаний "
            f"(невалидный ответ модели не превращается в действие)."
        )
    return table, summary


def build_app():
    import gradio as gr
    with gr.Blocks(title="FRAME · AI-анализ смет") as demo:
        gr.Markdown(
            "# 🏗️ FRAME · AI-модули платформы\n"
            "_Демо ИИ-слоя FRAME: анализ смет (фича 5.2) и структурный рейтинг "
            "мастеров по отзывам (фича 5.3), координатор переписки._"
        )
        with gr.Tab("💰 Анализ сметы"):
            gr.Markdown(
                "Вставьте смету подрядчика — модель сравнит каждую позицию с реальными "
                "рыночными ценами (2 369 цен, 22 компании, 7 городов) и пометит "
                "**завышенные** позиции."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    inp = gr.Textbox(
                        label="Смета (одна позиция в строке: Название; количество; цена/ед)",
                        value=EXAMPLE, lines=10)
                    btn = gr.Button("🔍 Проверить смету", variant="primary")
                    gr.Markdown("Распознаётся **47 типов работ**: штукатурка, стяжка, "
                                "плитка, обои, электрика, сантехника, потолки, двери и др.")
                with gr.Column(scale=2):
                    out_sum = gr.Markdown()
                    out_tbl = gr.Dataframe(label="Разбор по позициям", wrap=True)
            btn.click(analyze, inputs=inp, outputs=[out_tbl, out_sum])
        with gr.Tab("💬 Координатор переписки"):
            gr.Markdown(
                "Вставьте фрагмент чата. Правила найдут кандидатов, GigaChat "
                "свяжет реплики в события, а валидатор проверит суммы и ссылки "
                "на исходные сообщения. Формат: `Имя: сообщение`."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    cinp = gr.Textbox(
                        label="Переписка проекта",
                        value=EXAMPLE_CHAT,
                        lines=16,
                    )
                    cbtn = gr.Button(
                        "🧠 Подготовить карточки и напоминания",
                        variant="primary",
                    )
                with gr.Column(scale=2):
                    csum = gr.Markdown()
                    ctbl = gr.Dataframe(
                        label="Предложения координатора — требуют подтверждения",
                        wrap=True,
                    )
            cbtn.click(analyze_chat, inputs=cinp, outputs=[ctbl, csum])
        with gr.Tab("⭐ Рейтинг мастера по отзывам"):
            gr.Markdown(
                "Вставьте отзывы о мастере (разделитель — пустая строка) — модель "
                "разложит их на **9 аспектов**: сроки, качество, цена, чистота, "
                "коммуникация, профессионализм, честность, гарантия, вежливость."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    rinp = gr.Textbox(label="Отзывы клиентов",
                                      value=EXAMPLE_REVIEWS, lines=12)
                    rbtn = gr.Button("⭐ Построить профиль", variant="primary")
                with gr.Column(scale=2):
                    rsum = gr.Markdown()
                    rtbl = gr.Dataframe(label="Аспектный профиль", wrap=True)
            rbtn.click(analyze_reviews, inputs=rinp, outputs=[rtbl, rsum])
        demo.load(analyze, inputs=inp, outputs=[out_tbl, out_sum])
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860,
                       inbrowser=False, show_error=True,
                       theme=gr.themes.Soft())
