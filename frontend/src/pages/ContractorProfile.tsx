import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Star,
  Heart,
  Briefcase,
  Clock,
  Shield,
  MessageSquare,
  FileText,
} from "lucide-react";
import { contractors } from "../data/mock";

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

const portfolioColors = [
  "bg-gradient-to-br from-slate-200 to-slate-300",
  "bg-gradient-to-br from-blue-100 to-blue-200",
  "bg-gradient-to-br from-amber-100 to-amber-200",
  "bg-gradient-to-br from-emerald-100 to-emerald-200",
  "bg-gradient-to-br from-violet-100 to-violet-200",
];

function getAvatarColor(letter: string) {
  return avatarColors[letter] || "bg-slate-500";
}

export default function ContractorProfile() {
  const { id } = useParams<{ id: string }>();
  const contractor = contractors.find((c) => c.id === id);

  if (!contractor) {
    return (
      <div className="max-w-4xl mx-auto text-center py-20">
        <p className="text-slate-400 text-lg mb-4">Подрядчик не найден</p>
        <Link
          to="/contractors"
          className="text-frame-600 hover:text-frame-700 text-sm font-medium"
        >
          Вернуться к списку
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Link
        to="/contractors"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Все подрядчики
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 mb-6">
        <div className="flex items-start gap-5">
          <div
            className={`w-20 h-20 rounded-full ${getAvatarColor(contractor.avatar[0])} flex items-center justify-center text-white font-bold text-xl shrink-0`}
          >
            {contractor.avatar}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold text-slate-900">
                {contractor.name}
              </h1>
              {contractor.verified && (
                <CheckCircle2 className="w-6 h-6 text-blue-500 fill-blue-500 stroke-white shrink-0" />
              )}
            </div>
            <span className="inline-block px-3 py-1 rounded-md bg-slate-100 text-sm font-medium text-slate-600">
              {contractor.specialization}
            </span>

            <div className="flex items-center gap-1 mt-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`w-5 h-5 ${
                    i < Math.round(contractor.rating)
                      ? "text-amber-400 fill-amber-400"
                      : "text-slate-200 fill-slate-200"
                  }`}
                />
              ))}
              <span className="ml-1 text-lg font-semibold text-slate-900">
                {contractor.rating}
              </span>
            </div>
          </div>
          <div className="flex gap-3 shrink-0">
            <button className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
              <MessageSquare className="w-4 h-4" />
              Написать
            </button>
            <button className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-frame-600 text-white text-sm font-medium hover:bg-frame-700 transition-colors">
              <FileText className="w-4 h-4" />
              Запросить смету
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-center">
          <Star className="w-5 h-5 text-amber-400 fill-amber-400 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {contractor.rating}
          </p>
          <p className="text-xs text-slate-500">Рейтинг</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-center">
          <MessageSquare className="w-5 h-5 text-slate-400 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {contractor.reviews}
          </p>
          <p className="text-xs text-slate-500">Отзывов</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-center">
          <Briefcase className="w-5 h-5 text-slate-400 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {contractor.projects}
          </p>
          <p className="text-xs text-slate-500">Проектов</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-center">
          <Clock className="w-5 h-5 text-slate-400 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {contractor.experience}
          </p>
          <p className="text-xs text-slate-500">Опыт</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-center">
          <Shield className="w-5 h-5 text-slate-400 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {contractor.guarantee}
          </p>
          <p className="text-xs text-slate-500">Гарантия</p>
        </div>
      </div>

      {contractor.recommended > 0 && (
        <div className="bg-rose-50 border border-rose-100 rounded-xl p-5 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
              <Heart className="w-5 h-5 text-rose-500 fill-rose-500" />
            </div>
            <div>
              <p className="text-base font-semibold text-slate-900">
                {contractor.recommended} человек из ваших контактов советуют
                этого мастера
              </p>
              <p className="text-sm text-slate-500 mt-0.5">
                Рекомендации от людей, которым вы доверяете
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3">
          О мастере
        </h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          {contractor.description}
        </p>
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="text-sm text-slate-500">
            <span className="font-medium text-slate-700">Цены:</span>{" "}
            {contractor.priceRange}
          </p>
        </div>
      </div>

      {contractor.portfolio.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 mb-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Портфолио
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {contractor.portfolio.map((item, index) => (
              <div key={index} className="group cursor-pointer">
                <div
                  className={`aspect-[4/3] rounded-lg ${portfolioColors[index % portfolioColors.length]} flex items-center justify-center mb-2 group-hover:opacity-80 transition-opacity`}
                >
                  <span className="text-xs text-slate-400 font-medium">
                    Фото проекта
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-700">
                  {item.title}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {contractor.badges.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 mb-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-3">
            Достижения
          </h2>
          <div className="flex flex-wrap gap-2">
            {contractor.badges.map((badge) => (
              <span
                key={badge}
                className="px-3 py-1.5 rounded-full bg-frame-50 text-frame-700 text-sm font-medium border border-frame-100"
              >
                {badge}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
