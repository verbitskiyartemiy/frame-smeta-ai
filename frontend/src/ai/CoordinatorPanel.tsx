import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ListTodo,
  Loader2,
  MessageCircle,
  Sparkles,
  WalletCards,
  type LucideIcon,
} from 'lucide-react'
import type { Thread } from '../data/mock'
import type { ConversationEvent } from './types'
import { modeBadgeClasses, useDemoStore } from './context'
import type { LiveState } from './useCoordinator'

interface FixtureEvent {
  eventId: string
  title: string
  description: string
  action?: string
  icon: LucideIcon
}

const fixtureByThread: Record<string, FixtureEvent> = {
  e0: {
    eventId: 'e0-budget',
    title: 'Доплата требует решения',
    description:
      'Полная замена старой проводки: +12 000 ₽. Сумма названа электриком, согласие заказчика найдено в этой же ветке.',
    action: 'Подтвердить доплату',
    icon: WalletCards,
  },
  p0: {
    eventId: 'p0-acceptance',
    title: 'Этап ждёт приёмки',
    description:
      'Плиточник сообщил о завершении укладки в ванной и просит принять этап. Ответа заказчика в ветке нет.',
    action: 'Принять этап',
    icon: Clock3,
  },
  t1: {
    eventId: 't1-task',
    title: 'Задача выполнена',
    description:
      'Развести 9 электроточек на кухне. Исполнитель сообщил о завершении и приложил фото.',
    icon: CheckCircle2,
  },
  t2: {
    eventId: 't2-budget',
    title: 'Доплата требует решения',
    description:
      'Армирование трещины: +8 000 ₽ и +1 день. Сумма извлечена из сообщения прораба, но ещё не согласована заказчиком.',
    action: 'Подтвердить доплату',
    icon: WalletCards,
  },
  t3: {
    eventId: 't3-decision',
    title: 'Решение зафиксировано',
    description:
      'Для затирки выбран графит Ceresit CE 40 №16. Ответ дизайнера связан с исходным вопросом.',
    icon: ListTodo,
  },
  t4: {
    eventId: 't4-acceptance',
    title: 'Этап принят',
    description:
      'Демонтаж принят заказчиком. Оплата подтверждена только после явной реплики в чате.',
    icon: CheckCircle2,
  },
}

const LIVE_THREAD_ID = 'e0'

// Этапы совпадают с реальным пайплайном, но идут по таймеру: бэкенд отдаёт
// результат одним ответом и промежуточных событий не присылает. Это индикатор
// ожидания, а не трассировка — поэтому и последний этап не отмечается готовым.
const STAGES = [
  'Ищу кандидатов правилами',
  'Связываю реплики по смыслу',
  'Разбираю контекст моделью',
  'Проверяю источники',
]

function AnalysisProgress() {
  const [stage, setStage] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(
      () => setStage((value) => Math.min(value + 1, STAGES.length - 1)),
      1400,
    )
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className="space-y-1.5 rounded-xl border border-slate-200 bg-white px-4 py-3">
      {STAGES.map((label, index) => (
        <div
          key={label}
          className={`flex items-center gap-2 text-xs transition-colors ${
            index < stage
              ? 'text-slate-400'
              : index === stage
                ? 'font-medium text-slate-800'
                : 'text-slate-300'
          }`}
        >
          {index < stage ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
          ) : index === stage ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-500" />
          ) : (
            <span className="h-3.5 w-3.5 rounded-full border border-current" />
          )}
          {label}
        </div>
      ))}
    </div>
  )
}

function eventStableId(threadId: string, event: ConversationEvent): string {
  if (event.type === 'budget_change' && threadId === LIVE_THREAD_ID) {
    return 'e0-budget'
  }
  return `${threadId}-live-${event.id}`
}

const typeLabels: Record<ConversationEvent['type'], string> = {
  task: 'задача',
  decision: 'решение',
  budget_change: 'изменение бюджета',
  acceptance_request: 'запрос приёмки',
  risk: 'риск',
  question: 'вопрос',
}

const typeStyles: Record<
  ConversationEvent['type'],
  { icon: LucideIcon; accent: string; action: string }
