import type { CorridorPosition } from './types'

interface CorridorBarProps {
  price: number
  p10: number
  median: number
  p90: number
  position: CorridorPosition
}

const markerColor: Record<CorridorPosition, string> = {
  inside: 'bg-emerald-500 ring-emerald-200',
  above: 'bg-red-500 ring-red-200',
  below: 'bg-amber-500 ring-amber-200',
}

const priceLabelColor: Record<CorridorPosition, string> = {
  inside: 'text-emerald-700',
  above: 'text-red-700',
  below: 'text-amber-700',
}

function money(value: number): string {
  return Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function CorridorBar({
  price,
  p10,
  median,
  p90,
  position,
}: CorridorBarProps) {
  const lo = Math.min(p10, price)
  const hi = Math.max(p90, price)
  const pad = Math.max((hi - lo) * 0.14, 1)
  const from = lo - pad
  const span = hi + pad - from

  const pct = (value: number) => ((value - from) / span) * 100
  const clamp = (value: number) => Math.min(96, Math.max(4, value))

  const bandLeft = pct(p10)
  const bandWidth = pct(p90) - bandLeft
  const priceLeft = pct(price)

  return (
    <div className="w-full min-w-[180px] select-none">
      <div
        className={`mb-1 text-[11px] font-semibold ${priceLabelColor[position]}`}
        style={{
          marginLeft: `${clamp(priceLeft)}%`,
          transform: 'translateX(-50%)',
          width: 'max-content',
        }}
      >
        {money(price)} ₽
      </div>

      <div className="relative h-2 rounded-full bg-slate-100">
        <div
          className="absolute inset-y-0 rounded-full bg-emerald-100"
          style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
        />
        <div
          className="absolute -top-0.5 h-3 w-px bg-emerald-600"
          style={{ left: `${pct(median)}%` }}
        />
        <div
          className={`absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ${markerColor[position]}`}
          style={{ left: `${priceLeft}%` }}
        />
      </div>

      <div className="mt-1 flex justify-between text-[10px] leading-tight text-slate-400">
        <span>{money(p10)}</span>
        <span className="text-slate-500">медиана {money(median)}</span>
        <span>{money(p90)}</span>
      </div>
    </div>
  )
}
