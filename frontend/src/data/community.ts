export type AuthorRole = 'customer' | 'contractor' | 'designer' | 'expert'

export interface ForumCategory {
  id: string
  name: string
  icon: string
  description: string
  topicsCount: number
  isProfessional: boolean
  color: string
}

export interface ForumComment {
  id: string
  author: string
  authorRole: AuthorRole
  authorAvatar: string
  date: string
  text: string
  likes: number
  isBestAnswer: boolean
}

export interface ForumTopic {
  id: string
  title: string
  categoryId: string
  author: string
  authorRole: AuthorRole
  authorAvatar: string
  date: string
  preview: string
  content: string
  replies: number
  views: number
  likes: number
  isPinned: boolean
  isHot: boolean
  hasExpertAnswer: boolean
  comments: ForumComment[]
}

export interface EducationVideo {
  id: string
  title: string
  category: string
  duration: number
  views: number
  author: string
  authorRole: string
  thumbnail: string
  description: string
}

export interface Challenge {
  id: string
  title: string
  description: string
  reward: string
  participants: number
  deadline: string
  status: 'active' | 'completed'
  difficulty: 'easy' | 'medium' | 'hard'
  prize: string
}

export interface RatingEntry {
  rank: number
  name: string
  avatar: string
  specialization: string
  rating: number
  projects: number
  reviews: number
  trend: 'up' | 'down' | 'stable'
  isNew: boolean
}

export const roleLabels: Record<AuthorRole, string> = {
  customer: 'Заказчик',
  contractor: 'Подрядчик',
  designer: 'Дизайнер',
  expert: 'Эксперт',
}

export const roleColors: Record<AuthorRole, string> = {
  customer: 'bg-slate-100 text-slate-700',
  contractor: 'bg-blue-100 text-blue-700',
  designer: 'bg-purple-100 text-purple-700',
  expert: 'bg-emerald-100 text-emerald-700',
}

export const forumCategories: ForumCategory[] = [
  { id: 'all', name: 'Все темы', icon: '💬', description: 'Все обсуждения', topicsCount: 348, isProfessional: false, color: 'bg-slate-100 text-slate-700' },
  { id: 'general', name: 'Общие вопросы', icon: '🏠', description: 'Планирование, документы, согласования', topicsCount: 84, isProfessional: false, color: 'bg-amber-100 text-amber-700' },
  { id: 'electric', name: 'Электрика', icon: '⚡', description: 'Проводка, освещение, умный дом', topicsCount: 62, isProfessional: false, color: 'bg-yellow-100 text-yellow-700' },
  { id: 'plumbing', name: 'Сантехника', icon: '🚿', description: 'Разводка, замена, тёплый пол', topicsCount: 54, isProfessional: false, color: 'bg-cyan-100 text-cyan-700' },
  { id: 'finishing', name: 'Отделка', icon: '🎨', description: 'Покраска, обои, плитка, ламинат', topicsCount: 78, isProfessional: false, color: 'bg-rose-100 text-rose-700' },
  { id: 'design', name: 'Дизайн и интерьер', icon: '🛋️', description: 'Стили, мебель, освещение', topicsCount: 45, isProfessional: false, color: 'bg-purple-100 text-purple-700' },
  { id: 'diy', name: 'DIY и лайфхаки', icon: '🔧', description: 'Самостоятельный ремонт', topicsCount: 28, isProfessional: false, color: 'bg-green-100 text-green-700' },
  { id: 'pro', name: 'Профессиональный раздел', icon: '👷', description: 'Только для верифицированных исполнителей', topicsCount: 37, isProfessional: true, color: 'bg-blue-100 text-blue-700' },
]

