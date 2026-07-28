import { Link } from 'react-router-dom'
import { Plus, MapPin, Maximize2, DoorOpen, Calendar, TrendingUp, Wallet, PiggyBank, FolderKanban } from 'lucide-react'
import { type Project } from '../data/mock'
import { useProjects } from '../hooks/useProjects'

function formatNumber(n: number): string {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
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

const statusLabels: Record<Project['status'], string> = {
  planning: 'Планирование',
  active: 'В работе',
  completed: 'Завершён',
}

const statusColors: Record<Project['status'], string> = {
  planning: 'bg-yellow-100 text-yellow-700',
  active: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
}

const progressBarColors: Record<Project['status'], string> = {
  planning: 'bg-yellow-400',
  active: 'bg-blue-500',
  completed: 'bg-green-500',
}

export default function Dashboard() {
  const { projects } = useProjects()
  const activeCount = projects.filter((p) => p.status === 'active').length
  const totalBudget = projects.reduce((sum, p) => sum + p.budget, 0)
  const totalSpent = projects.reduce((sum, p) => sum + p.spent, 0)
  const avgProgress = projects.length
    ? Math.round(projects.reduce((sum, p) => sum + p.progress, 0) / projects.length)
    : 0

  const stats = [
    { label: 'Активные проекты', value: activeCount.toString(), icon: FolderKanban, color: 'text-blue-600 bg-blue-50' },
    { label: 'Общий бюджет', value: `${formatNumber(totalBudget)} ₽`, icon: Wallet, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Потрачено', value: `${formatNumber(totalSpent)} ₽`, icon: PiggyBank, color: 'text-orange-600 bg-orange-50' },
    { label: 'Средний прогресс', value: `${avgProgress}%`, icon: TrendingUp, color: 'text-purple-600 bg-purple-50' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Мои проекты</h1>
          <Link
            to="/project/new"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 active:bg-blue-800"
          >
            <Plus className="h-4 w-4" />
            Создать проект
          </Link>
        </div>

        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-xl bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${stat.color}`}>
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-lg font-semibold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {projects.map((project) => {
            const spentPercent = project.budget > 0 ? Math.round((project.spent / project.budget) * 100) : 0

            return (
              <Link
                key={project.id}
                to={`/project/${project.id}`}
                className="block rounded-xl bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">{project.name}</h2>
                    <div className="mt-1 flex items-center gap-2">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${typeColors[project.type]}`}>
                        {typeLabels[project.type]}
                      </span>
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[project.status]}`}>
                        {statusLabels[project.status]}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
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

                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-gray-500">Прогресс</span>
                  <span className="font-medium text-gray-900">{project.progress}%</span>
                </div>
                <div className="mb-4 h-2 overflow-hidden rounded-full bg-gray-100">
                  <div
                    className={`h-full rounded-full transition-all ${progressBarColors[project.status]}`}
                    style={{ width: `${project.progress}%` }}
                  />
                </div>

                <div className="mb-4 flex items-center justify-between text-sm">
                  <span className="text-gray-500">Бюджет</span>
                  <span className="text-gray-700">
                    <span className="font-medium text-gray-900">{formatNumber(project.spent)} &#8381;</span>
                    {' / '}
                    {formatNumber(project.budget)} &#8381;
                    <span className="ml-1 text-gray-400">({spentPercent}%)</span>
                  </span>
                </div>

                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Calendar className="h-3.5 w-3.5" />
                  <span>{formatDate(project.startDate)} &mdash; {formatDate(project.endDate)}</span>
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
