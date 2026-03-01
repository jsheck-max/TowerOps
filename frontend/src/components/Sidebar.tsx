import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, Clock, Settings, LogOut } from 'lucide-react';
import { api } from '../api/client';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/time', icon: Clock, label: 'Time Entries' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  const handleLogout = () => {
    api.clearToken();
    window.location.href = '/login';
  };

  return (
    <aside className="w-64 bg-brand-900 text-white flex flex-col min-h-screen">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <h1 className="text-xl font-bold tracking-tight">
          <span className="text-blue-400">Tower</span>Ops
        </h1>
        <p className="text-xs text-gray-400 mt-1">Job Cost Intelligence</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-gray-300 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 hover:bg-white/10 hover:text-white w-full transition-colors"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
