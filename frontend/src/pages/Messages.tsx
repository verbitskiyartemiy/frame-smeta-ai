import { useState } from 'react'
import {
  Bot,
  Loader2,
  MessageSquare,
  Paperclip,
  Send,
  Sparkles,
} from 'lucide-react'
import { threads, type Thread, type ThreadMessage } from '../data/mock'
import CoordinatorPanel from '../ai/CoordinatorPanel'
import { simulateReply } from '../ai/service'
import { useCoordinator } from '../ai/useCoordinator'
import { useDemoStore } from '../ai/context'

type FilterTab = 'all' | 'open' | 'waiting' | 'resolved'

const filterLabels: Record<FilterTab, string> = {
  all: 'Все',
  open: 'Открытые',
  waiting: 'Ожидают ответа',
  resolved: 'Решённые',
}

const statusColors: Record<Thread['status'], string> = {
  open: 'bg-red-500',
  waiting: 'bg-yellow-400',
  resolved: 'bg-green-500',
}

const statusLabels: Record<Thread['status'], string> = {
  open: 'Открыт',
  waiting: 'Ожидает ответа',
  resolved: 'Решён',
}

const statusBadgeColors: Record<Thread['status'], string> = {
  open: 'bg-red-100 text-red-700',
  waiting: 'bg-yellow-100 text-yellow-700',
  resolved: 'bg-green-100 text-green-700',
}

const zoneColors: Record<string, string> = {
  'Кухня': 'bg-orange-100 text-orange-700',
  'Спальня': 'bg-purple-100 text-purple-700',
  'Ванная': 'bg-cyan-100 text-cyan-700',
  'Вся квартира': 'bg-gray-100 text-gray-600',
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
}

const roleAvatarColors: Record<string, string> = {
  'Заказчик': 'bg-blue-600',
  'Прораб': 'bg-amber-600',
  'Электрик': 'bg-yellow-500',
  'Дизайнер': 'bg-pink-500',
  'Плиточник': 'bg-teal-600',
  'Сантехник': 'bg-indigo-500',
}

