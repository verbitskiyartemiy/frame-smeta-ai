import type { EstimateAnalysis } from './types'

const REASON_BENCHMARK =
  'это ориентир для вопроса подрядчику, а не оценка добросовестности'
const REASON_ABSTAIN =
  'позиция не сопоставлена со справочником работ — ориентир не выдаётся'

// Снимок ответа /api/estimate/analyze от 2026-07-28. Показывается только когда
// backend недоступен, и всегда под меткой DEMO_FIXTURE — за живой расчёт не выдаётся.
export const estimateFixture: EstimateAnalysis = {
  live: false,
  matched: 11,
  total: 14,
  minSample: 5,
  checks: [],
  source: '2 369 публичных цен · 22 компании · 7 городов · 47 типов работ',
  items: [
    { rawName: 'Демонтаж старых покрытий', normalizedWork: 'Демонтаж прочее', unitPrice: 450, quantity: 78, reason: REASON_BENCHMARK, benchmark: { median: 190, p10: 80, p90: 500, deviationPct: 136.8, sampleSize: 469, position: 'inside' } },
    { rawName: 'Штукатурка стен', normalizedWork: 'Штукатурка стен', unitPrice: 850, quantity: 210, reason: REASON_BENCHMARK, benchmark: { median: 500, p10: 300, p90: 1176, deviationPct: 70, sampleSize: 79, position: 'inside' } },
    { rawName: 'Шпаклёвка стен', normalizedWork: 'Шпаклёвка стен', unitPrice: 380, quantity: 210, reason: REASON_BENCHMARK, benchmark: { median: 300, p10: 211.7, p90: 578, deviationPct: 26.7, sampleSize: 24, position: 'inside' } },
    { rawName: 'Грунтовка', normalizedWork: 'Грунтовка', unitPrice: 80, quantity: 210, reason: REASON_BENCHMARK, benchmark: { median: 85, p10: 50, p90: 154, deviationPct: -5.9, sampleSize: 81, position: 'inside' } },
    { rawName: 'Покраска стен', normalizedWork: 'Покраска стен', unitPrice: 420, quantity: 180, reason: REASON_BENCHMARK, benchmark: { median: 250, p10: 200, p90: 300, deviationPct: 68, sampleSize: 21, position: 'above' } },
    { rawName: 'Укладка плитки (пол)', normalizedWork: 'Плитка на пол', unitPrice: 1800, quantity: 25, reason: REASON_BENCHMARK, benchmark: { median: 1100, p10: 878, p90: 2156, deviationPct: 63.6, sampleSize: 17, position: 'inside' } },
    { rawName: 'Укладка плитки (стены)', normalizedWork: 'Плитка на стену', unitPrice: 2100, quantity: 35, reason: REASON_BENCHMARK, benchmark: { median: 2816, p10: 2222, p90: 3080, deviationPct: -25.4, sampleSize: 5, position: 'below' } },
    { rawName: 'Электромонтаж (точка)', normalizedWork: null, unitPrice: 900, quantity: 65, reason: REASON_ABSTAIN, benchmark: null },
    { rawName: 'Разводка сантехники', normalizedWork: 'Разводка сантехники', unitPrice: 3500, quantity: 12, reason: REASON_BENCHMARK, benchmark: { median: 3018, p10: 1740, p90: 7650, deviationPct: 16, sampleSize: 38, position: 'inside' } },
    { rawName: 'Стяжка пола', normalizedWork: 'Стяжка пола', unitPrice: 650, quantity: 78, reason: REASON_BENCHMARK, benchmark: { median: 600, p10: 344, p90: 902, deviationPct: 8.3, sampleSize: 33, position: 'inside' } },
    { rawName: 'Укладка ламината', normalizedWork: 'Укладка ламината', unitPrice: 550, quantity: 53, reason: REASON_BENCHMARK, benchmark: { median: 375, p10: 301, p90: 491.5, deviationPct: 46.7, sampleSize: 22, position: 'above' } },
    { rawName: 'Потолки натяжные', normalizedWork: 'Натяжной потолок', unitPrice: 850, quantity: 78, reason: REASON_BENCHMARK, benchmark: { median: 850, p10: 400, p90: 1514.4, deviationPct: 0, sampleSize: 23, position: 'inside' } },
    { rawName: 'Установка дверей', normalizedWork: null, unitPrice: 5500, quantity: 6, reason: REASON_ABSTAIN, benchmark: null },
    { rawName: 'Материалы (ориентировочно)', normalizedWork: null, unitPrice: 636050, quantity: 1, reason: REASON_ABSTAIN, benchmark: null },
  ],
}
