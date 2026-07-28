import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  SlidersHorizontal,
  CheckCircle2,
  Star,
  Heart,
  Briefcase,
  Clock,
  Shield,
} from "lucide-react";
import { contractors } from "../data/mock";

const specializations = [
  "Все",
  "Отделка",
  "Электромонтаж",
  "Сантехника",
  "Плитка",
  "Дизайн",
  "Столярные",
];

const specMap: Record<string, string> = {
  Отделка: "Отделочные работы",
  Электромонтаж: "Электромонтаж",
  Сантехника: "Сантехника",
  Плитка: "Плиточные работы",
  Дизайн: "Дизайн интерьера",
  Столярные: "Столярные работы",
};

const avatarColors: Record<string, string> = {
  А: "bg-blue-500",
  Б: "bg-emerald-500",
  В: "bg-violet-500",
  Г: "bg-rose-500",
  Д: "bg-amber-500",
  Е: "bg-teal-500",
  Ж: "bg-pink-500",
  З: "bg-cyan-500",
  И: "bg-indigo-500",
  К: "bg-orange-500",
  Л: "bg-lime-600",
  М: "bg-purple-500",
  Н: "bg-red-500",
  О: "bg-sky-500",
  П: "bg-green-500",
};

function getAvatarColor(letter: string) {
  return avatarColors[letter] || "bg-slate-500";
}

export default function Contractors() {
  const [search, setSearch] = useState("");
  const [specFilter, setSpecFilter] = useState("Все");
  const [minRating, setMinRating] = useState(0);
  const [onlyVerified, setOnlyVerified] = useState(false);

  const filtered = useMemo(() => {
    return contractors.filter((c) => {
      if (search && !c.name.toLowerCase().includes(search.toLowerCase()))
        return false;
      if (specFilter !== "Все" && c.specialization !== specMap[specFilter])
        return false;
      if (minRating > 0 && c.rating < minRating) return false;
      if (onlyVerified && !c.verified) return false;
      return true;
    });
  }, [search, specFilter, minRating, onlyVerified]);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">
          Биржа подрядчиков
        </h1>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Поиск по имени..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 w-64 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-frame-500 focus:border-transparent"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
            <SlidersHorizontal className="w-4 h-4" />
            Фильтры
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <div className="flex items-center gap-2">
          {specializations.map((spec) => (
            <button
              key={spec}
              onClick={() => setSpecFilter(spec)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                specFilter === spec
                  ? "bg-frame-600 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {spec}
            </button>
          ))}
        </div>

        <div className="h-6 w-px bg-slate-200" />

        <select
          value={minRating}
          onChange={(e) => setMinRating(Number(e.target.value))}
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-600 focus:outline-none focus:ring-2 focus:ring-frame-500"
        >
          <option value={0}>Любой рейтинг</option>
          <option value={4.5}>4.5+</option>
          <option value={4.7}>4.7+</option>
          <option value={4.9}>4.9+</option>
        </select>

        <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={onlyVerified}
            onChange={(e) => setOnlyVerified(e.target.checked)}
            className="w-4 h-4 rounded border-slate-300 text-frame-600 focus:ring-frame-500"
          />
          Только проверенные
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {filtered.map((contractor) => (
          <div
            key={contractor.id}
            className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3 mb-3">
              <div
                className={`w-12 h-12 rounded-full ${getAvatarColor(contractor.avatar[0])} flex items-center justify-center text-white font-semibold text-sm shrink-0`}
              >
                {contractor.avatar}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <h3 className="text-base font-semibold text-slate-900 truncate">
                    {contractor.name}
                  </h3>
                  {contractor.verified && (
                    <CheckCircle2 className="w-4.5 h-4.5 text-blue-500 shrink-0 fill-blue-500 stroke-white" />
                  )}
                </div>
                <span className="inline-block mt-1 px-2 py-0.5 rounded-md bg-slate-100 text-xs font-medium text-slate-600">
                  {contractor.specialization}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-1 mb-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`w-4 h-4 ${
                    i < Math.round(contractor.rating)
                      ? "text-amber-400 fill-amber-400"
                      : "text-slate-200 fill-slate-200"
                  }`}
                />
              ))}
              <span className="ml-1 text-sm font-semibold text-slate-900">
                {contractor.rating}
              </span>
              <span className="text-sm text-slate-400">
                ({contractor.reviews} отзывов)
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-3 text-center">
              <div className="bg-slate-50 rounded-lg py-2 px-1">
                <Briefcase className="w-4 h-4 text-slate-400 mx-auto mb-0.5" />
                <p className="text-sm font-semibold text-slate-900">
                  {contractor.projects}
                </p>
                <p className="text-xs text-slate-500">проектов</p>
              </div>
              <div className="bg-slate-50 rounded-lg py-2 px-1">
                <Clock className="w-4 h-4 text-slate-400 mx-auto mb-0.5" />
                <p className="text-sm font-semibold text-slate-900">
                  {contractor.experience}
                </p>
                <p className="text-xs text-slate-500">опыт</p>
              </div>
              <div className="bg-slate-50 rounded-lg py-2 px-1">
                <Shield className="w-4 h-4 text-slate-400 mx-auto mb-0.5" />
                <p className="text-sm font-semibold text-slate-900">
                  {contractor.guarantee}
                </p>
                <p className="text-xs text-slate-500">гарантия</p>
              </div>
            </div>

            <p className="text-sm text-slate-600 mb-3">
              {contractor.priceRange}
            </p>

            {contractor.recommended > 0 && (
              <div className="flex items-center gap-1.5 mb-3 text-sm text-rose-500">
                <Heart className="w-4 h-4 fill-rose-500" />
                <span className="font-medium">
                  Советуют: {contractor.recommended}
                </span>
              </div>
            )}

            {contractor.badges.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {contractor.badges.map((badge) => (
                  <span
                    key={badge}
                    className="px-2 py-0.5 rounded-full bg-frame-50 text-frame-700 text-xs font-medium"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            )}

            <Link
              to={`/contractors/${contractor.id}`}
              className="block w-full text-center px-4 py-2 rounded-lg bg-frame-600 text-white text-sm font-medium hover:bg-frame-700 transition-colors"
            >
              Подробнее
            </Link>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16">
          <p className="text-slate-400 text-sm">
            Подрядчики не найдены. Попробуйте изменить фильтры.
          </p>
        </div>
      )}
    </div>
  );
}
