import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Eye,
  ThumbsUp,
  MessageSquare,
  Pin,
  Flame,
  CheckCircle2,
  Share2,
  Bookmark,
  Send,
  Paperclip,
} from 'lucide-react'
import { getTopicById, getCategoryById, roleLabels, roleColors } from '../data/community'

export default function ForumTopic() {
  const { id } = useParams<{ id: string }>()
  const topic = id ? getTopicById(id) : undefined

  if (!topic) {
    return (
      <div className="max-w-4xl mx-auto text-center py-20">
        <h2 className="text-2xl font-semibold text-slate-900 mb-2">Тема не найдена</h2>
        <Link to="/community" className="text-frame-600 hover:underline">
          Вернуться к форуму
        </Link>
      </div>
    )
  }

  const category = getCategoryById(topic.categoryId)

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/community" className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 mb-4">
        <ArrowLeft className="w-4 h-4" />
        Все темы
      </Link>

      {/* Topic header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-4">
        <div className="flex items-center gap-2 flex-wrap mb-3">
          {category && (
            <span className={`px-2 py-1 rounded text-xs font-medium ${category.color}`}>
              {category.icon} {category.name}
            </span>
          )}
          {topic.isPinned && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-700">
              <Pin className="w-3 h-3" />
              Закреплено
            </span>
          )}
          {topic.isHot && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-rose-100 text-rose-700">
              <Flame className="w-3 h-3" />
              Горячее
            </span>
          )}
          {topic.hasExpertAnswer && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-emerald-100 text-emerald-700">
              <CheckCircle2 className="w-3 h-3" />
              Ответ эксперта
            </span>
          )}
        </div>

        <h1 className="text-2xl font-bold text-slate-900 mb-4">{topic.title}</h1>

        <div className="flex items-start gap-4 pb-4 border-b border-slate-100">
          <div className="w-11 h-11 rounded-full bg-gradient-to-br from-frame-400 to-frame-600 flex items-center justify-center text-white font-semibold shrink-0">
            {topic.authorAvatar}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-0.5 flex-wrap">
              <span className="font-medium text-slate-900">{topic.author}</span>
              <span className={`px-1.5 py-0.5 rounded text-xs ${roleColors[topic.authorRole]}`}>
                {roleLabels[topic.authorRole]}
              </span>
            </div>
            <div className="text-xs text-slate-500">
              {new Date(topic.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition">
              <Bookmark className="w-4 h-4" />
            </button>
            <button className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition">
              <Share2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-slate-700 leading-relaxed mt-4 whitespace-pre-wrap">{topic.content}</p>

        <div className="flex items-center gap-6 mt-5 pt-4 border-t border-slate-100 text-sm text-slate-500">
          <button className="flex items-center gap-1.5 hover:text-frame-600 transition">
            <ThumbsUp className="w-4 h-4" />
            <span>{topic.likes}</span>
          </button>
          <span className="flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4" />
            {topic.replies} ответов
          </span>
          <span className="flex items-center gap-1.5">
            <Eye className="w-4 h-4" />
            {topic.views.toLocaleString('ru-RU')} просмотров
          </span>
        </div>
      </div>

      {/* Comments */}
      {topic.comments.length > 0 && (
        <div className="space-y-3 mb-6">
          <h2 className="text-sm font-semibold text-slate-700 px-1">Ответы ({topic.comments.length})</h2>
          {topic.comments.map((c) => (
            <div
              key={c.id}
              className={`bg-white rounded-xl border p-5 ${
                c.isBestAnswer ? 'border-emerald-200 ring-1 ring-emerald-100' : 'border-slate-200'
              }`}
            >
              {c.isBestAnswer && (
                <div className="flex items-center gap-2 mb-3 pb-3 border-b border-emerald-100">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-medium text-emerald-700">Лучший ответ</span>
                </div>
              )}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-frame-400 to-frame-600 flex items-center justify-center text-white text-sm font-semibold shrink-0">
                  {c.authorAvatar}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="font-medium text-slate-900">{c.author}</span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${roleColors[c.authorRole]}`}>
                      {roleLabels[c.authorRole]}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(c.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                    </span>
                  </div>
                  <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">{c.text}</p>
                  <div className="flex items-center gap-4 mt-3 text-sm text-slate-500">
                    <button className="flex items-center gap-1.5 hover:text-frame-600 transition">
                      <ThumbsUp className="w-4 h-4" />
                      <span>{c.likes}</span>
                    </button>
                    <button className="hover:text-frame-600 transition">Ответить</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reply box */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Ваш ответ</h3>
        <textarea
          placeholder="Поделитесь опытом или задайте уточняющий вопрос..."
          rows={4}
          className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none resize-none"
        />
        <div className="flex items-center justify-between mt-3">
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-600 hover:bg-slate-100 transition">
            <Paperclip className="w-4 h-4" />
            Прикрепить файл
          </button>
          <button className="flex items-center gap-2 px-5 py-2 rounded-lg bg-frame-600 text-white text-sm font-medium hover:bg-frame-700 transition shadow-sm">
            <Send className="w-4 h-4" />
            Отправить
          </button>
        </div>
      </div>
    </div>
  )
}
