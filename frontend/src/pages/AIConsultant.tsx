import { useEffect, useRef, useState } from 'react'
import { modeBadgeClasses, useDemoStore } from '../ai/context'
import { askAssistant } from '../ai/service'
import { buildProjectFacts } from '../ai/projectFacts'
import type { RuntimeMode } from '../ai/types'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Clock3,
  Database,
  FileSearch,
  FlaskConical,
  Loader2,
  MessageSquareText,
  Send,
  ShieldCheck,
  Sparkles,
  User,
} from 'lucide-react'

interface ChatMessage {
  role: 'assistant' | 'user'
  text: string
  sources?: string[]
  method?: string
  refused?: boolean
  knowledge?: string[]
  /** Предложение помощника. Выполняется только после подтверждения. */
  action?: { id: string; title: string; why: string; mode: RuntimeMode }
}

const quickActions = [
  'Что требует моего решения?',
  'Что проверить перед приёмкой электрики?',
  'Покажи изменения бюджета',
  'Какие задачи ждут ответа?',
]

const initialMessage: ChatMessage = {
  role: 'assistant',
  text: 'Я собрал только подтверждённые факты из сметы и переписки проекта. Сейчас от вас требуется два решения: согласовать доплату 12 000 ₽ за замену проводки и ответить по приёмке плитки.',
  sources: ['Электрика · сообщения #1–#4', 'Ванная · сообщение #2'],
  method: 'координатор переписки',
}

