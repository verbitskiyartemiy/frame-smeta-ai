import { NavLink, Link } from "react-router-dom";
import {
  LayoutDashboard,
  Hammer,
  Users,
  Calculator,
  MessageSquare,
  FileText,
  Home,
  Bot,
  Plus,
  Users2,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Главная", icon: LayoutDashboard },
  { to: "/project/1", label: "Мой проект", icon: Hammer },
  { to: "/contractors", label: "Подрядчики", icon: Users },
  { to: "/estimates", label: "Сметы", icon: Calculator },
  { to: "/messages", label: "Сообщения", icon: MessageSquare },
  { to: "/documents", label: "Документы", icon: FileText },
  { to: "/home-hub", label: "Home Hub", icon: Home },
  { to: "/community", label: "Сообщество", icon: Users2 },
  { to: "/ai", label: "AI-контроль", icon: Bot },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0">
      <div className="px-6 py-5 flex items-center gap-2.5">
        <div className="w-8 h-8 bg-frame-600 rounded-lg" />
        <span className="text-xl font-bold text-slate-900 tracking-tight">
          ФРЕЙМ
        </span>
      </div>

      <div className="px-3 pb-2">
        <Link
          to="/project/new"
          className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium bg-frame-600 text-white hover:bg-frame-700 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Создать проект
        </Link>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-frame-50 text-frame-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            <Icon className="w-5 h-5 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-frame-600 flex items-center justify-center text-white text-sm font-semibold shrink-0">
            АВ
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">
              Анна Вербицкая
            </p>
            <p className="text-xs text-slate-500">Заказчик</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
