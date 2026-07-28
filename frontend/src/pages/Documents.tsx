import { useState } from 'react'
import { FileText, Calculator, ClipboardCheck, Camera, Map, Upload, Download, Shield } from 'lucide-react'
import { documents, type Document } from '../data/mock'

const typeConfig: Record<Document['type'], { label: string; icon: typeof FileText; color: string; badgeColor: string }> = {
  contract: { label: 'Договоры', icon: FileText, color: 'text-blue-600 bg-blue-50', badgeColor: 'bg-blue-100 text-blue-700' },
  estimate: { label: 'Сметы', icon: Calculator, color: 'text-green-600 bg-green-50', badgeColor: 'bg-green-100 text-green-700' },
  act: { label: 'Акты приёмки', icon: ClipboardCheck, color: 'text-purple-600 bg-purple-50', badgeColor: 'bg-purple-100 text-purple-700' },
  photo: { label: 'Фотоотчёты', icon: Camera, color: 'text-amber-600 bg-amber-50', badgeColor: 'bg-amber-100 text-amber-700' },
  plan: { label: 'Планы', icon: Map, color: 'text-indigo-600 bg-indigo-50', badgeColor: 'bg-indigo-100 text-indigo-700' },
}

type FilterType = 'all' | Document['type']

const filters: { key: FilterType; label: string }[] = [
  { key: 'all', label: 'Все' },
  { key: 'contract', label: 'Договоры' },
  { key: 'estimate', label: 'Сметы' },
  { key: 'act', label: 'Акты приёмки' },
  { key: 'photo', label: 'Фотоотчёты' },
  { key: 'plan', label: 'Планы' },
]

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

function getCount(type: FilterType): number {
  if (type === 'all') return documents.length
  return documents.filter((d) => d.type === type).length
}

export default function Documents() {
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')

  const filtered = activeFilter === 'all' ? documents : documents.filter((d) => d.type === activeFilter)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Документы</h1>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 active:bg-blue-800"
          >
            <Upload className="h-4 w-4" />
            Загрузить
          </button>
        </div>

        <div className="mb-6 flex flex-wrap gap-2">
          {filters.map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => setActiveFilter(f.key)}
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                activeFilter === f.key
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {f.label}
              <span
                className={`ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-semibold ${
                  activeFilter === f.key ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500'
                }`}
              >
                {getCount(f.key)}
              </span>
            </button>
          ))}
        </div>

        <div className="overflow-hidden rounded-xl bg-white shadow-sm">
          <div className="hidden border-b border-gray-100 px-6 py-3 sm:grid sm:grid-cols-12 sm:gap-4">
            <span className="col-span-5 text-xs font-medium uppercase tracking-wider text-gray-400">Документ</span>
            <span className="col-span-2 text-xs font-medium uppercase tracking-wider text-gray-400">Этап</span>
            <span className="col-span-2 text-xs font-medium uppercase tracking-wider text-gray-400">Дата</span>
            <span className="col-span-2 text-xs font-medium uppercase tracking-wider text-gray-400">Статус</span>
            <span className="col-span-1" />
          </div>

          <div className="divide-y divide-gray-50">
            {filtered.map((doc) => {
              const cfg = typeConfig[doc.type]
              const Icon = cfg.icon

              return (
                <div
                  key={doc.id}
                  className="group grid grid-cols-1 gap-3 px-6 py-4 transition-colors hover:bg-gray-50/80 sm:grid-cols-12 sm:items-center sm:gap-4"
                >
                  <div className="col-span-5 flex items-center gap-3">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${cfg.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-gray-900">{doc.name}</p>
                      <p className="text-xs text-gray-400">{doc.author}</p>
                    </div>
                  </div>

                  <div className="col-span-2">
                    <span className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                      {doc.stage}
                    </span>
                  </div>

                  <div className="col-span-2 text-sm text-gray-500">{formatDate(doc.date)}</div>

                  <div className="col-span-2">
                    {doc.signed ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                        <Shield className="h-3 w-3" />
                        Подписан
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-400">
                        Не подписан
                      </span>
                    )}
                  </div>

                  <div className="col-span-1 flex justify-end">
                    <button
                      type="button"
                      className="rounded-lg p-2 text-gray-300 transition-colors hover:bg-gray-100 hover:text-gray-600 group-hover:text-gray-400"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {filtered.length === 0 && (
            <div className="px-6 py-16 text-center">
              <FileText className="mx-auto mb-3 h-10 w-10 text-gray-300" />
              <p className="text-sm text-gray-400">Нет документов в этой категории</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