> = {
  budget_change: {
    icon: WalletCards,
    accent: 'bg-amber-100 text-amber-700',
    action: 'Согласовать доплату',
  },
  acceptance_request: {
    icon: Clock3,
    accent: 'bg-blue-100 text-blue-700',
    action: 'Принять этап',
  },
  task: { icon: ListTodo, accent: 'bg-slate-100 text-slate-600', action: 'Взять в работу' },
  decision: { icon: CheckCircle2, accent: 'bg-blue-100 text-blue-700', action: 'Зафиксировать' },
  risk: { icon: AlertTriangle, accent: 'bg-red-100 text-red-700', action: 'Учесть риск' },
  question: { icon: MessageCircle, accent: 'bg-slate-100 text-slate-600', action: 'Ответить' },
}

function LiveEventCard({
  threadId,
  event,
  isNew,
  onShowSources,
}: {
  threadId: string
  event: ConversationEvent
  isNew: boolean
  onShowSources: (ids: number[]) => void
}) {
  const { confirmed, confirmEvent, rejectEvent } = useDemoStore()
  const [showTech, setShowTech] = useState(false)
  const id = eventStableId(threadId, event)
  const isConfirmed = confirmed.has(id)
  const style = typeStyles[event.type]
  const Icon = style.icon
  const detail = event.amountRub
    ? `${event.title} (+${event.amountRub.toLocaleString('ru-RU')} ₽)`
    : event.title

  return (
    <div
      className={`rounded-xl border bg-white p-4 shadow-sm transition-colors ${
        isConfirmed ? 'border-emerald-300' : 'border-slate-200'
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
            isConfirmed ? 'bg-emerald-100 text-emerald-700' : style.accent
          }`}
        >
          <Icon className="h-4.5 w-4.5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-900">{event.title}</p>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
              {typeLabels[event.type]}
            </span>
            {isNew && !isConfirmed && (
              <span className="rounded-full bg-indigo-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                новое
              </span>
            )}
          </div>

          {event.amountRub !== null && (
            <p
              className={`mt-1.5 text-xl font-bold tabular-nums ${
                event.amountRub > 0 ? 'text-amber-700' : 'text-emerald-700'
              }`}
            >
              {event.amountRub > 0 ? '+' : ''}
              {event.amountRub.toLocaleString('ru-RU')} ₽
            </p>
          )}

          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            {event.description}
          </p>

          {isConfirmed ? (
            <p className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-800">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Подтверждено вами · записано в проект
            </p>
          ) : (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => confirmEvent(id, detail, event.mode)}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-slate-700"
              >
                {style.action}
              </button>
              <button
                type="button"
                onClick={() => rejectEvent(id, detail, event.mode)}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
              >
                Это не так
              </button>
              <button
                type="button"
                onClick={() => onShowSources(event.sourceMessageIds)}
                className="text-xs font-medium text-slate-500 underline-offset-2 transition-colors hover:text-slate-800 hover:underline"
              >
                Показать в переписке
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={() => setShowTech((value) => !value)}
            className="mt-2.5 text-[11px] text-slate-400 transition-colors hover:text-slate-600"
          >
            {showTech ? 'Скрыть' : 'Как это получено'}
          </button>

          {showTech && (
            <dl className="mt-2 grid gap-x-4 gap-y-1 border-t border-slate-100 pt-2 text-[11px] text-slate-500 sm:grid-cols-2">
              <div className="flex gap-1.5">
                <dt className="text-slate-400">источники:</dt>
                <dd>
                  {event.sourceMessageIds.map((s) => `сообщение ${s}`).join(', ')}
                </dd>
              </div>
              <div className="flex gap-1.5">
                <dt className="text-slate-400">метод:</dt>
                <dd>{event.detectedBy}</dd>
              </div>
              <div className="flex gap-1.5">
                <dt className="text-slate-400">статус:</dt>
                <dd>{event.state}</dd>
              </div>
              {event.confidence !== null && (
                <div className="flex gap-1.5">
                  <dt className="text-slate-400">уверенность:</dt>
                  <dd>{event.confidence.toFixed(2)}</dd>
                </div>
              )}
            </dl>
          )}
        </div>
      </div>
    </div>
  )
}

function FixtureCard({ threadId }: { threadId: string }) {
  const fixture = fixtureByThread[threadId]
  const { confirmed, confirmEvent } = useDemoStore()
  if (!fixture) return null
  const isConfirmed = confirmed.has(fixture.eventId)
  const Icon = fixture.icon

  return (
    <div
      className={`rounded-xl border bg-white p-4 shadow-sm ${
        isConfirmed ? 'border-emerald-300' : 'border-slate-200'
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
            isConfirmed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
          }`}
        >
          {isConfirmed ? (
            <CheckCircle2 className="h-4.5 w-4.5" />
          ) : (
            <Icon className="h-4.5 w-4.5" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-900">{fixture.title}</p>
            <span
              className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${modeBadgeClasses.DEMO_FIXTURE}`}
              title="сохранённый пример, не результат живого разбора"
            >
              пример
            </span>
          </div>

          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            {fixture.description}
          </p>

          {isConfirmed ? (
            <p className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-800">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Подтверждено вами · записано в проект
            </p>
          ) : (
            fixture.action && (
              <button
                type="button"
                onClick={() =>
                  confirmEvent(fixture.eventId, fixture.title, 'DEMO_FIXTURE')
                }
                className="mt-3 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-slate-700"
              >
                {fixture.action}
              </button>
            )
          )}
        </div>
      </div>
    </div>
  )
}

export default function CoordinatorPanel({
  thread,
  live,
  onRun,
  onShowSources,
  newIds,
  hasLocalMessages = false,
}: {
  thread: Thread
  live: LiveState
  onRun: () => void
  onShowSources: (ids: number[]) => void
  /** Идентификаторы событий, появившихся в последнем прогоне. */
  newIds: ReadonlySet<string>
  /** Человек дописал в ветку — она перестаёт быть демонстрационной. */
  hasLocalMessages?: boolean
}) {
  const isLiveThread = thread.id === LIVE_THREAD_ID || hasLocalMessages

  if (!isLiveThread) {
    return <FixtureCard threadId={thread.id} />
  }

  const events = live.kind === 'done' ? live.events : []

  return (
    <div className="space-y-2.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Sparkles className="h-4 w-4 text-indigo-500" />
          Найдено в переписке
          {events.length > 0 && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">
              {events.length}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onRun}
          disabled={live.kind === 'loading'}
          className="rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-500 transition-colors hover:bg-slate-50 disabled:opacity-40"
        >
          Перечитать
        </button>
      </div>

      {live.kind === 'loading' && <AnalysisProgress />}

      {live.kind === 'done' && events.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
          Решений, требующих вашего участия, в этой ветке нет.
        </div>
      )}

      {events.map((event) => (
        <LiveEventCard
          key={event.id}
          threadId={thread.id}
          event={event}
          isNew={newIds.has(event.id)}
          onShowSources={onShowSources}
        />
      ))}

      {live.kind === 'error' && (
        <>
          <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>
              Разбор недоступен: {live.message}. Ниже — сохранённый результат
              прошлого запуска, он помечен как {' '}
              <span className="font-semibold">DEMO_FIXTURE</span>.
            </span>
          </div>
          <FixtureCard threadId={thread.id} />
        </>
      )}

      {live.kind === 'idle' && <FixtureCard threadId={thread.id} />}

      {live.kind === 'done' && (
        <details className="group rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2">
          <summary className="cursor-pointer list-none text-[11px] text-slate-400 transition-colors hover:text-slate-600">
            Технические детали разбора
          </summary>
          <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
            <span
              className={`rounded-full border px-2 py-0.5 font-semibold ${modeBadgeClasses[live.mode]}`}
            >
              {live.mode}
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-slate-600">
              retrieval: {live.retrieval}
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-slate-600">
              extraction: {live.extraction}
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-slate-600">
              {live.elapsedSec.toFixed(1)} c
            </span>
          </div>
          {live.warnings.length > 0 && (
            <div className="mt-2 space-y-0.5 text-[11px] leading-relaxed text-slate-500">
              <p className="text-slate-400">отклонено валидатором:</p>
              {live.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          )}
        </details>
      )}
    </div>
  )
}