const roleBadgeColors: Record<string, string> = {
  'Заказчик': 'bg-blue-100 text-blue-700',
  'Прораб': 'bg-amber-100 text-amber-700',
  'Электрик': 'bg-yellow-100 text-yellow-700',
  'Дизайнер': 'bg-pink-100 text-pink-700',
  'Плиточник': 'bg-teal-100 text-teal-700',
  'Сантехник': 'bg-indigo-100 text-indigo-700',
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const PROJECT = 'Квартира на Невском, ремонт под ключ'

const speakerPresets = {
  customer: { author: 'Вы', role: 'Заказчик', label: 'от заказчика' },
  contractor: { author: 'Игорь', role: 'Прораб', label: 'от подрядчика' },
} as const

type Speaker = keyof typeof speakerPresets

export default function Messages() {
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all')
  const [selectedThreadId, setSelectedThreadId] = useState<string>(threads[0]?.id ?? '')
  const { health, lastRun } = useDemoStore()

  const [added, setAdded] = useState<Record<string, ThreadMessage[]>>({})
  const { live, run, reset, newIds } = useCoordinator(PROJECT)
  const [highlighted, setHighlighted] = useState<ReadonlySet<number>>(new Set())
  const [draft, setDraft] = useState('')
  const [speaker, setSpeaker] = useState<Speaker>('contractor')
  const [simulating, setSimulating] = useState(false)
  const [simError, setSimError] = useState<string | null>(null)

  const filteredThreads =
    activeFilter === 'all'
      ? threads
      : threads.filter((t) => t.status === activeFilter)

  const selectedThread = threads.find((t) => t.id === selectedThreadId) ?? threads[0]

  const openCount = threads.filter((t) => t.status === 'open').length

  const conversation = selectedThread
    ? [...selectedThread.messages, ...(added[selectedThread.id] ?? [])]
    : []

  // Разбор запускается сразу с новым списком: ждать, пока состояние
  // доедет до рендера, не нужно.
  function appendMessage(message: ThreadMessage) {
    const threadId = selectedThread.id
    setAdded((current) => ({
      ...current,
      [threadId]: [...(current[threadId] ?? []), message],
    }))
    void run([...conversation, message])
  }

  // Источник события — порядковый номер сообщения в ветке, поэтому
  // подсветка ищет элемент по этому же номеру.
  function showSources(ids: number[]) {
    setHighlighted(new Set(ids))
    const first = document.getElementById(`msg-${ids[0]}`)
    first?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  function sendDraft() {
    const text = draft.trim()
    if (!text || !selectedThread) return
    const preset = speakerPresets[speaker]
    appendMessage({
      id: `local-${selectedThread.id}-${conversation.length + 1}`,
      author: preset.author,
      role: preset.role,
      text,
      date: new Date().toISOString().slice(0, 10),
    })
    setDraft('')
    setSimError(null)
  }

  async function askContractor() {
    if (!selectedThread || simulating) return
    setSimulating(true)
    setSimError(null)
    try {
      const reply = await simulateReply(
        conversation.map((message, index) => ({
          id: index + 1,
          author: message.author,
          ts: message.date,
          text: message.text,
        })),
        PROJECT,
      )
      appendMessage({
        id: `sim-${selectedThread.id}-${conversation.length + 1}`,
        author: reply.author,
        role: reply.role,
        text: reply.text,
        date: new Date().toISOString().slice(0, 10),
      })
    } catch (error) {
      setSimError(
        error instanceof Error ? error.message : 'собеседник недоступен',
      )
    } finally {
      setSimulating(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="mb-4 flex items-start justify-between gap-4 rounded-xl border border-indigo-200 bg-gradient-to-r from-indigo-50 to-blue-50 px-4 py-3">
        <div className="flex items-start gap-3">
          <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
          <div>
            <p className="text-sm font-semibold text-indigo-900">AI-координатор переписки</p>
            <p className="text-xs leading-relaxed text-indigo-700">
              Связывает реплики в задачи, решения, риски и изменения бюджета. Каждая карточка содержит источники и требует подтверждения человека.
            </p>
          </div>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
            health?.reachable
              ? 'border-emerald-200 bg-white text-emerald-700'
              : 'border-slate-300 bg-white text-slate-500'
          }`}
          title={
            lastRun
              ? `${lastRun.mode} · ${lastRun.retrievalBackend} · ${lastRun.extractionBackend}`
              : undefined
          }
        >
          {health?.reachable ? 'AI подключён' : 'AI недоступен · показаны примеры'}
        </span>
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex w-2/5 flex-col border-r border-slate-200">
          <div className="border-b border-slate-200 px-5 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-900">Сообщения</h1>
                {openCount > 0 && (
                  <span className="inline-flex items-center justify-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                    {openCount}
                  </span>
                )}
              </div>
            </div>
            <div className="mt-3 flex gap-1">
              {(Object.keys(filterLabels) as FilterTab[]).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveFilter(tab)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                    activeFilter === tab
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
                  }`}
                >
                  {filterLabels[tab]}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredThreads.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-sm text-slate-400">
                <MessageSquare className="mb-2 h-8 w-8" />
                Нет сообщений
              </div>
            ) : (
              filteredThreads.map((thread) => {
                const lastMessage = thread.messages[thread.messages.length - 1]
                const isSelected = thread.id === selectedThreadId
                return (
                  <button
                    key={thread.id}
                    type="button"
                    onClick={() => {
                      setSelectedThreadId(thread.id)
                      reset()
                      setSimError(null)
                    }}
                    className={`w-full border-b border-slate-100 px-5 py-4 text-left transition-colors ${
                      isSelected ? 'bg-slate-50' : 'hover:bg-slate-50/50'
                    }`}
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                        {thread.title}
                      </h3>
                      <div className="flex shrink-0 items-center gap-2">
                        <span className="text-xs text-slate-400">{formatDate(thread.date)}</span>
                        <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${statusColors[thread.status]}`} />
                      </div>
                    </div>
                    <div className="mb-2 flex flex-wrap gap-1.5">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${
                          zoneColors[thread.zone] ?? 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {thread.zone}
                      </span>
                      <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                        {thread.stage}
                      </span>
                    </div>
                    {lastMessage && (
                      <p className="mb-1.5 truncate text-xs text-slate-500">
                        {lastMessage.author}: {lastMessage.text}
                      </p>
                    )}
                    <p className="text-xs text-slate-400">
                      {thread.author} &middot; {thread.authorRole}
                    </p>
                  </button>
                )
              })
            )}
          </div>
        </div>

        {selectedThread ? (
          <div className="flex w-3/5 flex-col">
            <div className="border-b border-slate-200 px-6 py-4">
              <div className="mb-2 flex items-start justify-between">
                <h2 className="text-base font-bold text-slate-900">{selectedThread.title}</h2>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    statusBadgeColors[selectedThread.status]
                  }`}
                >
                  {statusLabels[selectedThread.status]}
                </span>
              </div>
              <div className="flex gap-1.5">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    zoneColors[selectedThread.zone] ?? 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {selectedThread.zone}
                </span>
                <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
                  {selectedThread.stage}
                </span>
              </div>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
              <CoordinatorPanel
                thread={selectedThread}
                live={live}
                onRun={() => void run(conversation)}
                onShowSources={showSources}
                newIds={newIds}
                hasLocalMessages={(added[selectedThread.id] ?? []).length > 0}
              />
              {conversation.map((msg, index) => {
                const isCustomer = msg.role === 'Заказчик'
                const isHighlighted = highlighted.has(index + 1)
                const avatarColor = roleAvatarColors[msg.role] ?? 'bg-slate-500'
                const badgeColor = roleBadgeColors[msg.role] ?? 'bg-slate-100 text-slate-600'
                return (
                  <div
                    key={msg.id}
                    id={`msg-${index + 1}`}
                    className={`flex gap-3 rounded-xl transition-colors ${
                      isCustomer ? 'flex-row-reverse' : ''
                    } ${isHighlighted ? 'bg-indigo-50 ring-2 ring-indigo-200 p-2 -m-2' : ''}`}
                  >
                    <div
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white ${avatarColor}`}
                    >
                      {getInitials(msg.author)}
                    </div>
                    <div className={`max-w-[75%] ${isCustomer ? 'items-end' : 'items-start'}`}>
                      <div className={`mb-1 flex items-center gap-2 ${isCustomer ? 'justify-end' : ''}`}>
                        <span className="text-sm font-medium text-slate-900">{msg.author}</span>
                        <span className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-medium ${badgeColor}`}>
                          {msg.role}
                        </span>
                      </div>
                      <div
                        className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                          isCustomer
                            ? 'rounded-tr-sm bg-blue-600 text-white'
                            : 'rounded-tl-sm bg-slate-100 text-slate-800'
                        }`}
                      >
                        {msg.text}
                      </div>
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div className={`mt-1.5 flex flex-wrap gap-1.5 ${isCustomer ? 'justify-end' : ''}`}>
                          {msg.attachments.map((file) => (
                            <span
                              key={file}
                              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600"
                            >
                              <Paperclip className="h-3 w-3 text-slate-400" />
                              {file}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className={`mt-1 text-[11px] text-slate-400 ${isCustomer ? 'text-right' : ''}`}>
                        {formatDate(msg.date)}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="border-t border-slate-200 px-6 py-4">
              <div className="mb-2.5 flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-medium text-slate-400">
                  Пишу
                </span>
                <div className="flex rounded-lg border border-slate-200 p-0.5">
                  {(Object.keys(speakerPresets) as Speaker[]).map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setSpeaker(key)}
                      className={`rounded-md px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                        speaker === key
                          ? 'bg-slate-900 text-white'
                          : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      {speakerPresets[key].label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={askContractor}
                  disabled={simulating}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700 transition-colors hover:bg-indigo-100 disabled:opacity-50"
                >
                  {simulating ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Bot className="h-3 w-3" />
                  )}
                  {simulating ? 'Подрядчик печатает…' : 'Пусть ответит подрядчик'}
                </button>
                <span className="text-[11px] text-slate-400">
                  реплика генерируется моделью — это стенд, а не живой человек
                </span>
              </div>

              {simError && (
                <p className="mb-2 text-[11px] text-red-600">
                  Собеседник недоступен: {simError}. Напишите реплику руками —
                  координатор разберёт её так же.
                </p>
              )}

              <div className="flex items-end gap-3">
                <button
                  type="button"
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-slate-400 transition-colors hover:bg-slate-50 hover:text-slate-600"
                >
                  <Paperclip className="h-5 w-5" />
                </button>
                <div className="flex-1">
                  <input
                    type="text"
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') sendDraft()
                    }}
                    placeholder={`Написать ${speakerPresets[speaker].label}…`}
                    className="w-full rounded-lg border border-slate-200 px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={sendDraft}
                  disabled={!draft.trim()}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:bg-slate-300"
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex w-3/5 items-center justify-center text-sm text-slate-400">
            Выберите тему для просмотра
          </div>
        )}
      </div>
    </div>
  )
}
