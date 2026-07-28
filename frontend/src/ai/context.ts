import { createContext, useContext } from 'react'
import type { HealthState, RuntimeMode } from './types'

export interface AuditEntry {
  ts: string
  action: string
  detail: string
  mode: RuntimeMode
}

export interface LastRun {
  mode: RuntimeMode
  retrievalBackend: string
  extractionBackend: string
  elapsedSec: number
}

export interface DemoStoreValue {
  health: HealthState | null
  lastRun: LastRun | null
  setLastRun: (run: LastRun) => void
  confirmed: ReadonlySet<string>
  confirmEvent: (id: string, detail: string, mode: RuntimeMode) => void
  rejectEvent: (id: string, detail: string, mode: RuntimeMode) => void
  audit: AuditEntry[]
}

export const DemoStoreContext = createContext<DemoStoreValue | null>(null)

export function useDemoStore(): DemoStoreValue {
  const value = useContext(DemoStoreContext)
  if (!value) throw new Error('DemoStoreProvider отсутствует в дереве')
  return value
}

export const modeBadgeClasses: Record<RuntimeMode, string> = {
  DEMO_FIXTURE: 'border-amber-200 bg-amber-50 text-amber-700',
  LIVE_HYBRID: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  PARTIAL_HYBRID: 'border-blue-200 bg-blue-50 text-blue-700',
  RULES_ONLY: 'border-slate-300 bg-slate-100 text-slate-600',
}
