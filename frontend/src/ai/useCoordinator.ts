import { useCallback, useRef, useState } from 'react'
import type { ThreadMessage } from '../data/mock'
import { analyzeChat } from './service'
import { useDemoStore } from './context'
import type { ConversationEvent, RuntimeMode } from './types'

export type LiveState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | {
      kind: 'done'
      mode: RuntimeMode
      retrieval: string
      extraction: string
      elapsedSec: number
      events: ConversationEvent[]
      warnings: string[]
    }
  | { kind: 'error'; message: string }

/**
 * Разбор переписки живёт на странице, а не внутри карточки: сообщение
 * отправляется и сразу передаёт новый список в run, поэтому не нужен эффект,
 * гоняющий рендеры следом за состоянием.
 */
export function useCoordinator(project: string) {
  const [live, setLive] = useState<LiveState>({ kind: 'idle' })
  const [newIds, setNewIds] = useState<ReadonlySet<string>>(new Set())
  const seenIds = useRef<Set<string>>(new Set())
  const { setLastRun } = useDemoStore()

  const run = useCallback(
    async (messages: ThreadMessage[]) => {
      setLive({ kind: 'loading' })
      try {
        const result = await analyzeChat(
          messages.map((message, index) => ({
            id: index + 1,
            author: message.author,
            ts: message.date,
            text: message.text,
          })),
          project,
        )
        setLastRun({
          mode: result.mode,
          retrievalBackend: result.retrievalBackend,
          extractionBackend: result.extractionBackend,
          elapsedSec: result.elapsedSec,
        })
        // Новым считается событие, которого не было ни в одном прошлом
        // прогоне этой ветки: так карточки прирастают, а не мигают заново.
        const fresh = new Set(
          result.events.map((e) => e.id).filter((id) => !seenIds.current.has(id)),
        )
        for (const event of result.events) seenIds.current.add(event.id)
        setNewIds(fresh)
        setLive({
          kind: 'done',
          mode: result.mode,
          retrieval: result.retrievalBackend,
          extraction: result.extractionBackend,
          elapsedSec: result.elapsedSec,
          events: result.events,
          warnings: result.warnings,
        })
      } catch (error) {
        setLive({
          kind: 'error',
          message:
            error instanceof Error ? error.message : 'неизвестная ошибка сети',
        })
      }
    },
    [project, setLastRun],
  )

  const reset = useCallback(() => {
    setLive({ kind: 'idle' })
    setNewIds(new Set())
    seenIds.current = new Set()
  }, [])

  return { live, run, reset, newIds }
}
