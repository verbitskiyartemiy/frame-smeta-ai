export type RuntimeMode =
  | 'DEMO_FIXTURE'
  | 'LIVE_HYBRID'
  | 'PARTIAL_HYBRID'
  | 'RULES_ONLY'

export type EventType =
  | 'task'
  | 'decision'
  | 'budget_change'
  | 'acceptance_request'
  | 'risk'
  | 'question'

export interface ConversationEvent {
  id: string
  type: EventType
  title: string
  description: string
  state: string
  amountRub: number | null
  deadlineText: string | null
  assignee: string | null
  sourceMessageIds: number[]
  confidence: number | null
  detectedBy: string
  reason: string
  mode: RuntimeMode
}

export interface AnalyzeChatResult {
  mode: RuntimeMode
  retrievalBackend: 'gigachat_embeddings' | 'local_embeddings' | 'rules'
  extractionBackend: 'gigachat' | 'rules'
  events: ConversationEvent[]
  warnings: string[]
  elapsedSec: number
  stats: {
    messages: number
    candidates: number
    liveChunks: number
    chunks: number
  }
}

export type CorridorPosition = 'inside' | 'above' | 'below'

export interface EstimateCheck {
  kind: 'line_mismatch' | 'duplicate' | 'total_mismatch'
  line: number | null
  title: string
  detail: string
}

export interface EstimateLineInput {
  name: string
  unit: string
  qty: number
  price: number
  /** Заявленная в смете сумма строки — по ней проверяется арифметика. */
  amount?: number
}

export interface EstimateLineResult {
  rawName: string
  normalizedWork: string | null
  unitPrice: number
  quantity: number
  reason: string
  benchmark: {
    median: number
    p10: number
    p90: number
    deviationPct: number
    sampleSize: number
    position: CorridorPosition
  } | null
}

export interface EstimateAnalysis {
  live: boolean
  items: EstimateLineResult[]
  matched: number
  total: number
  source: string
  minSample: number
  checks: EstimateCheck[]
}

export interface HealthState {
  reachable: boolean
  llmConfigured: boolean
  provider: string
}

export interface ChatMessageInput {
  id: number
  author: string
  ts: string
  text: string
}
