# Контракты AI-демо

## Режимы

- `DEMO_FIXTURE` — воспроизводимый локальный сценарий. Всегда имеет видимый badge.
- `LIVE_HYBRID` — GigaChat Embeddings + GigaChat extraction + validator.
- `RULES_ONLY` — fallback без LLM при недоступном API.

Frontend не должен автоматически называть режим `LIVE_HYBRID`, если backend не вернул его в ответе.

## Событие переписки

```ts
type ConversationEvent = {
  id: string
  type: 'budget_change' | 'deadline_change' | 'task' | 'decision' | 'acceptance'
  title: string
  state: 'proposed' | 'confirmed' | 'rejected' | 'needs_reply'
  amountRub?: number
  deadline?: string
  description: string
  sourceMessageIds: string[]
  confidence?: number
  mode: 'DEMO_FIXTURE' | 'LIVE_HYBRID' | 'RULES_ONLY'
}
```

## HTTP-граница

### `POST /api/demo/analyze-chat`

Вход: проект, ветка и сообщения. Выход: список `ConversationEvent`, метаданные режима и предупреждения валидатора.

### `POST /api/demo/confirm-event`

Вход: `eventId`, решение пользователя и версия события. Выход: обновлённое состояние и запись audit log.

### `POST /api/demo/analyze-estimate`

Вход: позиции сметы. Выход:

- нормализованная работа;
- покрытие;
- медианный ориентир и коридор;
- ссылка на источник/срез;
- причина отсутствия оценки.

Ответ не использует слова «переплата», «мошенничество» или «справедливая цена».

## Безопасный fallback

При ошибке API интерфейс:

1. сохраняет введённые данные;
2. показывает точный режим и причину fallback;
3. не подменяет live-результат фикстурой без явной пометки;
4. не применяет финансовое действие без подтверждения человека.