export const forumTopics: ForumTopic[] = [
  {
    id: 't1',
    title: 'Как выбрать ламинат для квартиры с тёплым полом?',
    categoryId: 'finishing',
    author: 'Мария К.',
    authorRole: 'customer',
    authorAvatar: 'МК',
    date: '2026-05-10',
    preview: 'Делаем капремонт, по всей квартире планируется водяной тёплый пол. Производитель ламината пишет про класс износа 33, но как насчёт совместимости с подогревом?',
    content: 'Делаем капремонт, по всей квартире планируется водяной тёплый пол. Производитель ламината пишет про класс износа 33, но как насчёт совместимости с подогревом? У кого был опыт — какой ламинат не повело за пару лет эксплуатации? Бюджет на покрытие — до 3 000 ₽/м². Площадь — 78 м².',
    replies: 12,
    views: 847,
    likes: 23,
    isPinned: false,
    isHot: true,
    hasExpertAnswer: true,
    comments: [
      {
        id: 'c1', author: 'Алексей Петров', authorRole: 'contractor', authorAvatar: 'АП', date: '2026-05-10',
        text: 'Для тёплого пола ищите маркировку «Warm Wasser» или специальный значок с волной. Quick-Step Impressive Ultra держит до +28°C. У меня на двух объектах стоит уже 4 года — без замечаний. Главное: не превышайте +27°C поверхности и используйте подложку с теплопроводностью не выше 0,15 м²·K/Вт.',
        likes: 18, isBestAnswer: true,
      },
      {
        id: 'c2', author: 'Дмитрий Соколов', authorRole: 'contractor', authorAvatar: 'ДС', date: '2026-05-11',
        text: 'Добавлю про монтаж: первые 3 дня после укладки тёплый пол не включаем. Потом плавно поднимаем температуру по +3°C в сутки. Если резко включить — может пойти волной.',
        likes: 9, isBestAnswer: false,
      },
      {
        id: 'c3', author: 'Мария К.', authorRole: 'customer', authorAvatar: 'МК', date: '2026-05-11',
        text: 'Спасибо! А подложку какую посоветуете? Видела вариант 2 мм пробковая — пишут что специально для тёплого пола.',
        likes: 2, isBestAnswer: false,
      },
      {
        id: 'c4', author: 'Алексей Петров', authorRole: 'contractor', authorAvatar: 'АП', date: '2026-05-11',
        text: 'Пробковая 2 мм — нормальный вариант, но она снижает теплоотдачу примерно на 15%. Я обычно ставлю Tuplex 3 мм с алюминиевой плёнкой — она работает на отражение, тепло идёт лучше.',
        likes: 14, isBestAnswer: false,
      },
    ],
  },
  {
    id: 't2',
    title: 'Демонтаж несущей стены — кто согласовывал в СПб?',
    categoryId: 'general',
    author: 'Андрей В.',
    authorRole: 'customer',
    authorAvatar: 'АВ',
    date: '2026-05-08',
    preview: 'Хочу объединить кухню с гостиной, между ними несущая стена. Кто проходил согласование в ГЖИ Петербурга — поделитесь опытом по срокам и стоимости...',
    content: 'Хочу объединить кухню с гостиной, между ними несущая стена. Кто проходил согласование в ГЖИ Петербурга — поделитесь опытом по срокам и стоимости проекта. Дом — кирпичный 1986 года, 5 этаж. Слышал про необходимость техзаключения, проекта от организации с допуском СРО, и потом согласование в БТИ и ГЖИ.',
    replies: 18,
    views: 1432,
    likes: 41,
    isPinned: true,
    isHot: true,
    hasExpertAnswer: true,
    comments: [
      {
        id: 'c1', author: 'Елена Краснова', authorRole: 'designer', authorAvatar: 'ЕК', date: '2026-05-08',
        text: 'Проходила в 2025 году — закладывайте 4-6 месяцев на бумажную часть. Стоимость проекта с усилением — 80 000–150 000 ₽ в зависимости от пролёта. Усиление стандартно делается швеллером или двутавром. Самостоятельно ничего не пытайтесь — это работа исключительно для организации с СРО.',
        likes: 28, isBestAnswer: true,
      },
    ],
  },
  {
    id: 't3',
    title: 'Натяжной vs гипсокартонный потолок — что лучше в 2026?',
    categoryId: 'finishing',
    author: 'Ольга М.',
    authorRole: 'customer',
    authorAvatar: 'ОМ',
    date: '2026-05-06',
    preview: 'Дилемма. Натяжной — быстро, но боюсь, что выглядит дёшево. ГКЛ — основательно, но дороже и долго. Какие плюсы и минусы каждого варианта на сегодня?',
    content: 'Дилемма. Натяжной — быстро, но боюсь, что выглядит дёшево. ГКЛ — основательно, но дороже и долго. Какие плюсы и минусы каждого варианта на сегодня?',
    replies: 24,
    views: 2103,
    likes: 56,
    isPinned: false,
    isHot: true,
    hasExpertAnswer: true,
    comments: [],
  },
  {
    id: 't4',
    title: 'Электрики, помогите рассчитать нагрузку на квартиру 100 м²',
    categoryId: 'electric',
    author: 'Сергей П.',
    authorRole: 'customer',
    authorAvatar: 'СП',
    date: '2026-05-05',
    preview: 'Планируется: 2 кондиционера, варочная панель 7 кВт, духовка, посудомойка, 2 тёплых пола в ванных. Стандартного ввода 15 кВт хватит?',
    content: 'Планируется: 2 кондиционера, варочная панель 7 кВт, духовка, посудомойка, 2 тёплых пола в ванных. Стандартного ввода 15 кВт хватит?',
    replies: 9,
    views: 612,
    likes: 12,
    isPinned: false,
    isHot: false,
    hasExpertAnswer: true,
    comments: [],
  },
  {
    id: 't5',
    title: 'Ошибки при укладке тёплого пола — обзор для коллег',
    categoryId: 'pro',
    author: 'Марат Хасанов',
    authorRole: 'contractor',
    authorAvatar: 'МХ',
    date: '2026-05-04',
    preview: 'За 18 лет работы насмотрелся всякого. Собрал топ-7 ошибок, которые встречаю на чужих объектах — может, кому пригодится...',
    content: 'За 18 лет работы насмотрелся всякого. Собрал топ-7 ошибок: 1) Греющий кабель ближе 5 см от стены — обрыв через год. 2) Стяжка тоньше 30 мм — трескается. 3) Без датчика в гофре — потом не заменить. 4) Тестирование под нагрузкой только после полного высыхания (28 дней!). 5) Алюминиевый мат под плитку — не работает. 6) Тёплый пол под мебелью — перегрев и поломка. 7) Один контур на >10 м² — неравномерный прогрев.',
    replies: 31,
    views: 1856,
    likes: 87,
    isPinned: true,
    isHot: true,
    hasExpertAnswer: false,
    comments: [],
  },
  {
    id: 't6',
    title: 'Можно ли клеить обои на старую краску?',
    categoryId: 'finishing',
    author: 'Виктория Л.',
    authorRole: 'customer',
    authorAvatar: 'ВЛ',
    date: '2026-05-03',
    preview: 'В прошлый раз красили водоэмульсионкой 5 лет назад. Хочу поклеить флизелиновые обои — нужно ли смывать всю краску, или достаточно прогрунтовать?',
    content: 'В прошлый раз красили водоэмульсионкой 5 лет назад. Хочу поклеить флизелиновые обои — нужно ли смывать всю краску, или достаточно прогрунтовать?',
    replies: 14,
    views: 923,
    likes: 18,
    isPinned: false,
    isHot: false,
    hasExpertAnswer: true,
    comments: [],
  },
  {
    id: 't7',
    title: 'Замена стояка с соседями — пошаговый алгоритм',
    categoryId: 'plumbing',
    author: 'Игорь Н.',
    authorRole: 'customer',
    authorAvatar: 'ИН',
    date: '2026-05-02',
    preview: 'Меняем стояк ХВС/ГВС на полипропилен. Надо согласовать с соседями сверху и снизу. Как организовать процесс и не остаться без воды на неделю?',
    content: 'Меняем стояк ХВС/ГВС на полипропилен. Надо согласовать с соседями сверху и снизу. Как организовать процесс и не остаться без воды на неделю?',
    replies: 16,
    views: 1187,
    likes: 22,
    isPinned: false,
    isHot: false,
    hasExpertAnswer: true,
    comments: [],
  },
  {
    id: 't8',
    title: 'Лайфхак: как подвесить тяжёлый шкаф на гипсокартон',
    categoryId: 'diy',
    author: 'Павел Р.',
    authorRole: 'customer',
    authorAvatar: 'ПР',
    date: '2026-05-01',
    preview: 'Делюсь способом, который реально работает. Купил молли-болты Hilti HSP — держат 35 кг каждый при правильной установке...',
    content: 'Делюсь способом, который реально работает. Купил молли-болты Hilti HSP — держат 35 кг каждый при правильной установке. На шкаф 80 кг ставлю 6 точек: 3 сверху, 3 снизу. За 2 года ни один не вылетел. Главное — раскрытие крыльев контролировать.',
    replies: 8,
    views: 542,
    likes: 31,
    isPinned: false,
    isHot: false,
    hasExpertAnswer: false,
    comments: [],
  },
  {
    id: 't9',
    title: 'Кто работал с дизайнером Еленой Красновой? Поделитесь опытом',
    categoryId: 'design',
    author: 'Наталья К.',
    authorRole: 'customer',
    authorAvatar: 'НК',
    date: '2026-04-29',
    preview: 'Рассматриваю варианты дизайнеров через биржу Фрейма. Елена Краснова с рейтингом 4.8 — высокий, но мало отзывов на платформе. У кого был опыт?',
    content: 'Рассматриваю варианты дизайнеров через биржу Фрейма. Елена Краснова с рейтингом 4.8 — высокий, но мало отзывов на платформе. У кого был опыт?',
    replies: 7,
    views: 389,
    likes: 11,
    isPinned: false,
    isHot: false,
    hasExpertAnswer: false,
    comments: [],
  },
  {
    id: 't10',
    title: 'Какую затирку выбрать для крупноформата 120×60?',
    categoryId: 'finishing',
    author: 'Дмитрий А.',
    authorRole: 'customer',
    authorAvatar: 'ДА',
    date: '2026-04-28',
    preview: 'Кладём керамогранит 120×60 на стены в ванной. Швы планируем минимальные — 1.5 мм. Эпоксидка или цементная? И какая марка надёжнее?',
    content: 'Кладём керамогранит 120×60 на стены в ванной. Швы планируем минимальные — 1.5 мм. Эпоксидка или цементная? И какая марка надёжнее?',
    replies: 11,
    views: 728,
    likes: 16,
    isPinned: false,
    isHot: false,
    hasExpertAnswer: true,
    comments: [],
  },
]

