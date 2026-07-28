export interface Project {
  id: string
  name: string
  type: 'cosmetic' | 'capital' | 'designer'
  address: string
  area: number
  rooms: number
  status: 'planning' | 'active' | 'completed'
  progress: number
  budget: number
  spent: number
  startDate: string
  endDate: string
  stages: Stage[]
  team: TeamMember[]
}

export interface Stage {
  id: string
  name: string
  status: 'pending' | 'active' | 'review' | 'completed'
  startDate: string
  endDate: string
  responsible: string
  progress: number
  budget: number
  spent: number
}

export interface Contractor {
  id: string
  name: string
  avatar: string
  specialization: string
  rating: number
  reviews: number
  projects: number
  verified: boolean
  recommended: number
  guarantee: string
  priceRange: string
  experience: string
  description: string
  portfolio: { title: string; image: string }[]
  badges: string[]
}

export interface Estimate {
  id: string
  contractor: string
  total: number
  items: EstimateItem[]
}

export interface EstimateItem {
  name: string
  unit: string
  quantity: number
  price: number
  total: number
}

export interface Thread {
  id: string
  title: string
  zone: string
  stage: string
  status: 'open' | 'waiting' | 'resolved'
  author: string
  authorRole: string
  date: string
  messages: ThreadMessage[]
}

export interface ThreadMessage {
  id: string
  author: string
  role: string
  text: string
  date: string
  attachments?: string[]
}

export interface Document {
  id: string
  name: string
  type: 'contract' | 'estimate' | 'act' | 'photo' | 'plan'
  stage: string
  date: string
  signed: boolean
  author: string
}

export interface Room {
  id: string
  name: string
  area: number
  materials: { name: string; brand: string }[]
  photoBefore: string
  photoAfter: string
}

export const projects: Project[] = [
  {
    id: '1',
    name: 'Ремонт квартиры на Невском',
    type: 'capital',
    address: 'Невский пр., 42, кв. 15',
    area: 78,
    rooms: 3,
    status: 'active',
    progress: 62,
    budget: 2850000,
    spent: 1767000,
    startDate: '2026-03-01',
    endDate: '2026-08-15',
    stages: [
      { id: 's1', name: 'Демонтаж', status: 'completed', startDate: '2026-03-01', endDate: '2026-03-15', responsible: 'Алексей Петров', progress: 100, budget: 180000, spent: 175000 },
      { id: 's2', name: 'Электромонтаж', status: 'completed', startDate: '2026-03-16', endDate: '2026-04-05', responsible: 'Игорь Волков', progress: 100, budget: 320000, spent: 335000 },
      { id: 's3', name: 'Сантехника', status: 'completed', startDate: '2026-04-01', endDate: '2026-04-20', responsible: 'Дмитрий Соколов', progress: 100, budget: 280000, spent: 272000 },
      { id: 's4', name: 'Штукатурка и выравнивание', status: 'active', startDate: '2026-04-10', endDate: '2026-05-10', responsible: 'Алексей Петров', progress: 75, budget: 450000, spent: 385000 },
      { id: 's5', name: 'Укладка плитки', status: 'active', startDate: '2026-05-01', endDate: '2026-05-25', responsible: 'Марат Хасанов', progress: 30, budget: 350000, spent: 120000 },
      { id: 's6', name: 'Чистовая отделка', status: 'pending', startDate: '2026-05-20', endDate: '2026-06-30', responsible: 'Алексей Петров', progress: 0, budget: 520000, spent: 0 },
      { id: 's7', name: 'Напольные покрытия', status: 'pending', startDate: '2026-06-15', endDate: '2026-07-10', responsible: 'Марат Хасанов', progress: 0, budget: 380000, spent: 0 },
      { id: 's8', name: 'Установка дверей и мебели', status: 'pending', startDate: '2026-07-10', endDate: '2026-08-15', responsible: 'Николай Фёдоров', progress: 0, budget: 370000, spent: 0 },
    ],
    team: [
      { name: 'Алексей Петров', role: 'Прораб / отделка', avatar: 'АП' },
      { name: 'Игорь Волков', role: 'Электрик', avatar: 'ИВ' },
      { name: 'Дмитрий Соколов', role: 'Сантехник', avatar: 'ДС' },
      { name: 'Марат Хасанов', role: 'Плиточник', avatar: 'МХ' },
      { name: 'Елена Краснова', role: 'Дизайнер', avatar: 'ЕК' },
    ],
  },
  {
    id: '2',
    name: 'Косметический ремонт ванной',
    type: 'cosmetic',
    address: 'ул. Рубинштейна, 8, кв. 3',
    area: 6,
    rooms: 1,
    status: 'planning',
    progress: 0,
    budget: 350000,
    spent: 0,
    startDate: '2026-06-01',
    endDate: '2026-07-15',
    stages: [
      { id: 's1', name: 'Демонтаж', status: 'pending', startDate: '2026-06-01', endDate: '2026-06-05', responsible: '', progress: 0, budget: 40000, spent: 0 },
      { id: 's2', name: 'Сантехника', status: 'pending', startDate: '2026-06-06', endDate: '2026-06-15', responsible: '', progress: 0, budget: 120000, spent: 0 },
      { id: 's3', name: 'Плитка и отделка', status: 'pending', startDate: '2026-06-16', endDate: '2026-07-05', responsible: '', progress: 0, budget: 150000, spent: 0 },
      { id: 's4', name: 'Финальная сборка', status: 'pending', startDate: '2026-07-06', endDate: '2026-07-15', responsible: '', progress: 0, budget: 40000, spent: 0 },
    ],
    team: [],
  },
]

