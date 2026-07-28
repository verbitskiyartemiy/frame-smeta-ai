import { useState, useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  PaintBucket,
  Hammer,
  Palette,
  MapPin,
  Home as HomeIcon,
  Ruler,
  Plus,
  X,
  Calendar,
  Wallet,
  Sparkles,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react'
import { useProjects } from '../hooks/useProjects'
import {
  renovationTypes,
  defaultRoomTypes,
  generateStages,
  calculateBudget,
  calculateDuration,
} from '../data/templates'
import type { Project } from '../data/mock'

type RenovationType = 'cosmetic' | 'capital' | 'designer'
type HouseType = 'new' | 'secondary' | 'historical'

interface RoomInput {
  id: string
  name: string
  area: number
}

const houseTypeLabels: Record<HouseType, string> = {
  new: 'Новостройка',
  secondary: 'Вторичка',
  historical: 'Историческое здание',
}

const typeIcons = {
  cosmetic: PaintBucket,
  capital: Hammer,
  designer: Palette,
}

function formatMoney(n: number) {
  return n.toLocaleString('ru-RU') + ' ₽'
}

export default function CreateProject() {
  const navigate = useNavigate()
  const { addProject } = useProjects()
  const [step, setStep] = useState(1)
  const totalSteps = 5

  // Step 1
  const [type, setType] = useState<RenovationType | null>(null)
  // Step 2
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [houseType, setHouseType] = useState<HouseType>('secondary')
  // Step 3
  const [totalArea, setTotalArea] = useState(60)
  const [rooms, setRooms] = useState<RoomInput[]>([
    { id: '1', name: 'Гостиная', area: 20 },
    { id: '2', name: 'Спальня', area: 15 },
    { id: '3', name: 'Кухня', area: 12 },
    { id: '4', name: 'Ванная', area: 6 },
    { id: '5', name: 'Прихожая', area: 7 },
  ])
  // Step 4
  const today = new Date().toISOString().slice(0, 10)
  const [startDate, setStartDate] = useState(today)
  const [customBudget, setCustomBudget] = useState<number | null>(null)

  const roomsArea = rooms.reduce((sum, r) => sum + (Number(r.area) || 0), 0)

  const suggestedBudget = useMemo(() => (type ? calculateBudget(type, totalArea) : 0), [type, totalArea])
  const suggestedDuration = useMemo(() => (type ? calculateDuration(type) : 0), [type])
  const finalBudget = customBudget ?? suggestedBudget

  const stages = useMemo(
    () => (type ? generateStages(type, totalArea, startDate) : []),
    [type, totalArea, startDate]
  )

  const endDate = stages.length ? stages[stages.length - 1].endDate : startDate

  function addRoom(roomName: string, area: number) {
    setRooms([...rooms, { id: String(Date.now()), name: roomName, area }])
  }

  function removeRoom(id: string) {
    setRooms(rooms.filter((r) => r.id !== id))
  }

  function updateRoomArea(id: string, area: number) {
    setRooms(rooms.map((r) => (r.id === id ? { ...r, area } : r)))
  }

  function canProceed(): boolean {
    if (step === 1) return type !== null
    if (step === 2) return name.trim().length >= 3 && address.trim().length >= 3
    if (step === 3) return totalArea > 0 && rooms.length > 0
    if (step === 4) return finalBudget > 0 && startDate.length > 0
    return true
  }

  function handleFinish() {
    if (!type) return
    const id = 'p' + Date.now()
    const project: Project = {
      id,
      name,
      type,
      address,
      area: totalArea,
      rooms: rooms.length,
      status: 'planning',
      progress: 0,
      budget: finalBudget,
      spent: 0,
      startDate,
      endDate,
      stages,
      team: [],
    }
    addProject(project)
    navigate(`/project/${id}`)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 mb-6">
        <ArrowLeft className="w-4 h-4" />
        К проектам
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Создание проекта ремонта</h1>
        <p className="text-slate-600">AI поможет рассчитать бюджет и автоматически сгенерирует этапы работ</p>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className="flex items-center flex-1 last:flex-initial">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  s < step
                    ? 'bg-frame-600 text-white'
                    : s === step
                    ? 'bg-frame-600 text-white ring-4 ring-frame-100'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {s < step ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 5 && (
                <div className={`h-0.5 flex-1 mx-2 ${s < step ? 'bg-frame-600' : 'bg-slate-200'}`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-slate-500 px-1">
          <span>Тип</span>
          <span>Информация</span>
          <span>Помещения</span>
          <span>Бюджет и сроки</span>
          <span>Готово</span>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-6">
        {step === 1 && <Step1 type={type} setType={setType} />}
        {step === 2 && (
          <Step2
            name={name}
            setName={setName}
            address={address}
            setAddress={setAddress}
            houseType={houseType}
            setHouseType={setHouseType}
          />
        )}
        {step === 3 && (
          <Step3
            totalArea={totalArea}
            setTotalArea={setTotalArea}
            rooms={rooms}
            roomsArea={roomsArea}
            addRoom={addRoom}
            removeRoom={removeRoom}
            updateRoomArea={updateRoomArea}
          />
        )}
        {step === 4 && type && (
          <Step4
            type={type}
            suggestedBudget={suggestedBudget}
            suggestedDuration={suggestedDuration}
            customBudget={customBudget}
            setCustomBudget={setCustomBudget}
            startDate={startDate}
            setStartDate={setStartDate}
            endDate={endDate}
            stagesCount={stages.length}
          />
        )}
        {step === 5 && type && (
          <Step5
            type={type}
            name={name}
            address={address}
            totalArea={totalArea}
            rooms={rooms.length}
            budget={finalBudget}
            startDate={startDate}
            endDate={endDate}
            stages={stages}
          />
        )}
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={() => setStep(Math.max(1, step - 1))}
          disabled={step === 1}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Назад
        </button>

        {step < totalSteps ? (
          <button
            onClick={() => setStep(Math.min(totalSteps, step + 1))}
            disabled={!canProceed()}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-frame-600 text-white hover:bg-frame-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm"
          >
            Далее
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleFinish}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition shadow-sm"
          >
            <Check className="w-4 h-4" />
            Создать проект
          </button>
        )}
      </div>
    </div>
  )
}

// ============ STEP 1 ============
function Step1({ type, setType }: { type: RenovationType | null; setType: (t: RenovationType) => void }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-900 mb-2">Какой тип ремонта планируете?</h2>
      <p className="text-slate-600 mb-6">
        От типа зависит набор этапов, оценка бюджета и сроков. Можно изменить позже.
      </p>
      <div className="grid gap-4">
        {(Object.keys(renovationTypes) as RenovationType[]).map((key) => {
          const t = renovationTypes[key]
          const Icon = typeIcons[key]
          const selected = type === key
          return (
            <button
              key={key}
              onClick={() => setType(key)}
              className={`text-left p-5 rounded-xl border-2 transition flex items-start gap-4 ${
                selected
                  ? 'border-frame-600 bg-frame-50 shadow-sm'
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
            >
              <div
                className={`w-12 h-12 rounded-lg flex items-center justify-center shrink-0 ${
                  selected ? 'bg-frame-600 text-white' : 'bg-slate-100 text-slate-600'
                }`}
              >
                <Icon className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold text-slate-900">{t.label}</h3>
                  {selected && (
                    <div className="w-5 h-5 rounded-full bg-frame-600 flex items-center justify-center">
                      <Check className="w-3 h-3 text-white" />
                    </div>
                  )}
                </div>
                <p className="text-sm text-slate-600 mb-3">{t.description}</p>
                <div className="flex gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> {t.duration}
                  </span>
                  <span className="flex items-center gap-1">
                    <Wallet className="w-3.5 h-3.5" /> {t.budget}
                  </span>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ============ STEP 2 ============
function Step2({
  name,
  setName,
  address,
  setAddress,
  houseType,
  setHouseType,
}: {
  name: string
  setName: (v: string) => void
  address: string
  setAddress: (v: string) => void
  houseType: HouseType
  setHouseType: (v: HouseType) => void
}) {
  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-900 mb-2">Основная информация</h2>
      <p className="text-slate-600 mb-6">Это поможет команде ориентироваться в проекте</p>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Название проекта</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Например: Ремонт двушки на Невском"
            className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
            <MapPin className="w-4 h-4" />
            Адрес объекта
          </label>
          <input
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="ул. Рубинштейна, 8, кв. 12"
            className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none transition"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
            <HomeIcon className="w-4 h-4" />
            Тип дома
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(Object.keys(houseTypeLabels) as HouseType[]).map((key) => (
              <button
                key={key}
                onClick={() => setHouseType(key)}
                className={`px-4 py-3 rounded-lg border-2 text-sm font-medium transition ${
                  houseType === key
                    ? 'border-frame-600 bg-frame-50 text-frame-700'
                    : 'border-slate-200 text-slate-700 hover:border-slate-300'
                }`}
              >
                {houseTypeLabels[key]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-50 border border-blue-100">
          <Sparkles className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <strong>AI-подсказка:</strong> Для исторических зданий мы добавим в смету пункт согласования с
            КГИОП и используем щадящие технологии демонтажа.
          </div>
        </div>
      </div>
    </div>
  )
}

// ============ STEP 3 ============
function Step3({
  totalArea,
  setTotalArea,
  rooms,
  roomsArea,
  addRoom,
  removeRoom,
  updateRoomArea,
}: {
  totalArea: number
  setTotalArea: (v: number) => void
  rooms: RoomInput[]
  roomsArea: number
  addRoom: (name: string, area: number) => void
  removeRoom: (id: string) => void
  updateRoomArea: (id: string, area: number) => void
}) {
  const [showAddMenu, setShowAddMenu] = useState(false)
  const existingNames = new Set(rooms.map((r) => r.name))
  const available = defaultRoomTypes.filter((r) => !existingNames.has(r.name))

  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-900 mb-2">Помещения и зоны</h2>
      <p className="text-slate-600 mb-6">Укажите площадь и состав помещений</p>

      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
          <Ruler className="w-4 h-4" />
          Общая площадь квартиры, м²
        </label>
        <input
          type="number"
          value={totalArea}
          onChange={(e) => setTotalArea(Number(e.target.value))}
          className="w-32 px-4 py-3 rounded-lg border border-slate-200 focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none"
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-700">Помещения ({rooms.length})</h3>
          <span className="text-xs text-slate-500">
            Сумма: {roomsArea} м² из {totalArea} м²
          </span>
        </div>

        <div className="space-y-2 mb-4">
          {rooms.map((r) => (
            <div
              key={r.id}
              className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50"
            >
              <div className="w-9 h-9 rounded-lg bg-frame-100 text-frame-700 flex items-center justify-center text-sm font-semibold">
                {r.name.charAt(0)}
              </div>
              <span className="flex-1 font-medium text-slate-900">{r.name}</span>
              <input
                type="number"
                value={r.area}
                onChange={(e) => updateRoomArea(r.id, Number(e.target.value))}
                className="w-20 px-3 py-1.5 rounded-md border border-slate-200 text-sm text-right"
              />
              <span className="text-sm text-slate-500 w-6">м²</span>
              <button
                onClick={() => removeRoom(r.id)}
                className="w-8 h-8 rounded-md hover:bg-red-50 hover:text-red-600 text-slate-400 flex items-center justify-center transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        <div className="relative">
          <button
            onClick={() => setShowAddMenu(!showAddMenu)}
            disabled={available.length === 0}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border-2 border-dashed border-slate-200 text-slate-600 hover:border-frame-300 hover:text-frame-600 transition disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Добавить помещение
          </button>
          {showAddMenu && available.length > 0 && (
            <div className="absolute z-10 left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-slate-200 p-2 grid grid-cols-2 gap-1">
              {available.map((r) => (
                <button
                  key={r.name}
                  onClick={() => {
                    addRoom(r.name, r.defaultArea)
                    setShowAddMenu(false)
                  }}
                  className="text-left px-3 py-2 rounded hover:bg-slate-50 text-sm text-slate-700"
                >
                  {r.name} <span className="text-xs text-slate-400">{r.defaultArea} м²</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {Math.abs(roomsArea - totalArea) > 5 && (
        <div className="mt-4 flex items-start gap-3 p-4 rounded-lg bg-amber-50 border border-amber-100">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-900">
            Сумма площадей помещений ({roomsArea} м²) сильно отличается от общей площади ({totalArea} м²).
            Проверьте значения — это влияет на расчёт сметы.
          </div>
        </div>
      )}
    </div>
  )
}

// ============ STEP 4 ============
function Step4({
  type,
  suggestedBudget,
  suggestedDuration,
  customBudget,
  setCustomBudget,
  startDate,
  setStartDate,
  endDate,
  stagesCount,
}: {
  type: RenovationType
  suggestedBudget: number
  suggestedDuration: number
  customBudget: number | null
  setCustomBudget: (v: number | null) => void
  startDate: string
  setStartDate: (v: string) => void
  endDate: string
  stagesCount: number
}) {
  const finalBudget = customBudget ?? suggestedBudget
  return (
    <div>
      <h2 className="text-2xl font-semibold text-slate-900 mb-2">Бюджет и сроки</h2>
      <p className="text-slate-600 mb-6">AI рассчитал параметры на основе вашего типа ремонта и метража</p>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="p-5 rounded-xl bg-gradient-to-br from-frame-50 to-blue-50 border border-frame-100">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-frame-600" />
            <span className="text-xs font-semibold text-frame-700 uppercase tracking-wide">
              AI-оценка бюджета
            </span>
          </div>
          <div className="text-3xl font-bold text-slate-900 mb-1">{formatMoney(suggestedBudget)}</div>
          <div className="text-sm text-slate-600">
            На основе {renovationTypes[type].label.toLowerCase()} ремонта
          </div>
        </div>

        <div className="p-5 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">
              Прогноз сроков
            </span>
          </div>
          <div className="text-3xl font-bold text-slate-900 mb-1">{suggestedDuration} дней</div>
          <div className="text-sm text-slate-600">
            {stagesCount} этапов работ с учётом параллелизма
          </div>
        </div>
      </div>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
            <Calendar className="w-4 h-4" />
            Желаемая дата начала
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-4 py-3 rounded-lg border border-slate-200 focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none"
          />
          <p className="text-xs text-slate-500 mt-2">
            Предполагаемое окончание:{' '}
            <strong className="text-slate-700">
              {new Date(endDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}
            </strong>
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
            <Wallet className="w-4 h-4" />
            Ваш бюджет (можно скорректировать)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="number"
              value={finalBudget}
              onChange={(e) => setCustomBudget(Number(e.target.value))}
              className="flex-1 px-4 py-3 rounded-lg border border-slate-200 focus:border-frame-500 focus:ring-2 focus:ring-frame-100 outline-none"
            />
            {customBudget !== null && (
              <button
                onClick={() => setCustomBudget(null)}
                className="text-sm text-frame-600 hover:underline whitespace-nowrap"
              >
                Сбросить
              </button>
            )}
          </div>
          {customBudget !== null && customBudget < suggestedBudget * 0.8 && (
            <div className="mt-3 flex items-start gap-2 text-sm text-amber-700">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                Бюджет ниже AI-оценки на{' '}
                {Math.round(((suggestedBudget - customBudget) / suggestedBudget) * 100)}%. Возможно
                придётся выбирать более бюджетные материалы.
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ============ STEP 5 ============
function Step5({
  type,
  name,
  address,
  totalArea,
  rooms,
  budget,
  startDate,
  endDate,
  stages,
}: {
  type: RenovationType
  name: string
  address: string
  totalArea: number
  rooms: number
  budget: number
  startDate: string
  endDate: string
  stages: { id: string; name: string; budget: number; startDate: string; endDate: string }[]
}) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
          <CheckCircle2 className="w-7 h-7 text-emerald-600" />
        </div>
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Всё готово!</h2>
          <p className="text-slate-600">Проверьте параметры — после создания AI сразу сгенерирует этапы</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Проект</div>
          <div className="font-semibold text-slate-900 mb-2">{name}</div>
          <div className="text-sm text-slate-600">{address}</div>
        </div>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Тип ремонта</div>
          <div className="font-semibold text-slate-900 mb-2">{renovationTypes[type].label}</div>
          <div className="text-sm text-slate-600">
            {totalArea} м² · {rooms} {rooms === 1 ? 'помещение' : 'помещений'}
          </div>
        </div>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Бюджет</div>
          <div className="font-semibold text-slate-900">{formatMoney(budget)}</div>
        </div>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Срок</div>
          <div className="font-semibold text-slate-900">
            {new Date(startDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })} —{' '}
            {new Date(endDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })}
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-frame-600" />
          <h3 className="font-semibold text-slate-900">AI сгенерировал {stages.length} этапов работ</h3>
        </div>
        <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
          {stages.map((s, i) => (
            <div
              key={s.id}
              className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-white"
            >
              <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-semibold shrink-0">
                {i + 1}
              </div>
              <span className="flex-1 text-sm text-slate-900">{s.name}</span>
              <span className="text-xs text-slate-500 hidden sm:block">
                {new Date(s.startDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })} —{' '}
                {new Date(s.endDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
              </span>
              <span className="text-sm font-medium text-slate-700">{formatMoney(s.budget)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
