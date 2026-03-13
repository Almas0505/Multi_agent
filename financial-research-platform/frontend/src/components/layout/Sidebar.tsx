import { NavLink } from 'react-router-dom'
import { BarChart2, FileText, Home, TrendingUp, X } from 'lucide-react'
import { cn } from '../../utils/cn'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/analysis', label: 'New Analysis', icon: TrendingUp, end: false },
  { to: '/reports', label: 'Reports', icon: FileText, end: false },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-900 border-r border-slate-700/50 transition-transform duration-300 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-6 border-b border-slate-700/50">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <BarChart2 className="h-5 w-5 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-100 leading-tight">
              Financial<br />Research
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-200 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150',
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-700/50">
          <p className="text-xs text-slate-600">Financial Research Platform</p>
          <p className="text-xs text-slate-700">v1.0.0</p>
        </div>
      </aside>
    </>
  )
}