export interface TeamMember {
  name: string
  role: string
  avatar: string
}

export const contractors: Contractor[] = [
  {
    id: 'c1',
    name: 'Алексей Петров',
    avatar: 'АП',
    specialization: 'Отделочные работы',
    rating: 4.9,
    reviews: 127,
    projects: 84,
    verified: true,
    recommended: 12,
    guarantee: '2 года',
    priceRange: 'от 3 500 ₽/м²',
    experience: '12 лет',
    description: 'Специализируюсь на комплексных отделочных работах в жилых помещениях. Работаю с командой из 4 человек. Все этапы — от штукатурки до финальной покраски.',
    portfolio: [
      { title: 'Квартира на Петроградке, 95м²', image: '' },
      { title: 'Студия на Васильевском, 32м²', image: '' },
      { title: 'Трёшка на Московском, 110м²', image: '' },
    ],
    badges: ['Топ-10 отделочников', 'Без срывов сроков', '100+ проектов'],
  },
  {
    id: 'c2',
    name: 'Игорь Волков',
    avatar: 'ИВ',
    specialization: 'Электромонтаж',
    rating: 4.8,
    reviews: 93,
    projects: 156,
    verified: true,
    recommended: 8,
    guarantee: '3 года',
    priceRange: 'от 800 ₽/точка',
    experience: '15 лет',
    description: 'Электромонтаж любой сложности. Сертифицированный электрик с допуском до 1000В. Работаю один или с напарником.',
    portfolio: [
      { title: 'Полная разводка 4-комнатной', image: '' },
      { title: 'Умный дом, квартира 120м²', image: '' },
    ],
    badges: ['Сертифицированный', 'Топ-5 электриков'],
  },
  {
    id: 'c3',
    name: 'Дмитрий Соколов',
    avatar: 'ДС',
    specialization: 'Сантехника',
    rating: 4.7,
    reviews: 68,
    projects: 112,
    verified: true,
    recommended: 5,
    guarantee: '2 года',
    priceRange: 'от 1 200 ₽/точка',
    experience: '10 лет',
    description: 'Установка и замена сантехники, разводка труб, тёплые полы. Работаю с премиальными и бюджетными материалами.',
    portfolio: [
      { title: 'Ванная комната под ключ', image: '' },
      { title: 'Разводка в новостройке', image: '' },
    ],
    badges: ['Гарантия качества'],
  },
  {
    id: 'c4',
    name: 'Марат Хасанов',
    avatar: 'МХ',
    specialization: 'Плиточные работы',
    rating: 4.9,
    reviews: 156,
    projects: 203,
    verified: true,
    recommended: 18,
    guarantee: '5 лет',
    priceRange: 'от 1 800 ₽/м²',
    experience: '18 лет',
    description: 'Укладка плитки, керамогранита, мозаики. Работаю с любыми форматами, включая крупноформат 120×60. Гарантия — 5 лет.',
    portfolio: [
      { title: 'Ванная в стиле лофт', image: '' },
      { title: 'Кухонный фартук мозаика', image: '' },
      { title: 'Террасная плитка, 40м²', image: '' },
    ],
    badges: ['Топ-3 плиточника', 'Мастер крупного формата', '200+ проектов'],
  },
  {
    id: 'c5',
    name: 'Елена Краснова',
    avatar: 'ЕК',
    specialization: 'Дизайн интерьера',
    rating: 4.8,
    reviews: 45,
    projects: 38,
    verified: true,
    recommended: 7,
    guarantee: 'Авторский надзор',
    priceRange: 'от 2 500 ₽/м²',
    experience: '8 лет',
    description: 'Дизайн-проекты для квартир и загородных домов. Полный пакет: планировка, визуализация, подбор материалов, авторский надзор.',
    portfolio: [
      { title: 'Скандинавский минимализм, 80м²', image: '' },
      { title: 'Неоклассика, 120м²', image: '' },
    ],
    badges: ['Авторский надзор', 'Дипломант выставки'],
  },
  {
    id: 'c6',
    name: 'Николай Фёдоров',
    avatar: 'НФ',
    specialization: 'Столярные работы',
    rating: 4.6,
    reviews: 34,
    projects: 67,
    verified: false,
    recommended: 3,
    guarantee: '1 год',
    priceRange: 'от 5 000 ₽/дверь',
    experience: '7 лет',
    description: 'Установка дверей, сборка и установка кухонь, встроенных шкафов. Работаю аккуратно, убираю за собой.',
    portfolio: [
      { title: 'Кухня на заказ', image: '' },
      { title: 'Встроенный шкаф-купе', image: '' },
    ],
    badges: [],
  },
]

