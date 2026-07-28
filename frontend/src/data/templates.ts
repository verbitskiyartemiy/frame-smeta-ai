import type { Stage } from './mock'

export interface StageTemplate {
  name: string
  durationDays: number
  budgetPerSqm: number
  responsible: string
}

export const stageTemplates: Record<'cosmetic' | 'capital' | 'designer', StageTemplate[]> = {
  cosmetic: [
    { name: 'Подготовка поверхностей', durationDays: 5, budgetPerSqm: 800, responsible: 'Отделочник' },
    { name: 'Покраска и обои', durationDays: 10, budgetPerSqm: 1500, responsible: 'Отделочник' },
    { name: 'Замена напольных покрытий', durationDays: 7, budgetPerSqm: 1200, responsible: 'Отделочник' },
    { name: 'Финальная уборка', durationDays: 2, budgetPerSqm: 200, responsible: 'Клининг' },
  ],
  capital: [
    { name: 'Демонтаж', durationDays: 14, budgetPerSqm: 2300, responsible: 'Прораб' },
    { name: 'Электромонтаж', durationDays: 20, budgetPerSqm: 4100, responsible: 'Электрик' },
    { name: 'Сантехника', durationDays: 18, budgetPerSqm: 3600, responsible: 'Сантехник' },
    { name: 'Штукатурка и выравнивание', durationDays: 28, budgetPerSqm: 5800, responsible: 'Отделочник' },
    { name: 'Укладка плитки', durationDays: 21, budgetPerSqm: 4500, responsible: 'Плиточник' },
    { name: 'Чистовая отделка', durationDays: 35, budgetPerSqm: 6700, responsible: 'Отделочник' },
    { name: 'Напольные покрытия', durationDays: 14, budgetPerSqm: 4900, responsible: 'Отделочник' },
    { name: 'Установка дверей и мебели', durationDays: 21, budgetPerSqm: 4700, responsible: 'Столяр' },
  ],
  designer: [
    { name: 'Дизайн-проект и согласование', durationDays: 30, budgetPerSqm: 2500, responsible: 'Дизайнер' },
    { name: 'Демонтаж', durationDays: 14, budgetPerSqm: 2300, responsible: 'Прораб' },
    { name: 'Электромонтаж', durationDays: 22, budgetPerSqm: 4500, responsible: 'Электрик' },
    { name: 'Сантехника', durationDays: 20, budgetPerSqm: 4000, responsible: 'Сантехник' },
    { name: 'Штукатурка и выравнивание', durationDays: 30, budgetPerSqm: 6500, responsible: 'Отделочник' },
    { name: 'Декоративные стены', durationDays: 18, budgetPerSqm: 5800, responsible: 'Декоратор' },
    { name: 'Укладка плитки и камня', durationDays: 25, budgetPerSqm: 7200, responsible: 'Плиточник' },
    { name: 'Чистовая отделка', durationDays: 40, budgetPerSqm: 9500, responsible: 'Отделочник' },
    { name: 'Напольные покрытия премиум', durationDays: 16, budgetPerSqm: 7400, responsible: 'Отделочник' },
    { name: 'Установка дверей и мебели на заказ', durationDays: 28, budgetPerSqm: 8100, responsible: 'Столяр' },
    { name: 'Декор и финальная стилизация', durationDays: 14, budgetPerSqm: 3500, responsible: 'Декоратор' },
  ],
}

export const renovationTypes = {
  cosmetic: {
    label: 'Косметический',
    description: 'Покраска, обои, замена пола без больших работ',
    duration: '1–2 месяца',
    budget: '4 000–8 000 ₽/м²',
    icon: 'PaintBucket',
  },
  capital: {
    label: 'Капитальный',
    description: 'Полная замена коммуникаций, отделки и перепланировка',
    duration: '4–6 месяцев',
    budget: '25 000–45 000 ₽/м²',
    icon: 'Hammer',
  },
  designer: {
    label: 'Дизайнерский',
    description: 'С дизайн-проектом, премиальные материалы, авторский надзор',
    duration: '6–9 месяцев',
    budget: '60 000–120 000 ₽/м²',
    icon: 'Palette',
  },
}

export const defaultRoomTypes = [
  { name: 'Гостиная', defaultArea: 20 },
  { name: 'Спальня', defaultArea: 15 },
  { name: 'Кухня', defaultArea: 12 },
  { name: 'Ванная', defaultArea: 6 },
  { name: 'Туалет', defaultArea: 3 },
  { name: 'Прихожая', defaultArea: 8 },
  { name: 'Балкон', defaultArea: 4 },
  { name: 'Кабинет', defaultArea: 10 },
  { name: 'Детская', defaultArea: 14 },
  { name: 'Гардеробная', defaultArea: 5 },
]

export function generateStages(
  type: 'cosmetic' | 'capital' | 'designer',
  area: number,
  startDate: string
): Stage[] {
  const templates = stageTemplates[type]
  const start = new Date(startDate)
  let currentDate = new Date(start)

  return templates.map((template, i) => {
    const stageStart = new Date(currentDate)
    const stageEnd = new Date(currentDate)
    stageEnd.setDate(stageEnd.getDate() + template.durationDays)
    // Some stages overlap — shift start back a bit for parallelism
    currentDate = new Date(stageEnd)
    currentDate.setDate(currentDate.getDate() - Math.floor(template.durationDays * 0.3))

    return {
      id: `s${i + 1}`,
      name: template.name,
      status: 'pending' as const,
      startDate: stageStart.toISOString().slice(0, 10),
      endDate: stageEnd.toISOString().slice(0, 10),
      responsible: template.responsible,
      progress: 0,
      budget: Math.round(template.budgetPerSqm * area),
      spent: 0,
    }
  })
}

export function calculateBudget(type: 'cosmetic' | 'capital' | 'designer', area: number): number {
  return stageTemplates[type].reduce((sum, t) => sum + t.budgetPerSqm * area, 0)
}

export function calculateDuration(type: 'cosmetic' | 'capital' | 'designer'): number {
  const templates = stageTemplates[type]
  // Approximate total duration with overlapping
  return templates.reduce((sum, t) => sum + Math.floor(t.durationDays * 0.7), 0)
}
