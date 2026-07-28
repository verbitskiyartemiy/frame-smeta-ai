import { useParams, Link } from 'react-router-dom'
import {
  MapPin,
  Maximize2,
  DoorOpen,
  TrendingUp,
  Wallet,
  CheckCircle2,
  Clock,
  User,
  ArrowLeft,
} from 'lucide-react'
import { type Project, type Stage } from '../data/mock'
import { getProjectById } from '../hooks/useProjects'

function formatNumber(n: number): string {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

const typeLabels: Record<Project['type'], string> = {
  cosmetic: 'Косметический',
  capital: 'Капитальный',
  designer: 'Дизайнерский',
}

const typeColors: Record<Project['type'], string> = {
  cosmetic: 'bg-green-100 text-green-700',
  capital: 'bg-blue-100 text-blue-700',
  designer: 'bg-purple-100 text-purple-700',
}

const statusBarColor: Record<Stage['status'], string> = {
  completed: 'bg-emerald-500',
  active: 'bg-blue-500',
  review: 'bg-amber-500',
  pending: 'bg-slate-200',
}

const statusDotColor: Record<Stage['status'], string> = {
  completed: 'bg-emerald-500',
  active: 'bg-blue-500 animate-pulse',
  review: 'bg-amber-500',
  pending: 'bg-slate-300',
}

const statusLabel: Record<Stage['status'], string> = {
  completed: 'Завершён',
  active: 'В работе',
  review: 'На проверке',
  pending: 'Ожидание',
}

function daysRemaining(endDate: string): number {
  const now = new Date()
  const end = new Date(endDate)
  return Math.max(0, Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)))
}

function monthsBetween(start: Date, end: Date): { label: string; offset: number; width: number }[] {
  const months: { label: string; offset: number; width: number }[] = []
  const totalDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
  const monthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

  const cursor = new Date(start.getFullYear(), start.getMonth(), 1)
  while (cursor <= end) {
    const monthStart = new Date(Math.max(cursor.getTime(), start.getTime()))
    const nextMonth = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1)
    const monthEnd = new Date(Math.min(nextMonth.getTime() - 1, end.getTime()))

    const offset = ((monthStart.getTime() - start.getTime()) / (1000 * 60 * 60 * 24) / totalDays) * 100
    const width = ((monthEnd.getTime() - monthStart.getTime()) / (1000 * 60 * 60 * 24) / totalDays) * 100

    months.push({
      label: `${monthNames[cursor.getMonth()]} ${cursor.getFullYear()}`,
      offset,
      width,
    })

    cursor.setMonth(cursor.getMonth() + 1)
  }

  return months
}