export const estimates: Estimate[] = [
  {
    id: 'e1',
    contractor: 'Алексей Петров',
    total: 1420000,
    items: [
      { name: 'Демонтаж старых покрытий', unit: 'м²', quantity: 78, price: 450, total: 35100 },
      { name: 'Штукатурка стен', unit: 'м²', quantity: 210, price: 850, total: 178500 },
      { name: 'Шпаклёвка стен', unit: 'м²', quantity: 210, price: 380, total: 79800 },
      { name: 'Грунтовка', unit: 'м²', quantity: 210, price: 80, total: 16800 },
      { name: 'Покраска стен', unit: 'м²', quantity: 180, price: 420, total: 75600 },
      { name: 'Укладка плитки (пол)', unit: 'м²', quantity: 25, price: 1800, total: 45000 },
      { name: 'Укладка плитки (стены)', unit: 'м²', quantity: 35, price: 2100, total: 75000 },
      { name: 'Электромонтаж (точка)', unit: 'шт', quantity: 65, price: 900, total: 58500 },
      { name: 'Разводка сантехники', unit: 'точка', quantity: 12, price: 3500, total: 42000 },
      { name: 'Стяжка пола', unit: 'м²', quantity: 78, price: 650, total: 50700 },
      { name: 'Укладка ламината', unit: 'м²', quantity: 53, price: 550, total: 29150 },
      { name: 'Потолки натяжные', unit: 'м²', quantity: 78, price: 850, total: 66300 },
      { name: 'Установка дверей', unit: 'шт', quantity: 6, price: 5500, total: 33000 },
      { name: 'Материалы (ориентировочно)', unit: 'комплект', quantity: 1, price: 636050, total: 636050 },
    ],
  },
]

