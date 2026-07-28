import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MessageSquare,
  GraduationCap,
  Trophy,
  Award,
  Pin,
  Flame,
  CheckCircle2,
  Eye,
  ThumbsUp,
  Users,
  Play,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  Star,
  Sparkles,
  Search,
  Plus,
  Lock,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import {
  forumCategories,
  forumTopics,
  educationVideos,
  challenges,
  ratingsByCategory,
  roleLabels,
  roleColors,
} from '../data/community'

type Tab = 'forum' | 'education' | 'rating' | 'challenges'

const DEMO_NOW_MS = new Date('2026-07-28T12:00:00+03:00').getTime()

const tabs: { id: Tab; label: string; icon: LucideIcon }[] = [
  { id: 'forum', label: 'Форум', icon: MessageSquare },
  { id: 'education', label: 'Обучение', icon: GraduationCap },
  { id: 'rating', label: 'Рейтинг мастеров', icon: Trophy },
  { id: 'challenges', label: 'Челленджи', icon: Award },
]

export default function Community() {
  const [activeTab, setActiveTab] = useState<Tab>('forum')

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Сообщество</h1>
        <p className="text-slate-600">Форум, обучение и рейтинг мастеров — экспертиза и удержание DIY-сегмента</p>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard icon={Users} value="1 247" label="Участников" color="text-blue-600 bg-blue-50" />
        <StatCard icon={MessageSquare} value="348" label="Тем на форуме" color="text-purple-600 bg-purple-50" />
        <StatCard icon={GraduationCap} value="142" label="Обучающих видео" color="text-emerald-600 bg-emerald-50" />
        <StatCard icon={Sparkles} value="24" label="Экспертов онлайн" color="text-amber-600 bg-amber-50" />
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-frame-600 text-frame-700'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'forum' && <ForumTab />}
      {activeTab === 'education' && <EducationTab />}
      {activeTab === 'rating' && <RatingTab />}
      {activeTab === 'challenges' && <ChallengesTab />}
    </div>
  )
}

function StatCard({ icon: Icon, value, label, color }: { icon: LucideIcon; value: string; label: string; color: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-lg font-bold text-slate-900">{value}</div>
          <div className="text-xs text-slate-500">{label}</div>
        </div>
      </div>
    </div>
  )
}

