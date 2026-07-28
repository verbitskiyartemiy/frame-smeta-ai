import type { EstimateLineInput } from './types'

interface WorkTemplate {
  name: string
  unit: string
  basePrice: number
  qtyFrom: number
  qtyTo: number
}

// Прайс подрядчика: округлённые ставки и типовые объёмы работ по двушке.
// Рыночных ориентиров здесь нет — коридор считает backend по своей базе,
// генератор его не видит и подогнать под ответ не может.
const WORKS: WorkTemplate[] = [
  { name: 'Демонтаж старых покрытий', unit: 'м²', basePrice: 200, qtyFrom: 40, qtyTo: 120 },
  { name: 'Демонтаж напольного покрытия', unit: 'м²', basePrice: 150, qtyFrom: 30, qtyTo: 90 },
  { name: 'Демонтаж перегородок', unit: 'м²', basePrice: 350, qtyFrom: 6, qtyTo: 25 },
  { name: 'Демонтаж обоев', unit: 'м²', basePrice: 120, qtyFrom: 50, qtyTo: 180 },
  { name: 'Демонтаж плитки', unit: 'м²', basePrice: 150, qtyFrom: 15, qtyTo: 60 },
  { name: 'Демонтаж потолка', unit: 'м²', basePrice: 150, qtyFrom: 20, qtyTo: 70 },
  { name: 'Поклейка обоев', unit: 'м²', basePrice: 300, qtyFrom: 60, qtyTo: 200 },
  { name: 'Укладка плинтуса', unit: 'м.п.', basePrice: 180, qtyFrom: 30, qtyTo: 90 },
  { name: 'Укладка плитки (пол)', unit: 'м²', basePrice: 1200, qtyFrom: 10, qtyTo: 40 },
  { name: 'Укладка плитки (стены)', unit: 'м²', basePrice: 2800, qtyFrom: 15, qtyTo: 50 },
  { name: 'Грунтовка стен', unit: 'м²', basePrice: 90, qtyFrom: 80, qtyTo: 240 },
  { name: 'Штукатурка стен', unit: 'м²', basePrice: 500, qtyFrom: 80, qtyTo: 240 },
  { name: 'Штукатурка потолка', unit: 'м²', basePrice: 550, qtyFrom: 20, qtyTo: 70 },
  { name: 'Шпаклёвка стен', unit: 'м²', basePrice: 300, qtyFrom: 80, qtyTo: 240 },
  { name: 'Покраска стен', unit: 'м²', basePrice: 250, qtyFrom: 60, qtyTo: 200 },
  { name: 'Покраска потолка', unit: 'м²', basePrice: 280, qtyFrom: 20, qtyTo: 70 },
  { name: 'Монтаж светильников', unit: 'шт', basePrice: 500, qtyFrom: 4, qtyTo: 20 },
  { name: 'Прокладка кабеля', unit: 'м.п.', basePrice: 120, qtyFrom: 60, qtyTo: 250 },
  { name: 'Штробление стен', unit: 'м.п.', basePrice: 280, qtyFrom: 20, qtyTo: 90 },
  { name: 'Перегородка из ГКЛ', unit: 'м²', basePrice: 700, qtyFrom: 6, qtyTo: 30 },
  { name: 'Потолок из ГКЛ', unit: 'м²', basePrice: 1000, qtyFrom: 10, qtyTo: 45 },
  { name: 'Короб из ГКЛ', unit: 'м.п.', basePrice: 800, qtyFrom: 4, qtyTo: 18 },
  { name: 'Отделка откосов', unit: 'м.п.', basePrice: 450, qtyFrom: 8, qtyTo: 30 },
  { name: 'Укладка линолеума', unit: 'м²', basePrice: 250, qtyFrom: 15, qtyTo: 60 },
  { name: 'Укладка ламината', unit: 'м²', basePrice: 380, qtyFrom: 20, qtyTo: 80 },
  { name: 'Укладка ковролина', unit: 'м²', basePrice: 200, qtyFrom: 10, qtyTo: 40 },
  { name: 'Стяжка пола', unit: 'м²', basePrice: 600, qtyFrom: 30, qtyTo: 90 },
  { name: 'Наливной пол', unit: 'м²', basePrice: 250, qtyFrom: 20, qtyTo: 70 },
  { name: 'Тёплый пол', unit: 'м²', basePrice: 700, qtyFrom: 5, qtyTo: 25 },
  { name: 'Натяжной потолок', unit: 'м²', basePrice: 850, qtyFrom: 20, qtyTo: 80 },
  { name: 'Реечный потолок', unit: 'м²', basePrice: 530, qtyFrom: 5, qtyTo: 20 },
  { name: 'Декоративная штукатурка', unit: 'м²', basePrice: 800, qtyFrom: 10, qtyTo: 45 },
  { name: 'Облицовка камнем', unit: 'м²', basePrice: 1300, qtyFrom: 5, qtyTo: 25 },
  { name: 'Разводка сантехники', unit: 'точка', basePrice: 3000, qtyFrom: 4, qtyTo: 16 },
  { name: 'Установка ванны', unit: 'шт', basePrice: 4000, qtyFrom: 1, qtyTo: 2 },
  { name: 'Установка раковины', unit: 'шт', basePrice: 2000, qtyFrom: 1, qtyTo: 3 },
  { name: 'Установка унитаза', unit: 'шт', basePrice: 2500, qtyFrom: 1, qtyTo: 2 },
  { name: 'Установка смесителя', unit: 'шт', basePrice: 1500, qtyFrom: 1, qtyTo: 4 },
  { name: 'Установка душевой кабины', unit: 'шт', basePrice: 5000, qtyFrom: 1, qtyTo: 2 },
  { name: 'Установка водонагревателя', unit: 'шт', basePrice: 3000, qtyFrom: 1, qtyTo: 2 },
  { name: 'Установка полотенцесушителя', unit: 'шт', basePrice: 3200, qtyFrom: 1, qtyTo: 2 },
  { name: 'Монтаж электрощита', unit: 'шт', basePrice: 3800, qtyFrom: 1, qtyTo: 2 },
  { name: 'Установка межкомнатной двери', unit: 'шт', basePrice: 5000, qtyFrom: 2, qtyTo: 8 },
]

