import { Camera, MapPin, Maximize2, DoorOpen, Calendar, TrendingUp, Sparkles, Home } from 'lucide-react'
import { rooms } from '../data/mock'

function formatNumber(n: number): string {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function HomeHub() {
  const totalArea = rooms.reduce((sum, r) => sum + r.area, 0)

  const stats = [
    { label: 'Комнат', value: rooms.length.toString(), icon: DoorOpen, color: 'text-blue-600 bg-blue-50' },
    { label: 'Площадь', value: `${totalArea} м²`, icon: Maximize2, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Ремонт завершён', value: 'Авг 2026', icon: Calendar, color: 'text-orange-600 bg-orange-50' },
    { label: 'Оценка стоимости', value: '~12 500 000 ₽', icon: TrendingUp, color: 'text-purple-600 bg-purple-50' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-2 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600">
            <Home className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Home Hub — Цифровой паспорт</h1>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                Невский пр., 42, кв. 15
              </span>
              <span className="inline-flex items-center gap-1">
                <Maximize2 className="h-3.5 w-3.5" />
                78 м²
              </span>
            </div>
          </div>
        </div>

        <div className="mb-8 mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
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

        <h2 className="mb-4 text-lg font-bold text-gray-900">Комнаты</h2>
        <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {rooms.map((room) => (
            <div key={room.id} className="rounded-xl bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-base font-bold text-gray-900">{room.name}</h3>
                <span className="text-sm text-gray-500">{room.area} м²</span>
              </div>

              <div className="mb-4 grid grid-cols-2 gap-3">
                <div className="flex h-32 flex-col items-center justify-center rounded-lg bg-gray-100">
                  <Camera className="mb-1 h-6 w-6 text-gray-300" />
                  <span className="text-xs text-gray-400">До</span>
                </div>
                <div className="flex h-32 flex-col items-center justify-center rounded-lg bg-gray-100">
                  <Camera className="mb-1 h-6 w-6 text-gray-300" />
                  <span className="text-xs text-gray-400">После</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {room.materials.map((mat) => (
                  <span
                    key={mat.name}
                    className="inline-flex rounded-full bg-gray-50 px-2.5 py-1 text-xs text-gray-600"
                  >
                    <span className="font-medium text-gray-700">{mat.name}:</span>
                    <span className="ml-1">{mat.brand}</span>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <h2 className="mb-4 text-lg font-bold text-gray-900">AI-стилист</h2>
        <div className="mb-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-white">AI-стилист</h3>
          </div>

          <p className="mb-5 max-w-xl text-sm leading-relaxed text-blue-100">
            Получите персональные рекомендации по обновлению интерьера без полного ремонта
          </p>

          <button
            type="button"
            className="mb-6 inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-medium text-blue-700 shadow-sm transition-colors hover:bg-blue-50"
          >
            <Sparkles className="h-4 w-4" />
            Получить рекомендации
          </button>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-white/10 p-4 backdrop-blur">
              <p className="mb-1 text-sm font-medium text-white">Сезонное обновление текстиля</p>
              <p className="text-xs text-blue-200">Замена штор, подушек и пледов для свежего образа гостиной</p>
            </div>
            <div className="rounded-lg bg-white/10 p-4 backdrop-blur">
              <p className="mb-1 text-sm font-medium text-white">Перестановка в гостиной</p>
              <p className="text-xs text-blue-200">Оптимизация расположения мебели для лучшей эргономики</p>
            </div>
          </div>
        </div>

        <h2 className="mb-4 text-lg font-bold text-gray-900">Стоимость жилья</h2>
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Оценочная стоимость</p>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(12500000)} &#8381;</p>
            </div>
            <div className="flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1.5">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="text-sm font-semibold text-green-700">+18%</span>
            </div>
          </div>

          <p className="mb-4 text-sm text-gray-500">Влияние ремонта на стоимость</p>

          <div className="mb-2 flex items-center gap-3">
            <span className="w-20 shrink-0 text-xs text-gray-400">До ремонта</span>
            <div className="h-4 flex-1 overflow-hidden rounded-full bg-gray-100">
              <div className="h-full rounded-full bg-gray-300" style={{ width: '84.7%' }} />
            </div>
            <span className="w-28 shrink-0 text-right text-sm font-medium text-gray-600">
              {formatNumber(10600000)} &#8381;
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-xs text-gray-400">После</span>
            <div className="h-4 flex-1 overflow-hidden rounded-full bg-gray-100">
              <div className="h-full rounded-full bg-blue-500" style={{ width: '100%' }} />
            </div>
            <span className="w-28 shrink-0 text-right text-sm font-medium text-gray-900">
              {formatNumber(12500000)} &#8381;
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