export const educationVideos: EducationVideo[] = [
  {
    id: 'v1',
    title: 'Разводка электрики в новостройке: пошаговое руководство',
    category: 'Электрика',
    duration: 28,
    views: 12450,
    author: 'Игорь Волков',
    authorRole: 'Электрик-эксперт',
    thumbnail: 'from-yellow-400 to-orange-500',
    description: 'От плана до монтажа щита: разбираем последовательность работ, типичные ошибки и нормы ПУЭ.',
  },
  {
    id: 'v2',
    title: 'Укладка плитки ёлочкой — техника от мастера',
    category: 'Плитка',
    duration: 35,
    views: 8932,
    author: 'Марат Хасанов',
    authorRole: 'Плиточник-эксперт',
    thumbnail: 'from-rose-400 to-pink-500',
    description: 'Как добиться идеальной геометрии при укладке плитки ёлочкой и шеврон. С разбором инструментов.',
  },
  {
    id: 'v3',
    title: 'Штукатурка стен под покраску: технология',
    category: 'Отделка',
    duration: 42,
    views: 15234,
    author: 'Алексей Петров',
    authorRole: 'Прораб',
    thumbnail: 'from-blue-400 to-cyan-500',
    description: 'Машинная штукатурка, маяки, правило, шпаклёвка. Как добиться гладкой поверхности за один заход.',
  },
  {
    id: 'v4',
    title: 'Замена смесителя за 15 минут — DIY',
    category: 'Сантехника',
    duration: 15,
    views: 23890,
    author: 'Дмитрий Соколов',
    authorRole: 'Сантехник',
    thumbnail: 'from-cyan-400 to-teal-500',
    description: 'Простая инструкция для замены смесителя без вызова мастера. Какие инструменты нужны и что не сделать.',
  },
  {
    id: 'v5',
    title: 'Дизайн маленькой квартиры: 10 приёмов',
    category: 'Дизайн',
    duration: 22,
    views: 18763,
    author: 'Елена Краснова',
    authorRole: 'Дизайнер интерьеров',
    thumbnail: 'from-purple-400 to-fuchsia-500',
    description: 'Как визуально увеличить пространство 30–40 м². Свет, цвет, зеркала, скрытое хранение.',
  },
  {
    id: 'v6',
    title: 'Демонтаж старого ремонта: что важно',
    category: 'Демонтаж',
    duration: 18,
    views: 6541,
    author: 'Алексей Петров',
    authorRole: 'Прораб',
    thumbnail: 'from-slate-400 to-slate-600',
    description: 'Безопасный демонтаж, утилизация мусора, что нельзя трогать без проекта.',
  },
]