export default function AIConsultant() {
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const { health, lastRun, confirmed, confirmEvent, audit } = useDemoStore()
  const budgetConfirmed = confirmed.has('e0-budget')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  async function handleSend(text?: string) {
    const value = (text ?? input).trim()
    if (!value || isThinking) return

    setMessages((current) => [...current, { role: 'user', text: value }])
    setInput('')
    setIsThinking(true)

    try {
      const facts = buildProjectFacts(audit)
      const result = await askAssistant(value, facts)
      setMessages((current) => [
        ...current,
        result.answered
          ? {
              role: 'assistant',
              text: result.answer,
              sources: [
                ...result.quotes,
                ...result.knowledgeQuotes.map((quote) => `База знаний: ${quote}`),
              ],
              method:
                result.retrieval === 'gigachat_embeddings'
                  ? 'факты проекта + смысловой поиск'
                  : result.retrieval === 'lexical'
                    ? 'факты проекта + поиск по словам'
                    : 'факты проекта',
              knowledge: result.knowledgeUsed,
              action: result.action
                ? {
                    id: `act-${Date.now()}`,
                    title: result.action.title,
                    why: result.action.why,
                    mode:
                      result.retrieval === 'gigachat_embeddings'
                        ? 'LIVE_HYBRID'
                        : 'PARTIAL_HYBRID',
                  }
                : undefined,
            }
          : {
              role: 'assistant',
              text:
                result.reason ||
                'В данных проекта нет того, о чём вы спрашиваете.',
              method: 'отказ',
              refused: true,
            },
      ])
    } catch (error) {
      // Кэшированный ответ за живой не выдаём: честно говорим, что ассистент не отвечает.
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text:
            'Ассистент сейчас недоступен: ' +
            (error instanceof Error ? error.message : 'нет связи с сервисом') +
            '. Ответ по данным проекта не сформирован.',
          method: 'сервис недоступен',
          refused: true,
        },
      ])
    } finally {
      setIsThinking(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
              <Sparkles className="h-3.5 w-3.5" />
              AI-контроль проекта
            </span>
            <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
              ДЕМО-СЦЕНАРИЙ
            </span>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                lastRun
                  ? modeBadgeClasses[lastRun.mode]
                  : health?.reachable
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                    : 'border-slate-300 bg-slate-100 text-slate-500'
              }`}
            >
              {lastRun
                ? `последний live-прогон: ${lastRun.mode}`
                : health === null
                  ? 'проверяю backend…'
                  : health.reachable
                    ? `backend доступен · ${health.llmConfigured ? 'LLM настроена' : 'без ключа'}`
                    : 'backend офлайн'}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">
            Решения, которые нельзя потерять в чатах и сметах
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            AI находит событие, привязывает его к исходным сообщениям и просит человека подтвердить действие.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-600 shadow-sm">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          Ответы только с источниками
        </div>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <h2 className="font-bold text-slate-900">Изменение бюджета</h2>
            </div>
            <span className="text-lg font-bold text-slate-900">+12 000 ₽</span>
          </div>
          <p className="text-sm leading-relaxed text-slate-600">
            Полная замена старой проводки согласована в диалоге, но ещё не внесена в бюджет.
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {['#1 сумма', '#2 уточнение', '#3 риск', '#4 согласие'].map((source) => (
              <span key={source} className="rounded-md bg-white px-2 py-1 text-[11px] font-medium text-slate-600">
                {source}
              </span>
            ))}
          </div>
          <button
            type="button"
            onClick={() =>
              confirmEvent('e0-budget', 'Доплата за замену проводки (+12 000 ₽)', 'DEMO_FIXTURE')
            }
            disabled={budgetConfirmed}
            className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-amber-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-amber-700 disabled:bg-emerald-600"
          >
            {budgetConfirmed ? (
              <>
                <CheckCircle2 className="h-4 w-4" />
                Подтверждено человеком
              </>
            ) : (
              'Подтвердить доплату'
            )}
          </button>
        </div>

        <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-5">
          <div className="mb-3 flex items-center gap-2">
            <Clock3 className="h-5 w-5 text-blue-600" />
            <h2 className="font-bold text-slate-900">Ждёт ответа</h2>
          </div>
          <p className="text-sm leading-relaxed text-slate-600">
            Исполнитель просит принять укладку плитки. В ветке нет ответа заказчика.
          </p>
          <div className="mt-4 rounded-lg bg-white px-3 py-2 text-xs text-slate-600">
            Источник: «Ванная · Приёмка работ · #2»
          </div>
          <Link
            to="/messages"
            className="mt-4 inline-flex w-full items-center justify-center rounded-lg border border-blue-200 bg-white px-4 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-50"
          >
            Открыть диалог
          </Link>
        </div>

        <div className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5">
          <div className="mb-3 flex items-center gap-2">
            <FileSearch className="h-5 w-5 text-indigo-600" />
            <h2 className="font-bold text-slate-900">Проверка сметы</h2>
          </div>
          <p className="text-sm leading-relaxed text-slate-600">
            13 из 14 позиций сопоставлены. Две позиции требуют уточнения условий и состава работ.
          </p>
          <div className="mt-4 rounded-lg bg-white px-3 py-2 text-xs text-slate-600">
            2 369 цен · 22 компании · 7 городов
          </div>
          <Link
            to="/estimates"
            className="mt-4 inline-flex w-full items-center justify-center rounded-lg border border-indigo-200 bg-white px-4 py-2.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-50"
          >
            Открыть сверку
          </Link>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <section className="flex min-h-[540px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">Помощник по проекту</h2>
                <p className="text-xs text-slate-500">Переписка + смета, без ответов «из головы»</p>
              </div>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
              DEMO_FIXTURE
            </span>
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto bg-slate-50/70 px-5 py-5">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  message.role === 'assistant' ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-600'
                }`}>
                  {message.role === 'assistant' ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                </div>
                <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  message.role === 'assistant'
                    ? 'rounded-tl-sm border border-slate-100 bg-white text-slate-700 shadow-sm'
                    : 'rounded-tr-sm bg-indigo-600 text-white'
                }`}>
                  <p>{message.text}</p>
                  {message.sources && (
                    <div className="mt-3 border-t border-slate-100 pt-2.5">
                      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-slate-400">Источники</p>
                      <div className="flex flex-wrap gap-1.5">
                        {message.sources.map((source) => (
                          <span key={source} className="rounded-md bg-slate-50 px-2 py-1 text-[11px] text-slate-600">
                            {source}
                          </span>
                        ))}
                      </div>
                      {message.knowledge && message.knowledge.length > 0 && (
                        <p className="mt-1.5 text-[11px] text-slate-500">
                          Требования к этапам: {message.knowledge.join(', ')}
                        </p>
                      )}
                      {message.method && (
                        <p className="mt-2 text-[11px] text-slate-400">Метод: {message.method}</p>
                      )}
                    </div>
                  )}

                  {message.action && (
                    <div className="mt-3 rounded-xl border-2 border-slate-900 bg-white p-3">
                      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                        Предложенное действие
                      </p>
                      <p className="mt-1 text-sm font-semibold text-slate-900">
                        {message.action.title}
                      </p>
                      {message.action.why && (
                        <p className="mt-0.5 text-xs text-slate-500">{message.action.why}</p>
                      )}
                      {confirmed.has(message.action.id) ? (
                        <p className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-800">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Задача создана
                        </p>
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            confirmEvent(
                              message.action!.id,
                              message.action!.title,
                              message.action!.mode,
                            )
                          }
                          className="mt-2 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-slate-700"
                        >
                          Создать напоминание
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isThinking && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />
                Проверяю источники проекта…
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-slate-100 p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              {quickActions.map((action) => (
                <button
                  key={action}
                  type="button"
                  onClick={() => handleSend(action)}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
                >
                  {action}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') handleSend()
                }}
                placeholder="Спросите о решениях, смете или переписке…"
                className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
              />
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!input.trim() || isThinking}
                aria-label="Отправить"
                className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>

        <aside className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-bold text-slate-900">Как получен результат</h2>
            <div className="space-y-3 text-xs text-slate-600">
              <div className="flex items-start gap-2">
                <Database className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500" />
                <span>Embeddings находят связанные сообщения, даже если формулировки отличаются.</span>
              </div>
              <div className="flex items-start gap-2">
                <MessageSquareText className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500" />
                <span>GigaChat извлекает тип события, сумму, срок и участников.</span>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500" />
                <span>Валидатор проверяет источники. Действие выполняется только после подтверждения.</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5">
            <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">Проверка пайплайна</p>
            <p className="mt-2 text-3xl font-bold text-slate-900">F1 0.95</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">
              На авторском синтетическом корпусе: 45 сообщений, 19 событий. Это не продуктовая точность.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-sm font-bold text-slate-900">Журнал подтверждений</h2>
            {audit.length === 0 ? (
              <p className="text-xs text-slate-400">
                Пока пусто: действия появляются после подтверждения человеком.
              </p>
            ) : (
              <ul className="space-y-2 text-xs text-slate-600">
                {audit.slice(0, 5).map((entry) => (
                  <li key={`${entry.ts}-${entry.detail}`} className="rounded-lg bg-slate-50 px-3 py-2">
                    <span className="font-semibold text-slate-800">{entry.ts}</span>{' '}
                    {entry.action}: {entry.detail}
                    <span className="ml-1 text-[10px] text-slate-400">({entry.mode})</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5">
            <div className="mb-2 flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-slate-500" />
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">R&amp;D, не выпущено</p>
            </div>
            <p className="text-sm font-semibold text-slate-800">Аспектный рейтинг подрядчиков</p>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              Привязка аспектов: 0.618. Quality gate не пройден — фича остаётся в исследовании.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