// Формулировки, которые подрядчики пишут в реальных сметах и по которым
// невозможно понять состав работ. Сопоставятся они или нет — решает backend.
const VAGUE: WorkTemplate[] = [
  { name: 'Электромонтаж (точка)', unit: 'шт', basePrice: 900, qtyFrom: 20, qtyTo: 80 },
  { name: 'Установка дверей', unit: 'шт', basePrice: 5500, qtyFrom: 2, qtyTo: 8 },
  { name: 'Материалы (ориентировочно)', unit: 'компл.', basePrice: 400000, qtyFrom: 1, qtyTo: 1 },
  { name: 'Монтаж системы умного дома', unit: 'компл.', basePrice: 85000, qtyFrom: 1, qtyTo: 1 },
  { name: 'Прочие работы по объекту', unit: 'компл.', basePrice: 60000, qtyFrom: 1, qtyTo: 1 },
  { name: 'Вывоз строительного мусора', unit: 'м³', basePrice: 1800, qtyFrom: 3, qtyTo: 14 },
]

function randomInt(from: number, to: number): number {
  return from + Math.floor(Math.random() * (to - from + 1))
}

function roundPrice(value: number): number {
  if (value >= 10000) return Math.round(value / 500) * 500
  if (value >= 1000) return Math.round(value / 50) * 50
  return Math.round(value / 10) * 10
}

// Разброс ставок между подрядчиками: логарифмически равномерно от 0.5x до 2x
// к прайсу. Симметрично вверх и вниз, к границам коридора не привязано.
function priceFactor(): number {
  const spread = Math.log(2)
  return Math.exp((Math.random() * 2 - 1) * spread)
}

function pick<T>(pool: T[], count: number): T[] {
  const copy = [...pool]
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy.slice(0, count)
}

function toLine(template: WorkTemplate): EstimateLineInput {
  const qty = randomInt(template.qtyFrom, template.qtyTo)
  const price = roundPrice(template.basePrice * priceFactor())
  // В реальных сметах строки иногда не сходятся: округлили вверх, пересчитали
  // цену и забыли сумму. Каждая пятая строка получает такое расхождение,
  // чтобы детерминированная проверка была видна в демо.
  const slip = Math.random() < 0.2 ? roundPrice(qty * price * 0.04) : 0
  return { name: template.name, unit: template.unit, qty, price,
           amount: qty * price + slip }
}

export function generateEstimateLines(): EstimateLineInput[] {
  const works = pick(WORKS, randomInt(9, 13)).map(toLine)
  const vague = pick(VAGUE, randomInt(1, 3)).map(toLine)
  const lines = pick([...works, ...vague], works.length + vague.length)
  // Иногда позиция дублируется — так бывает при сборке сметы из кусков.
  if (Math.random() < 0.35 && lines.length > 2) {
    const source = lines[randomInt(0, lines.length - 1)]
    lines.splice(randomInt(0, lines.length), 0, { ...source })
  }
  return lines
}
