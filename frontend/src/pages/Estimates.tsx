import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  FileSpreadsheet,
  HelpCircle,
  Loader2,
  Pause,
  Play,
  Shuffle,
} from 'lucide-react'
import { estimates } from '../data/mock'
import CorridorBar from '../ai/CorridorBar'
import { estimateFixture } from '../ai/estimateFixture'
import { generateEstimateLines } from '../ai/estimateGenerator'
import { analyzeEstimate } from '../ai/service'
import type {
  EstimateAnalysis,
  EstimateLineInput,
  EstimateLineResult,
} from '../ai/types'

type Bucket = 'inside' | 'ask' | 'none'
type Filter = Bucket | 'all'

function money(value: number): string {
  return Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

function bucketOf(item: EstimateLineResult): Bucket {
  if (!item.benchmark) return 'none'
  return item.benchmark.position === 'inside' ? 'inside' : 'ask'
}

const statusStyles: Record<Bucket, { chip: string; row: string }> = {
  inside: { chip: 'bg-emerald-50 text-emerald-700', row: '' },
  ask: { chip: 'bg-red-50 text-red-700', row: 'bg-red-50/40' },
  none: { chip: 'bg-slate-100 text-slate-600', row: 'bg-slate-50/60' },
}

function StatusChip({ item }: { item: EstimateLineResult }) {
  const bucket = bucketOf(item)
  if (bucket === 'none') {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles.none.chip}`}>
        <HelpCircle className="h-3.5 w-3.5" />
        Без оценки
      </span>
    )
  }
  const position = item.benchmark?.position
  if (position === 'inside') {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles.inside.chip}`}>
        <CheckCircle2 className="h-3.5 w-3.5" />
        В рынке
      </span>
    )
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles.ask.chip}`}>
      {position === 'above' ? (
        <ArrowUpRight className="h-3.5 w-3.5" />
      ) : (
        <ArrowDownRight className="h-3.5 w-3.5" />
      )}
      {position === 'above' ? 'Выше рынка' : 'Ниже рынка'}
    </span>
  )
}

function questionFor(item: EstimateLineResult): string {
  const bench = item.benchmark
  if (!bench) {
    return `«${item.rawName}»: работа не найдена в справочнике, ориентир не выдаётся. Попросите расшифровать состав позиции.`
  }
  if (bench.position === 'above') {
    return `«${item.rawName}»: ${money(item.unitPrice)} ₽ при верхней границе рынка ${money(bench.p90)} ₽. Спросите, что входит в цену — материалы, подготовка основания, вывоз мусора.`
  }
  return `«${item.rawName}»: ${money(item.unitPrice)} ₽ при нижней границе рынка ${money(bench.p10)} ₽. Уточните объём работ и чьи материалы — низкая цена сама по себе не означает плохое качество.`
}

interface LoadResult {
  analysis: EstimateAnalysis
  failure: string | null
}

async function loadAnalysis(lines: EstimateLineInput[]): Promise<LoadResult> {
  try {
    return { analysis: await analyzeEstimate(lines), failure: null }
  } catch (error) {
    return {
      analysis: estimateFixture,
      failure: error instanceof Error ? error.message : 'backend недоступен',
    }
  }
}

const BASE_LINES: EstimateLineInput[] = estimates[0].items.map((item) => ({
  name: item.name,
  unit: item.unit,
  qty: item.quantity,
  price: item.price,
  amount: item.total,
}))

interface BatchStats {
  checked: number
  outside: number
  abstained: number
}

interface Tally extends BatchStats {
  runs: number
}

export default function Estimates() {
  const estimate = estimates[0]
  const [batch, setBatch] = useState({ id: 0, lines: BASE_LINES, generated: false })
  const [analysis, setAnalysis] = useState<EstimateAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [failure, setFailure] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [auto, setAuto] = useState(false)
  const [history, setHistory] = useState<Record<number, BatchStats>>({})

  const { lines } = batch

  const apply = useCallback((batchId: number, next: LoadResult) => {
    setAnalysis(next.analysis)
    setFailure(next.failure)
    setLoading(false)
    if (next.failure) return
    const stats = next.analysis.items.reduce<BatchStats>(
      (acc, item) => {
        if (!item.benchmark) return { ...acc, abstained: acc.abstained + 1 }
        return {
          ...acc,
          checked: acc.checked + 1,
          outside:
            acc.outside + (item.benchmark.position === 'inside' ? 0 : 1),
        }
      },
      { checked: 0, outside: 0, abstained: 0 },
    )
    // Ключ по номеру прогона: повторное применение того же результата
    // перезаписывает запись, а не удваивает счётчик.
    setHistory((current) => ({ ...current, [batchId]: stats }))
  }, [])

  useEffect(() => {
    let cancelled = false
    loadAnalysis(batch.lines).then((next) => {
      if (!cancelled) apply(batch.id, next)
    })
    return () => {
      cancelled = true
    }
  }, [batch, apply])

  const regenerate = useCallback(() => {
    setLoading(true)
    setFilter('all')
    setBatch((current) => ({
      id: current.id + 1,
      lines: generateEstimateLines(),
      generated: true,
    }))
  }, [])

  const reset = () => {
    setLoading(true)
    setFilter('all')
    setBatch((current) => ({
      id: current.id + 1,
      lines: BASE_LINES,
      generated: false,
    }))
  }

  useEffect(() => {
    if (!auto) return
    const timer = window.setInterval(regenerate, 6000)
    return () => window.clearInterval(timer)
  }, [auto, regenerate])

  const totalSum = useMemo(
    () => lines.reduce((sum, line) => sum + line.qty * line.price, 0),
    [lines],
  )

  const tally = useMemo(
    () =>
      Object.values(history).reduce<Tally>(
        (acc, stats) => ({
          runs: acc.runs + 1,
          checked: acc.checked + stats.checked,
          outside: acc.outside + stats.outside,
          abstained: acc.abstained + stats.abstained,
        }),
        { runs: 0, checked: 0, outside: 0, abstained: 0 },
      ),
    [history],
  )

  const items = useMemo(() => analysis?.items ?? [], [analysis])
  const unitByName = useMemo(() => {
    const map = new Map<string, string>()
    for (const line of lines) map.set(line.name, line.unit)
    return map
  }, [lines])

  const counts = useMemo(() => {
    const acc: Record<Bucket, number> = { inside: 0, ask: 0, none: 0 }
    for (const item of items) acc[bucketOf(item)] += 1
    return acc
  }, [items])

  const checks = useMemo(() => analysis?.checks ?? [], [analysis])

  const questions = useMemo(
    () => items.filter((item) => bucketOf(item) !== 'inside'),
    [items],
  )

  const visible = useMemo(
    () => (filter === 'all' ? items : items.filter((i) => bucketOf(i) === filter)),
    [items, filter],
  )

  const cards: { key: Bucket; label: string; hint: string; value: number; accent: string }[] = [
    {
      key: 'inside',
      label: 'В рынке',
      hint: 'цена внутри коридора — вопросов нет',
      value: counts.inside,
      accent: 'text-emerald-600',
    },
    {
      key: 'ask',
      label: 'Стоит спросить',
      hint: 'цена вышла за коридор вверх или вниз',
      value: counts.ask,
      accent: 'text-red-600',
    },
    {
      key: 'none',
      label: 'Без оценки',
      hint: 'работа не найдена в справочнике — не угадываем',
      value: counts.none,
      accent: 'text-slate-500',
    },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Проверка сметы</h1>
          <p className="mt-1 text-sm text-slate-500">
            {batch.generated
              ? `Случайная смета №${batch.id} · ${lines.length} позиций на ${money(totalSum)} ₽`
              : `Подрядчик: ${estimate.contractor} · смета на ${money(totalSum)} ₽`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
              loading
                ? 'border-slate-300 bg-slate-100 text-slate-600'
                : analysis?.live
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                  : 'border-amber-200 bg-amber-50 text-amber-700'
            }`}
          >
            {loading
              ? 'идёт сверка…'
              : analysis?.live
                ? 'LIVE · рыночная база FRAME'
                : 'DEMO_FIXTURE'}
          </span>
          {batch.generated && (
            <button
              type="button"
              onClick={reset}
              className="rounded-lg px-2 py-2 text-sm font-medium text-slate-500 transition-colors hover:text-slate-800"
            >
              Исходная смета
            </button>
          )}
          <button
            type="button"
            onClick={() => setAuto((current) => !current)}
            className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
              auto
                ? 'border-indigo-300 bg-indigo-50 text-indigo-700'
                : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            }`}
          >
            {auto ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {auto ? 'Остановить поток' : 'Поток смет'}
          </button>
          <button
            type="button"
            onClick={regenerate}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Shuffle className="h-4 w-4" />
            )}
            Случайная смета
          </button>
        </div>
      </div>

      {tally.runs > 1 && (
        <div className="mb-6 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm">
          <span className="font-semibold text-slate-800">
            За сессию: {tally.runs} смет
          </span>
          <span className="text-slate-600">
            проверено позиций <strong className="text-slate-900">{tally.checked}</strong>
          </span>
          <span className="text-slate-600">
            вне коридора <strong className="text-red-600">{tally.outside}</strong>
            {tally.checked > 0 &&
              ` (${Math.round((tally.outside / tally.checked) * 100)}%)`}
          </span>
          <span className="text-slate-600">
            без оценки <strong className="text-slate-900">{tally.abstained}</strong>
          </span>
          <span className="text-xs text-slate-400">
            цены генерируются случайно, вердикт каждый раз считает backend
          </span>
        </div>
      )}

      {failure && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <p className="text-sm text-amber-800">
            Живой расчёт недоступен ({failure}). Ниже — сохранённый снимок прошлого
            ответа, помеченный DEMO_FIXTURE. Это не результат текущей проверки.
          </p>
        </div>
      )}

      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">Как читать проверку</h2>
        <div className="mt-4 grid gap-6 lg:grid-cols-[320px_1fr] lg:items-center">
          <div className="rounded-xl bg-slate-50 px-5 py-4">
            <CorridorBar price={850} p10={300} median={500} p90={1176} position="inside" />
          </div>
          <ul className="space-y-2 text-sm leading-relaxed text-slate-600">
            <li className="flex gap-2">
              <span className="mt-1.5 h-2 w-6 shrink-0 rounded-full bg-emerald-100" />
              <span>
                <strong className="text-slate-800">Зелёная полоса</strong> — рыночный
                коридор: в него попадает 80% реальных цен на эту работу.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="mt-1.5 h-3 w-px shrink-0 bg-emerald-600" />
              <span>
                <strong className="text-slate-800">Засечка</strong> — медиана,
                типичная цена. Отклонение от неё само по себе не проблема.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="mt-1 h-3 w-3 shrink-0 rounded-full bg-emerald-500 ring-2 ring-emerald-200" />
              <span>
                <strong className="text-slate-800">Точка</strong> — цена из сметы.
                Внутри полосы цена рыночная, даже если далека от медианы. Вышла за
                полосу — повод задать вопрос.
              </span>
            </li>
          </ul>
        </div>
        <p className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-500">
          Источник ориентира:{' '}
          <span className="font-semibold text-slate-700">
            {analysis?.source ?? '—'}
          </span>
          . Позиции без совпадения со справочником остаются без оценки: система не
          угадывает цену. Минимальная выборка для ориентира — {analysis?.minSample ?? 5}{' '}
          наблюдений.
        </p>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <button
            key={card.key}
            type="button"
            onClick={() => setFilter(filter === card.key ? 'all' : card.key)}
            className={`rounded-xl border bg-white p-4 text-left shadow-sm transition-colors ${
              filter === card.key
                ? 'border-slate-900'
                : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <p className={`text-2xl font-bold ${card.accent}`}>{card.value}</p>
            <p className="mt-0.5 text-sm font-semibold text-slate-800">{card.label}</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">{card.hint}</p>
          </button>
        ))}
      </div>

      {checks.length > 0 && (
        <div className="mb-6 rounded-2xl border-2 border-amber-300 bg-amber-50 p-6">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-700" />
            <h2 className="text-sm font-semibold text-amber-900">
              Ошибки в самой смете — {checks.length}
            </h2>
          </div>
          <p className="mt-1 text-xs text-amber-800">
            Проверено арифметикой, без модели. Здесь нет «повода спросить» —
            это несоответствия, которые подрядчик обязан объяснить.
          </p>
          <ul className="mt-3 space-y-2">
            {checks.map((check) => (
              <li
                key={`${check.kind}-${check.line ?? 'total'}`}
                className="rounded-lg border border-amber-200 bg-white px-3 py-2"
              >
                <p className="text-sm font-semibold text-slate-900">
                  {check.line !== null && (
                    <span className="mr-1.5 text-amber-700">строка {check.line}:</span>
                  )}
                  {check.title}
                </p>
                <p className="mt-0.5 text-xs text-slate-600">{check.detail}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {questions.length > 0 && (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">
            Что спросить у подрядчика
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            {questions.length} позиций из {items.length} требуют уточнения. Это
            вопросы для разговора, а не обвинения.
          </p>
          <ul className="mt-4 space-y-2.5">
            {questions.map((item) => (
              <li
                key={item.rawName}
                className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50/70 p-3 text-sm leading-relaxed text-slate-700"
              >
                <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                {questionFor(item)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="h-5 w-5 text-slate-400" />
            <h2 className="text-lg font-bold text-slate-900">Позиции сметы</h2>
          </div>
          {filter !== 'all' && (
            <button
              type="button"
              onClick={() => setFilter('all')}
              className="text-xs font-medium text-slate-500 underline-offset-2 hover:underline"
            >
              показать все {items.length}
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-left">
                <th className="px-6 py-3 font-semibold text-slate-600">Позиция</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-600">
                  Цена за ед.
                </th>
                <th className="min-w-[260px] px-4 py-3 font-semibold text-slate-600">
                  Положение в рынке
                </th>
                <th className="px-4 py-3 text-center font-semibold text-slate-600">
                  Итог
                </th>
              </tr>
            </thead>
            <tbody>
              {loading && items.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-slate-400">
                    <Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin" />
                    Сверяем позиции с рыночной базой…
                  </td>
                </tr>
              )}
              {visible.map((item) => {
                const bucket = bucketOf(item)
                const unit = unitByName.get(item.rawName) ?? ''
                return (
                  <tr
                    key={item.rawName}
                    className={`border-b border-slate-50 align-middle ${statusStyles[bucket].row}`}
                  >
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800">{item.rawName}</p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {item.normalizedWork
                          ? `распознано как «${item.normalizedWork}»`
                          : 'нет совпадения со справочником работ'}
                        {item.benchmark
                          ? ` · выборка ${item.benchmark.sampleSize}`
                          : ''}
                      </p>
                    </td>
                    <td className="whitespace-nowrap px-4 py-4 text-right">
                      <p className="font-semibold text-slate-900">
                        {money(item.unitPrice)} ₽
                      </p>
                      <p className="text-xs text-slate-400">
                        за {unit} · объём {item.quantity}
                      </p>
                    </td>
                    <td className="px-4 py-4">
                      {item.benchmark ? (
                        <CorridorBar
                          price={item.unitPrice}
                          p10={item.benchmark.p10}
                          median={item.benchmark.median}
                          p90={item.benchmark.p90}
                          position={item.benchmark.position}
                        />
                      ) : (
                        <p className="text-xs leading-relaxed text-slate-400">
                          {item.reason}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-4 text-center">
                      <StatusChip item={item} />
                    </td>
                  </tr>
                )
              })}
              {!loading && visible.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-slate-400">
                    В этой группе позиций нет
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <p className="mt-4 text-xs leading-relaxed text-slate-400">
        Проверка сопоставляет цену за единицу с коридором публичных цен и не
        оценивает добросовестность подрядчика. Модель предсказания цены в проверку
        не включена: на компаниях вне обучающей выборки она не показала преимущества
        над медианой.
      </p>
    </div>
  )
}