export const threads: Thread[] = [
  {
    id: 'e0',
    title: 'Старая проводка на кухне — доплата',
    zone: 'Кухня',
    stage: 'Электромонтаж',
    status: 'open',
    author: 'Игорь Волков',
    authorRole: 'Электрик',
    date: '2026-05-12',
    messages: [
      { id: 'm1', author: 'Игорь Волков', role: 'Электрик', text: 'Вскрыли стены на кухне: проводка старая, алюминий. Полная замена будет +12 000 ₽.', date: '2026-05-12', attachments: ['Фото_проводка.jpg'] },
      { id: 'm2', author: 'Вы', role: 'Заказчик', text: 'Это если менять полностью, без частичного ремонта?', date: '2026-05-12' },
      { id: 'm3', author: 'Игорь Волков', role: 'Электрик', text: 'Частично не советую: старые скрутки греются, это риск перегрева и пожара. Менять лучше целиком.', date: '2026-05-12' },
      { id: 'm4', author: 'Вы', role: 'Заказчик', text: 'Понял, тогда меняем полностью.', date: '2026-05-12' },
    ],
  },
  {
    id: 'p0',
    title: 'Приёмка: плитка в ванной',
    zone: 'Ванная',
    stage: 'Укладка плитки',
    status: 'waiting',
    author: 'Марат Хасанов',
    authorRole: 'Плиточник',
    date: '2026-05-11',
    messages: [
      { id: 'm1', author: 'Марат Хасанов', role: 'Плиточник', text: 'Укладка плитки в ванной завершена, затирка нанесена. Фото прикрепил.', date: '2026-05-11', attachments: ['Плитка_ванная_1.jpg', 'Плитка_ванная_2.jpg'] },
      { id: 'm2', author: 'Марат Хасанов', role: 'Плиточник', text: 'Прошу принять этап, чтобы перейти к установке сантехники.', date: '2026-05-11' },
    ],
  },
  {
    id: 't1',
    title: 'Розетки на кухне — расположение',
    zone: 'Кухня',
    stage: 'Электромонтаж',
    status: 'resolved',
    author: 'Елена Краснова',
    authorRole: 'Дизайнер',
    date: '2026-03-20',
    messages: [
      { id: 'm1', author: 'Елена Краснова', role: 'Дизайнер', text: 'По плану розетки за столешницей должны быть на высоте 110 см от пола. Нужно 6 точек вдоль рабочей зоны + 2 для вытяжки.', date: '2026-03-20', attachments: ['План кухни.pdf'] },
      { id: 'm2', author: 'Игорь Волков', role: 'Электрик', text: 'Принял. По фартуку 6 точек, по вытяжке — 2 на 200 см. Провожу завтра.', date: '2026-03-20' },
      { id: 'm3', author: 'Вы', role: 'Заказчик', text: 'Подтверждаю. Добавьте ещё одну розетку справа для кофемашины.', date: '2026-03-21' },
      { id: 'm4', author: 'Игорь Волков', role: 'Электрик', text: 'Готово, все 9 точек разведены. Фото прикрепил.', date: '2026-03-22', attachments: ['Фото_розетки_кухня.jpg'] },
    ],
  },
  {
    id: 't2',
    title: 'Трещина в стене спальни',
    zone: 'Спальня',
    stage: 'Штукатурка и выравнивание',
    status: 'open',
    author: 'Алексей Петров',
    authorRole: 'Прораб',
    date: '2026-05-02',
    messages: [
      { id: 'm1', author: 'Алексей Петров', role: 'Прораб', text: 'Обнаружил трещину в несущей стене спальни, глубина ~3мм. Нужно армирование сеткой перед штукатуркой. Это +1 день и примерно 8 000₽ на материалы.', date: '2026-05-02', attachments: ['Трещина_фото.jpg'] },
      { id: 'm2', author: 'Вы', role: 'Заказчик', text: 'Насколько это критично? Может ли трещина расширяться?', date: '2026-05-02' },
    ],
  },
  {
    id: 't3',
    title: 'Затирка плитки — выбор цвета',
    zone: 'Ванная',
    stage: 'Укладка плитки',
    status: 'waiting',
    author: 'Марат Хасанов',
    authorRole: 'Плиточник',
    date: '2026-05-05',
    messages: [
      { id: 'm1', author: 'Марат Хасанов', role: 'Плиточник', text: 'Плитка уложена на 80%. Нужно определиться с цветом затирки. Варианты: белая, серая, графит. По дизайн-проекту графит, но хочу уточнить.', date: '2026-05-05' },
      { id: 'm2', author: 'Елена Краснова', role: 'Дизайнер', text: 'По проекту графит (Ceresit CE 40 №16). Это лучше сочетается с серой плиткой и скрывает загрязнения.', date: '2026-05-05' },
    ],
  },
  {
    id: 't4',
    title: 'Согласование этапа: демонтаж',
    zone: 'Вся квартира',
    stage: 'Демонтаж',
    status: 'resolved',
    author: 'Алексей Петров',
    authorRole: 'Прораб',
    date: '2026-03-14',
    messages: [
      { id: 'm1', author: 'Алексей Петров', role: 'Прораб', text: 'Демонтаж завершён. Вывезли 3 контейнера мусора. Стены и полы очищены. Прошу принять этап.', date: '2026-03-14', attachments: ['Фото_демонтаж_1.jpg', 'Фото_демонтаж_2.jpg', 'Акт_демонтаж.pdf'] },
      { id: 'm2', author: 'Вы', role: 'Заказчик', text: 'Принято. Оплату подтверждаю через гарант.', date: '2026-03-15' },
    ],
  },
]

