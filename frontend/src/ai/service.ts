import type {
  AnalyzeChatResult,
  ChatMessageInput,
  ConversationEvent,
  CorridorPosition,
  EstimateAnalysis,
  EstimateCheck,
  EstimateLineInput,
  EstimateLineResult,
  HealthState,
  RuntimeMode,
} from './types'

const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  'http://127.0.0.1:8000'

const ANALYZE_TIMEOUT_MS = 120_000
const ESTIMATE_TIMEOUT_MS = 15_000
const SIMULATE_TIMEOUT_MS = 45_000
const ASSISTANT_TIMEOUT_MS = 60_000
const HEALTH_TIMEOUT_MS = 4_000

async function fetchJson(
  path: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<unknown> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new Error(`API ответил ${response.status}`)
    }
    return (await response.json()) as unknown
  } finally {
    window.clearTimeout(timer)
  }
}

export async function checkHealth(): Promise<HealthState> {
  try {
    const raw = (await fetchJson('/api/health', { method: 'GET' },
      HEALTH_TIMEOUT_MS)) as Record<string, unknown>
    return {
      reachable: raw.status === 'ok',
      llmConfigured: raw.llm_configured === true,
      provider: typeof raw.provider === 'string' ? raw.provider : '—',
    }
  } catch {
    return { reachable: false, llmConfigured: false, provider: '—' }
  }
}

function asMode(value: unknown): RuntimeMode {
  return value === 'LIVE_HYBRID' || value === 'PARTIAL_HYBRID' ||
    value === 'RULES_ONLY'
    ? value
    : 'RULES_ONLY'
}

function mapEvent(raw: Record<string, unknown>, mode: RuntimeMode):
  ConversationEvent | null {
  const type = raw.event_type
  if (
    type !== 'task' && type !== 'decision' && type !== 'budget_change' &&
    type !== 'acceptance_request' && type !== 'risk' && type !== 'question'
  ) {
    return null
  }
  const sources = Array.isArray(raw.source_message_ids)
    ? raw.source_message_ids.filter((v): v is number => typeof v === 'number')
    : []
  if (sources.length === 0) return null
  return {
    id: String(raw.event_id ?? `event_${sources[0]}`),
    type,
    title: String(raw.title ?? ''),
    description: String(raw.description ?? ''),
    state: String(raw.workflow_state ?? 'pending'),
    amountRub: typeof raw.amount_rub === 'number' ? raw.amount_rub : null,
    deadlineText:
      typeof raw.deadline_text === 'string' ? raw.deadline_text : null,
    assignee: typeof raw.assignee === 'string' ? raw.assignee : null,
    sourceMessageIds: sources,
    confidence: typeof raw.confidence === 'number' ? raw.confidence : null,
    detectedBy: String(raw.detected_by ?? 'rules'),
    reason: String(raw.reason ?? ''),
    mode,
  }
}

function corridorPosition(
  price: number,
  p10: number,
  p90: number,
): CorridorPosition {
  if (price > p90) return 'above'
  if (price < p10) return 'below'
  return 'inside'
}

function mapEstimateLine(raw: Record<string, unknown>): EstimateLineResult {
  const unitPrice = Number(raw.unit_price ?? 0)
  const corridor = raw.corridor as Record<string, unknown> | undefined
  const base: EstimateLineResult = {
    rawName: String(raw.raw_name ?? ''),
    normalizedWork:
      typeof raw.normalized_work === 'string' ? raw.normalized_work : null,
    unitPrice,
    quantity: Number(raw.quantity ?? 1),
    reason: String(raw.reason ?? ''),
    benchmark: null,
  }
  if (raw.assessment !== 'benchmarked' || !corridor) return base

  const p10 = Number(corridor.p10)
  const p90 = Number(corridor.p90)
  const median = Number(raw.median_benchmark)
  if (!Number.isFinite(p10) || !Number.isFinite(p90) || !Number.isFinite(median)) {
    return base
  }
  return {
    ...base,
    benchmark: {
      median,
      p10,
      p90,
      deviationPct: Number(raw.deviation_pct ?? 0),
      sampleSize: Number(raw.sample_size ?? 0),
      position: corridorPosition(unitPrice, p10, p90),
    },
  }
}

export async function analyzeEstimate(
  lines: EstimateLineInput[],
): Promise<EstimateAnalysis> {
  const raw = (await fetchJson(
    '/api/estimate/analyze',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lines: lines.map(({ name, qty, price, amount }) => ({
          name, qty, price, amount,
        })),
      }),
    },
    ESTIMATE_TIMEOUT_MS,
  )) as Record<string, unknown>

  const rawItems = Array.isArray(raw.items) ? raw.items : []
  const coverage = (raw.coverage ?? {}) as Record<string, unknown>
  return {
    live: true,
    items: rawItems.map((item) => mapEstimateLine(item as Record<string, unknown>)),
    matched: Number(coverage.matched ?? 0),
    total: Number(coverage.total ?? rawItems.length),
    source: String(raw.source ?? ''),
    minSample: Number(raw.min_sample ?? 5),
    checks: Array.isArray(raw.checks)
      ? (raw.checks as Record<string, unknown>[]).map((c) => ({
          kind: c.kind as EstimateCheck['kind'],
          line: typeof c.line === 'number' ? c.line : null,
          title: String(c.title ?? ''),
          detail: String(c.detail ?? ''),
        }))
      : [],
  }
}