export const challenges: Challenge[] = [
  {
    id: 'ch1',
    title: 'Ванная под ключ за 30 дней',
    description: 'Полный цикл от демонтажа до приёмки за 30 рабочих дней. Площадь от 4 м².',
    reward: 'Бейдж «Скоростной мастер» + продвижение в рейтинге',
    participants: 47,
    deadline: '2026-08-01',
    status: 'active',
    difficulty: 'medium',
    prize: '50 000 ₽',
  },
  {
    id: 'ch2',
    title: 'Электрика без замечаний',
    description: '10 проектов подряд с приёмкой технадзора без единого замечания.',
    reward: 'Бейдж «Безупречный электрик» + персональный значок в профиле',
    participants: 23,
    deadline: '2026-09-15',
    status: 'active',
    difficulty: 'hard',
    prize: '100 000 ₽',
  },
  {
    id: 'ch3',
    title: 'Эко-ремонт',
    description: 'Проект с использованием только экологичных материалов с подтверждёнными сертификатами.',
    reward: 'Зелёный бейдж + рекомендация в эко-секции',
    participants: 12,
    deadline: '2026-10-01',
    status: 'active',
    difficulty: 'easy',
    prize: '30 000 ₽',
  },
  {
    id: 'ch4',
    title: 'Дизайн-проект года',
    description: 'Лучший реализованный дизайн-проект по голосованию сообщества.',
    reward: 'Публикация на главной + интервью в блоге',
    participants: 89,
    deadline: '2026-12-31',
    status: 'active',
    difficulty: 'hard',
    prize: '200 000 ₽',
  },
]