function getBarPosition(stageStart: string, stageEnd: string, projectStart: Date, totalDays: number) {
  const s = new Date(stageStart)
  const e = new Date(stageEnd)
  const left = Math.max(0, ((s.getTime() - projectStart.getTime()) / (1000 * 60 * 60 * 24) / totalDays) * 100)
  const width = Math.max(2, ((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24) / totalDays) * 100)
  return { left: `${left}%`, width: `${Math.min(width, 100 - left)}%` }
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const project = getProjectById(id || '')

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-slate-600">Проект не найден</p>
          <Link to="/" className="mt-2 text-sm text-blue-600 hover:underline">
            Вернуться на главную
          </Link>
        </div>
      </div>
    )
  }

  const budgetPercent = Math.round((project.spent / project.budget) * 100)
  const completedStages = project.stages.filter((s) => s.status === 'completed').length
  const days = daysRemaining(project.endDate)

  const projectStart = new Date(project.startDate)
  const projectEnd = new Date(project.endDate)
  const totalDays = (projectEnd.getTime() - projectStart.getTime()) / (1000 * 60 * 60 * 24)
  const months = monthsBetween(projectStart, projectEnd)

  const budgetOverrun = budgetPercent > 100

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">{project.name}</h1>
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${typeColors[project.type]}`}>
              {typeLabels[project.type]}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-4 text-sm text-slate-500">
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {project.address}
            </span>
            <span className="inline-flex items-center gap-1">
              <Maximize2 className="h-3.5 w-3.5" />
              {project.area} м&sup2;
            </span>
            <span className="inline-flex items-center gap-1">
              <DoorOpen className="h-3.5 w-3.5" />
              {project.rooms} {project.rooms === 1 ? 'комната' : project.rooms < 5 ? 'комнаты' : 'комнат'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Прогресс</p>
              <p className="text-2xl font-bold text-slate-900">{project.progress}%</p>
            </div>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-blue-500 transition-all duration-700"
              style={{ width: `${project.progress}%` }}
            />
          </div>
        </div>

        <div className="rounded-xl bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50">
              <Wallet className="h-5 w-5 text-emerald-600" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Бюджет</p>
              <p className="text-lg font-bold text-slate-900">
                {formatNumber(project.spent)}
                <span className="text-sm font-normal text-slate-400"> / {formatNumber(project.budget)} &#8381;</span>
              </p>
            </div>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all duration-700 ${budgetOverrun ? 'bg-red-500' : budgetPercent > 80 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(budgetPercent, 100)}%` }}
            />
          </div>
          <p className={`mt-1 text-right text-xs ${budgetOverrun ? 'text-red-500 font-medium' : 'text-slate-400'}`}>
            {budgetPercent}% использовано
          </p>
        </div>

        <div className="rounded-xl bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-50">
              <CheckCircle2 className="h-5 w-5 text-purple-600" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Этапы</p>
              <p className="text-2xl font-bold text-slate-900">
                {completedStages}
                <span className="text-sm font-normal text-slate-400"> / {project.stages.length}</span>
              </p>
            </div>
          </div>
          <div className="mt-3 flex gap-1">
            {project.stages.map((stage) => (
              <div
                key={stage.id}
                className={`h-2 flex-1 rounded-full ${stage.status === 'completed' ? 'bg-emerald-500' : stage.status === 'active' ? 'bg-blue-500' : 'bg-slate-200'}`}
              />
            ))}
          </div>
        </div>

        <div className="rounded-xl bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-orange-50">
              <Clock className="h-5 w-5 text-orange-600" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Срок</p>
              <p className="text-2xl font-bold text-slate-900">
                {days}
                <span className="text-sm font-normal text-slate-400"> {days === 1 ? 'день' : days < 5 ? 'дня' : 'дней'}</span>
              </p>
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-400">
            до {new Date(project.endDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        </div>
      </div>

      <div className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="mb-6 text-lg font-bold text-slate-900">Этапы работ</h2>

        <div className="overflow-x-auto">
          <div className="min-w-[700px]">
            <div className="mb-1 flex">
              <div className="w-48 shrink-0" />
              <div className="relative flex-1 h-8">
                {months.map((m, i) => (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-slate-200 px-2"
                    style={{ left: `${m.offset}%`, width: `${m.width}%` }}
                  >
                    <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider whitespace-nowrap">
                      {m.label}
                    </span>
                  </div>
                ))}
              </div>
              <div className="w-40 shrink-0" />
            </div>

            <div className="space-y-2">
              {project.stages.map((stage) => {
                const pos = getBarPosition(stage.startDate, stage.endDate, projectStart, totalDays)
                return (
                  <div key={stage.id} className="group flex items-center rounded-lg transition-colors hover:bg-slate-50">
                    <div className="w-48 shrink-0 pr-3">
                      <div className="flex items-center gap-2">
                        <div className={`h-2.5 w-2.5 shrink-0 rounded-full ${statusDotColor[stage.status]}`} />
                        <span className="text-sm font-medium text-slate-700 truncate">{stage.name}</span>
                      </div>
                    </div>

                    <div className="relative flex-1 h-10">
                      {months.map((m, i) => (
                        <div
                          key={i}
                          className="absolute top-0 h-full border-l border-slate-100"
                          style={{ left: `${m.offset}%` }}
                        />
                      ))}
                      <div
                        className={`absolute top-1.5 h-7 rounded-md ${statusBarColor[stage.status]} ${stage.status === 'active' ? 'shadow-md shadow-blue-200' : ''} flex items-center transition-all`}
                        style={{ left: pos.left, width: pos.width }}
                      >
                        {stage.status === 'active' && (
                          <div className="absolute inset-0 rounded-md bg-blue-400 animate-pulse opacity-30" />
                        )}
                        <span
                          className={`relative z-10 px-2 text-xs font-semibold truncate ${
                            stage.status === 'pending' ? 'text-slate-400' : 'text-white'
                          }`}
                        >
                          {stage.progress}%
                        </span>
                      </div>
                    </div>

                    <div className="w-40 shrink-0 pl-3">
                      <div className="flex flex-col items-end text-right">
                        <span className="text-xs text-slate-500 truncate max-w-full">
                          {stage.responsible || '—'}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {formatNumber(stage.spent)} / {formatNumber(stage.budget)} &#8381;
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="mt-4 flex items-center gap-5 border-t border-slate-100 pt-3">
              <div className="flex items-center gap-1.5">
                <div className="h-3 w-3 rounded-sm bg-emerald-500" />
                <span className="text-xs text-slate-500">{statusLabel.completed}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-3 w-3 rounded-sm bg-blue-500" />
                <span className="text-xs text-slate-500">{statusLabel.active}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-3 w-3 rounded-sm bg-amber-500" />
                <span className="text-xs text-slate-500">{statusLabel.review}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-3 w-3 rounded-sm bg-slate-200" />
                <span className="text-xs text-slate-500">{statusLabel.pending}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <h2 className="mb-5 text-lg font-bold text-slate-900">Команда</h2>
          <div className="space-y-4">
            {project.team.map((member) => (
              <div key={member.name} className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-frame-500 to-frame-700 text-sm font-semibold text-white shadow-sm">
                  {member.avatar}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">{member.name}</p>
                  <p className="text-xs text-slate-400">{member.role}</p>
                </div>
              </div>
            ))}
            {project.team.length === 0 && (
              <div className="flex flex-col items-center py-6 text-center">
                <User className="h-8 w-8 text-slate-300" />
                <p className="mt-2 text-sm text-slate-400">Команда ещё не назначена</p>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="mb-5 text-lg font-bold text-slate-900">Бюджет по этапам</h2>
          <div className="space-y-3">
            {project.stages.map((stage) => {
              const pct = stage.budget > 0 ? Math.round((stage.spent / stage.budget) * 100) : 0
              const overrun = pct > 100

              return (
                <div key={stage.id}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">{stage.name}</span>
                    <span className="text-xs text-slate-500">
                      <span className={`font-medium ${overrun ? 'text-red-500' : 'text-slate-700'}`}>
                        {formatNumber(stage.spent)}
                      </span>
                      {' / '}
                      {formatNumber(stage.budget)} &#8381;
                    </span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                    <div className="flex h-full">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${overrun ? 'bg-red-500' : 'bg-emerald-500'}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                      {!overrun && pct > 0 && (
                        <div
                          className="h-full bg-emerald-100"
                          style={{ width: `${100 - pct}%` }}
                        />
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="mt-6 flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
            <span className="text-sm font-semibold text-slate-700">Итого</span>
            <span className="text-sm">
              <span className={`font-bold ${budgetOverrun ? 'text-red-600' : 'text-slate-900'}`}>
                {formatNumber(project.spent)} &#8381;
              </span>
              <span className="text-slate-400"> / {formatNumber(project.budget)} &#8381;</span>
              <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${
                budgetOverrun
                  ? 'bg-red-100 text-red-600'
                  : budgetPercent > 80
                    ? 'bg-amber-100 text-amber-600'
                    : 'bg-emerald-100 text-emerald-600'
              }`}>
                {budgetPercent}%
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