export interface ProjectFact {
  id: number
  text: string
}

export interface ProposedAction {
  title: string
  why: string
}

export interface AssistantAnswer {
  answered: boolean
  answer: string
  sourceIds: number[]
  quotes: string[]
  knowledgeSourceIds: string[]
  knowledgeQuotes: string[]
  reason: string
  knowledgeUsed: string[]
  retrieval: string
  action: ProposedAction | null
}

/**
 * Ответ по фактам проекта. Числа считает продукт, модель их только
 * переписывает — бэкенд отклоняет ответ, если в нём появилась сумма,
 * которой нет ни в одном процитированном факте.
 */
export async function askAssistant(
  question: string,
  facts: ProjectFact[],
): Promise<AssistantAnswer> {
  const raw = (await fetchJson(
    '/api/assistant/ask',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, facts }),
    },
    ASSISTANT_TIMEOUT_MS,
  )) as Record<string, unknown>

  const rawAction = raw.proposed_action as Record<string, unknown> | null
  const title =
    rawAction && typeof rawAction.title === 'string' ? rawAction.title.trim() : ''

  return {
    answered: raw.answered === true,
    answer: typeof raw.answer === 'string' ? raw.answer : '',
    sourceIds: Array.isArray(raw.source_ids)
      ? raw.source_ids.filter((v): v is number => typeof v === 'number')
      : [],
    quotes: Array.isArray(raw.quotes)
      ? raw.quotes.filter((v): v is string => typeof v === 'string')
      : [],
    knowledgeSourceIds: Array.isArray(raw.knowledge_source_ids)
      ? raw.knowledge_source_ids.filter((v): v is string => typeof v === 'string')
      : [],
    knowledgeQuotes: Array.isArray(raw.knowledge_quotes)
      ? raw.knowledge_quotes.filter((v): v is string => typeof v === 'string')
      : [],
    reason: typeof raw.reason === 'string' ? raw.reason : '',
    knowledgeUsed: Array.isArray(raw.knowledge_used)
      ? raw.knowledge_used.filter((v): v is string => typeof v === 'string')
      : [],
    retrieval: typeof raw.retrieval === 'string' ? raw.retrieval : 'none',
    action: title
      ? { title, why: typeof rawAction?.why === 'string' ? rawAction.why : '' }
      : null,
  }
}

export interface SimulatedReply {
  text: string
  author: string
  role: string
}

/** Собеседник для демо. Ответ всегда помечен как сгенерированный. */
export async function simulateReply(
  messages: ChatMessageInput[],
  project: string,
): Promise<SimulatedReply> {
  const raw = (await fetchJson(
    '/api/simulate/reply',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, project }),
    },
    SIMULATE_TIMEOUT_MS,
  )) as Record<string, unknown>

  const text = typeof raw.text === 'string' ? raw.text.trim() : ''
  if (!text) throw new Error('модель вернула пустую реплику')
  return {
    text,
    author: typeof raw.author === 'string' ? raw.author : 'Прораб',
    role: typeof raw.role === 'string' ? raw.role : 'Прораб',
  }
}

export async function analyzeChat(
  messages: ChatMessageInput[],
  project: string,
): Promise<AnalyzeChatResult> {
  const raw = (await fetchJson(
    '/api/coordinator/analyze',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, project, use_embeddings: true }),
    },
    ANALYZE_TIMEOUT_MS,
  )) as Record<string, unknown>

  const mode = asMode(raw.mode)
  const rawEvents = Array.isArray(raw.events) ? raw.events : []
  const events = rawEvents
    .map((item) => mapEvent(item as Record<string, unknown>, mode))
    .filter((item): item is ConversationEvent => item !== null)

  const rawErrors = Array.isArray(raw.errors) ? raw.errors : []
  const warnings = rawErrors.map((item) => {
    const record = item as Record<string, unknown>
    return String(record.reason ?? JSON.stringify(record))
  })

  const stats = (raw.stats ?? {}) as Record<string, unknown>
  return {
    mode,
    retrievalBackend:
      raw.retrieval_backend === 'gigachat_embeddings' ||
      raw.retrieval_backend === 'local_embeddings'
        ? raw.retrieval_backend
        : 'rules',
    extractionBackend: raw.extraction_backend === 'gigachat'
      ? 'gigachat'
      : 'rules',
    events,
    warnings,
    elapsedSec: typeof raw.elapsed_sec === 'number' ? raw.elapsed_sec : 0,
    stats: {
      messages: Number(stats.messages ?? messages.length),
      candidates: Number(stats.candidates ?? 0),
      liveChunks: Number(stats.live_chunks ?? 0),
      chunks: Number(stats.chunks ?? 0),
    },
  }
}
