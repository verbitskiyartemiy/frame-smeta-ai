import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { CheckCircle2 } from 'lucide-react'
import { checkHealth } from './service'
import type { HealthState, RuntimeMode } from './types'
import {
  DemoStoreContext,
  type AuditEntry,
  type LastRun,
} from './context'

export function DemoStoreProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<HealthState | null>(null)
  const [lastRun, setLastRun] = useState<LastRun | null>(null)
  const [confirmed, setConfirmed] = useState<ReadonlySet<string>>(new Set())
  const [audit, setAudit] = useState<AuditEntry[]>([])
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    checkHealth().then((state) => {
      if (!cancelled) setHealth(state)
    })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(null), 3200)
    return () => window.clearTimeout(timer)
  }, [toast])

  const pushAudit = useCallback(
    (action: string, detail: string, mode: RuntimeMode) => {
      const ts = new Date().toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
      })
      setAudit((current) => [{ ts, action, detail, mode }, ...current])
    },
    [],
  )

  const confirmEvent = useCallback(
    (id: string, detail: string, mode: RuntimeMode) => {
      setConfirmed((current) => new Set(current).add(id))
      pushAudit('Подтверждено человеком', detail, mode)
      setToast(`Подтверждено: ${detail}`)
    },
    [pushAudit],
  )

  const rejectEvent = useCallback(
    (_id: string, detail: string, mode: RuntimeMode) => {
      pushAudit('Отклонено человеком', detail, mode)
      setToast(`Отклонено: ${detail}`)
    },
    [pushAudit],
  )

  const value = useMemo(
    () => ({
      health,
      lastRun,
      setLastRun,
      confirmed,
      confirmEvent,
      rejectEvent,
      audit,
    }),
    [health, lastRun, confirmed, confirmEvent, rejectEvent, audit],
  )

  return (
    <DemoStoreContext.Provider value={value}>
      {children}
      {toast && (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white shadow-lg"
        >
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          {toast}
        </div>
      )}
    </DemoStoreContext.Provider>
  )
}