export const ratingsByCategory: Record<string, RatingEntry[]> = {
  'Отделка': [
    { rank: 1, name: 'Алексей Петров', avatar: 'АП', specialization: 'Отделочные работы', rating: 4.9, projects: 84, reviews: 127, trend: 'stable', isNew: false },
    { rank: 2, name: 'Сергей Кузнецов', avatar: 'СК', specialization: 'Отделочные работы', rating: 4.85, projects: 67, reviews: 98, trend: 'up', isNew: false },
    { rank: 3, name: 'Михаил Орлов', avatar: 'МО', specialization: 'Отделочные работы', rating: 4.8, projects: 102, reviews: 156, trend: 'up', isNew: true },
    { rank: 4, name: 'Артём Лебедев', avatar: 'АЛ', specialization: 'Отделочные работы', rating: 4.75, projects: 59, reviews: 81, trend: 'down', isNew: false },
    { rank: 5, name: 'Виктор Никитин', avatar: 'ВН', specialization: 'Отделочные работы', rating: 4.7, projects: 48, reviews: 64, trend: 'stable', isNew: false },
  ],
  'Электромонтаж': [
    { rank: 1, name: 'Игорь Волков', avatar: 'ИВ', specialization: 'Электромонтаж', rating: 4.92, projects: 156, reviews: 93, trend: 'up', isNew: false },
    { rank: 2, name: 'Роман Сидоров', avatar: 'РС', specialization: 'Электромонтаж', rating: 4.88, projects: 134, reviews: 87, trend: 'stable', isNew: false },
    { rank: 3, name: 'Денис Морозов', avatar: 'ДМ', specialization: 'Электромонтаж', rating: 4.83, projects: 98, reviews: 76, trend: 'up', isNew: true },
  ],
  'Сантехника': [
    { rank: 1, name: 'Дмитрий Соколов', avatar: 'ДС', specialization: 'Сантехника', rating: 4.78, projects: 112, reviews: 68, trend: 'stable', isNew: false },
    { rank: 2, name: 'Олег Тихонов', avatar: 'ОТ', specialization: 'Сантехника', rating: 4.75, projects: 89, reviews: 54, trend: 'up', isNew: false },
    { rank: 3, name: 'Андрей Соловьёв', avatar: 'АС', specialization: 'Сантехника', rating: 4.7, projects: 76, reviews: 47, trend: 'down', isNew: false },
  ],
  'Плитка': [
    { rank: 1, name: 'Марат Хасанов', avatar: 'МХ', specialization: 'Плиточные работы', rating: 4.95, projects: 203, reviews: 156, trend: 'stable', isNew: false },
    { rank: 2, name: 'Виталий Зайцев', avatar: 'ВЗ', specialization: 'Плиточные работы', rating: 4.87, projects: 145, reviews: 102, trend: 'up', isNew: false },
    { rank: 3, name: 'Артур Григорян', avatar: 'АГ', specialization: 'Плиточные работы', rating: 4.82, projects: 118, reviews: 89, trend: 'up', isNew: true },
  ],
  'Дизайн': [
    { rank: 1, name: 'Елена Краснова', avatar: 'ЕК', specialization: 'Дизайн интерьера', rating: 4.85, projects: 38, reviews: 45, trend: 'up', isNew: false },
    { rank: 2, name: 'Анна Белова', avatar: 'АБ', specialization: 'Дизайн интерьера', rating: 4.8, projects: 52, reviews: 67, trend: 'stable', isNew: false },
    { rank: 3, name: 'Кирилл Власов', avatar: 'КВ', specialization: 'Дизайн интерьера', rating: 4.72, projects: 29, reviews: 31, trend: 'down', isNew: false },
  ],
}

export function getTopicById(id: string): ForumTopic | undefined {
  return forumTopics.find((t) => t.id === id)
}

export function getCategoryById(id: string): ForumCategory | undefined {
  return forumCategories.find((c) => c.id === id)
}