export const documents: Document[] = [
  { id: 'd1', name: 'Договор подряда — Петров А.В.', type: 'contract', stage: 'Общее', date: '2026-02-28', signed: true, author: 'Система' },
  { id: 'd2', name: 'Договор подряда — Волков И.С.', type: 'contract', stage: 'Общее', date: '2026-03-01', signed: true, author: 'Система' },
  { id: 'd3', name: 'Смета на отделочные работы', type: 'estimate', stage: 'Общее', date: '2026-02-25', signed: true, author: 'Алексей Петров' },
  { id: 'd4', name: 'Акт приёмки — Демонтаж', type: 'act', stage: 'Демонтаж', date: '2026-03-15', signed: true, author: 'Система' },
  { id: 'd5', name: 'Акт приёмки — Электромонтаж', type: 'act', stage: 'Электромонтаж', date: '2026-04-05', signed: true, author: 'Система' },
  { id: 'd6', name: 'Акт приёмки — Сантехника', type: 'act', stage: 'Сантехника', date: '2026-04-20', signed: true, author: 'Система' },
  { id: 'd7', name: 'Фотоотчёт — Демонтаж', type: 'photo', stage: 'Демонтаж', date: '2026-03-14', signed: false, author: 'Алексей Петров' },
  { id: 'd8', name: 'Фотоотчёт — Электромонтаж', type: 'photo', stage: 'Электромонтаж', date: '2026-04-04', signed: false, author: 'Игорь Волков' },
  { id: 'd9', name: 'Дизайн-проект (финальная версия)', type: 'plan', stage: 'Общее', date: '2026-02-20', signed: true, author: 'Елена Краснова' },
  { id: 'd10', name: 'План электроточек', type: 'plan', stage: 'Электромонтаж', date: '2026-03-10', signed: true, author: 'Елена Краснова' },
]

export const rooms: Room[] = [
  {
    id: 'r1', name: 'Гостиная', area: 22,
    materials: [
      { name: 'Краска стен', brand: 'Dulux Trade Diamond Matt, белый' },
      { name: 'Ламинат', brand: 'Quick-Step Impressive, дуб натуральный' },
      { name: 'Потолок', brand: 'Натяжной, матовый белый' },
    ],
    photoBefore: '', photoAfter: '',
  },
  {
    id: 'r2', name: 'Спальня', area: 16,
    materials: [
      { name: 'Краска стен', brand: 'Tikkurila Harmony, серый' },
      { name: 'Ламинат', brand: 'Quick-Step Impressive, дуб серый' },
      { name: 'Потолок', brand: 'Натяжной, матовый белый' },
    ],
    photoBefore: '', photoAfter: '',
  },
  {
    id: 'r3', name: 'Кухня', area: 14,
    materials: [
      { name: 'Плитка пол', brand: 'Kerama Marazzi, керамогранит серый' },
      { name: 'Фартук', brand: 'Керамическая плитка, белый кабанчик' },
      { name: 'Краска стен', brand: 'Dulux Kitchen Matt, белый' },
    ],
    photoBefore: '', photoAfter: '',
  },
  {
    id: 'r4', name: 'Ванная', area: 6,
    materials: [
      { name: 'Плитка пол', brand: 'Italon Charme Evo, серый мрамор' },
      { name: 'Плитка стены', brand: 'Italon Charme Evo, белый мрамор' },
      { name: 'Затирка', brand: 'Ceresit CE 40, графит' },
    ],
    photoBefore: '', photoAfter: '',
  },
  {
    id: 'r5', name: 'Прихожая', area: 8,
    materials: [
      { name: 'Плитка пол', brand: 'Kerama Marazzi, керамогранит тёмный' },
      { name: 'Краска стен', brand: 'Tikkurila Harmony, белый' },
    ],
    photoBefore: '', photoAfter: '',
  },
]

export const aiChatMessages = [
  { role: 'assistant' as const, text: 'Здравствуйте! Я AI-консультант платформы ФРЕЙМ. Помогу разобраться в вопросах ремонта: оценю стоимость работ, объясню технические термины, помогу сформулировать техзадание. Что вас интересует?' },
]