// ============ FORUM TAB ============
function ForumTab() {
  const [activeCategory, setActiveCategory] = useState('all')
  const [search, setSearch] = useState('')

  const filteredTopics = forumTopics.filter((t) => {
    const matchCat = activeCategory === 'all' || t.categoryId === activeCategory
    const matchSearch = !search || t.title.toLowerCase().includes(search.toLowerCase())
    return matchCat && matchSearch
  })

  return (
    <div className="grid lg:grid-cols-[280px_1fr] gap-6">
      {/* Categories sidebar */}
      <aside className="space-y-1">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-3 mb-2">
          Категории
        </h3>
        {forumCategories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-3 transition-colors ${
              activeCategory === cat.id
                ? 'bg-frame-50 text-frame-700'
                : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            <span className="text-lg shrink-0">{cat.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-medium truncate">{cat.name}</span>
                {cat.isProfessional && <Lock className="w-3 h-3 text-slate-400 shrink-0" />}
              </div>
            </div>
            <span className="text-xs text-slate-400 shrink-0">{cat.topicsCount}</span>
          </button>
        ))}
      </aside>

      {/* Topics list */}
      <div>
        {/* Search and create */}
        <div className="flex gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по темам..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white border border-slate-200 text-sm focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-frame-600 text-white text-sm font-medium hover:bg-frame-700 transition-colors shadow-sm">
            <Plus className="w-4 h-4" />
            Создать тему
          </button>
        </div>

        {/* Topics */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {filteredTopics.length === 0 ? (
            <div className="p-8 text-center text-slate-500">Темы не найдены</div>
          ) : (
            filteredTopics.map((topic, i) => (
              <Link
                key={topic.id}
                to={`/community/topic/${topic.id}`}
                className={`block p-5 hover:bg-slate-50 transition-colors ${
                  i > 0 ? 'border-t border-slate-100' : ''
                }`}
              >
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-frame-400 to-frame-600 flex items-center justify-center text-white text-sm font-semibold shrink-0">
                    {topic.authorAvatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      {topic.isPinned && (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700">
                          <Pin className="w-3 h-3" />
                          Закреплено
                        </span>
                      )}
                      {topic.isHot && (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-rose-700">
                          <Flame className="w-3 h-3" />
                          Горячее
                        </span>
                      )}
                      {topic.hasExpertAnswer && (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700">
                          <CheckCircle2 className="w-3 h-3" />
                          Ответ эксперта
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-slate-900 mb-1.5 hover:text-frame-700 transition-colors">
                      {topic.title}
                    </h3>
                    <p className="text-sm text-slate-600 mb-3 line-clamp-2">{topic.preview}</p>
                    <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                      <span className="flex items-center gap-1">
                        {topic.author}
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${roleColors[topic.authorRole]}`}>
                          {roleLabels[topic.authorRole]}
                        </span>
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" /> {topic.replies}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" /> {topic.views.toLocaleString('ru-RU')}
                      </span>
                      <span className="flex items-center gap-1">
                        <ThumbsUp className="w-3 h-3" /> {topic.likes}
                      </span>
                      <span>{new Date(topic.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ============ EDUCATION TAB ============
function EducationTab() {
  return (
    <div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {educationVideos.map((video) => (
          <div key={video.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer group">
            <div className={`aspect-video bg-gradient-to-br ${video.thumbnail} relative flex items-center justify-center`}>
              <div className="w-14 h-14 rounded-full bg-white/95 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg">
                <Play className="w-6 h-6 text-slate-900 ml-0.5" fill="currentColor" />
              </div>
              <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-black/70 text-white text-xs font-medium flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {video.duration} мин
              </div>
              <div className="absolute top-2 left-2 px-2 py-1 rounded bg-white/95 text-slate-700 text-xs font-medium">
                {video.category}
              </div>
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-slate-900 mb-2 line-clamp-2">{video.title}</h3>
              <p className="text-sm text-slate-600 mb-3 line-clamp-2">{video.description}</p>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-frame-100 text-frame-700 flex items-center justify-center text-[10px] font-semibold">
                    {video.author.split(' ').map((n) => n[0]).join('')}
                  </div>
                  <div>
                    <div className="font-medium text-slate-700">{video.author}</div>
                    <div className="text-[11px] text-slate-500">{video.authorRole}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Eye className="w-3 h-3" />
                  {video.views.toLocaleString('ru-RU')}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ RATING TAB ============
function RatingTab() {
  const [activeCat, setActiveCat] = useState(Object.keys(ratingsByCategory)[0])
  const entries = ratingsByCategory[activeCat] || []

  return (
    <div>
      <div className="bg-gradient-to-r from-amber-50 via-yellow-50 to-orange-50 border border-amber-100 rounded-xl p-5 mb-6 flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-amber-500 flex items-center justify-center shrink-0">
          <Trophy className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900 mb-1">Полугодовой рейтинг мастеров</h3>
          <p className="text-sm text-slate-700">
            Рейтинг формируется автоматически на основе данных платформы: сроки, бюджет, отзывы и оценки технадзора.
            Следующее обновление — <strong>1 января 2027 г.</strong>
          </p>
        </div>
      </div>

      <div className="flex gap-2 mb-5 overflow-x-auto pb-1">
        {Object.keys(ratingsByCategory).map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCat(cat)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeCat === cat
                ? 'bg-frame-600 text-white'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {entries.map((entry, i) => (
          <div key={entry.rank} className={`p-4 flex items-center gap-4 ${i > 0 ? 'border-t border-slate-100' : ''}`}>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0 ${
                entry.rank === 1 ? 'bg-amber-100 text-amber-700' :
                entry.rank === 2 ? 'bg-slate-200 text-slate-700' :
                entry.rank === 3 ? 'bg-orange-100 text-orange-700' :
                'bg-slate-50 text-slate-500'
              }`}
            >
              {entry.rank <= 3 ? ['🥇', '🥈', '🥉'][entry.rank - 1] : entry.rank}
            </div>
            <div className="w-11 h-11 rounded-full bg-gradient-to-br from-frame-400 to-frame-600 flex items-center justify-center text-white font-semibold shrink-0">
              {entry.avatar}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-slate-900">{entry.name}</span>
                {entry.isNew && (
                  <span className="px-1.5 py-0.5 rounded text-xs bg-emerald-100 text-emerald-700 font-medium">NEW</span>
                )}
              </div>
              <div className="text-sm text-slate-500">{entry.specialization}</div>
            </div>
            <div className="hidden sm:flex items-center gap-6 text-sm">
              <div className="flex items-center gap-1.5">
                <Star className="w-4 h-4 text-amber-400" fill="currentColor" />
                <span className="font-medium text-slate-900">{entry.rating}</span>
              </div>
              <div className="text-slate-600">
                <span className="font-medium text-slate-900">{entry.projects}</span> проектов
              </div>
              <div className="text-slate-600">
                <span className="font-medium text-slate-900">{entry.reviews}</span> отзывов
              </div>
            </div>
            <div className="shrink-0">
              {entry.trend === 'up' && <TrendingUp className="w-5 h-5 text-emerald-500" />}
              {entry.trend === 'down' && <TrendingDown className="w-5 h-5 text-red-500" />}
              {entry.trend === 'stable' && <Minus className="w-5 h-5 text-slate-400" />}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ CHALLENGES TAB ============
function ChallengesTab() {
  const difficultyColors = {
    easy: 'bg-emerald-100 text-emerald-700',
    medium: 'bg-amber-100 text-amber-700',
    hard: 'bg-rose-100 text-rose-700',
  }
  const difficultyLabels = {
    easy: 'Лёгкий',
    medium: 'Средний',
    hard: 'Сложный',
  }

  return (
    <div>
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 rounded-xl p-5 mb-6 flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-purple-500 flex items-center justify-center shrink-0">
          <Award className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900 mb-1">Челленджи и награды</h3>
          <p className="text-sm text-slate-700">
            Подрядчики участвуют в челленджах и получают бейджи, продвижение в рейтинге и денежные призы. Активные челленджи: <strong>4</strong>
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {challenges.map((ch) => {
          const daysLeft = Math.ceil((new Date(ch.deadline).getTime() - DEMO_NOW_MS) / (1000 * 60 * 60 * 24))
          return (
            <div key={ch.id} className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="font-semibold text-slate-900 flex-1">{ch.title}</h3>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${difficultyColors[ch.difficulty]}`}>
                  {difficultyLabels[ch.difficulty]}
                </span>
              </div>
              <p className="text-sm text-slate-600 mb-4">{ch.description}</p>

              <div className="p-3 rounded-lg bg-slate-50 mb-4">
                <div className="flex items-center gap-2 mb-1">
                  <Trophy className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">Награда</span>
                </div>
                <div className="text-lg font-bold text-slate-900 mb-1">{ch.prize}</div>
                <div className="text-xs text-slate-600">{ch.reward}</div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1.5 text-slate-600">
                  <Users className="w-4 h-4" />
                  <span>{ch.participants} участников</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-600">
                  <Clock className="w-4 h-4" />
                  <span>{daysLeft > 0 ? `${daysLeft} дней` : 'Завершён'}</span>
                </div>
              </div>

              <button className="w-full mt-4 px-4 py-2.5 rounded-lg bg-frame-600 text-white text-sm font-medium hover:bg-frame-700 transition-colors">
                Участвовать
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
