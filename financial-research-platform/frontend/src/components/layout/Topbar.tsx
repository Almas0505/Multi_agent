import { Menu, Bell } from 'lucide-react'
import { useLocation } from 'react-router-dom'

interface TopbarProps {
  onMenuClick: () => void
}

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/analysis': 'New Analysis',
  '/reports': 'Reports',
}

function getPageTitle(pathname: string): string {
  if (pageTitles[pathname]) return pageTitles[pathname]
  if (pathname.startsWith('/analysis/')) return 'Analysis Progress'
  if (pathname.startsWith('/reports/')) return 'Report Detail'
  return 'Financial Research Platform'
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const location = useLocation()
  const title = getPageTitle(location.pathname)

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-700/50 bg-slate-900/80 px-6 backdrop-blur-sm">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-200 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-base font-semibold text-slate-100">{title}</h1>
      </div>

      <div className="flex items-center gap-2">
        <button
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
          FR
        </div>
      </div>
    </header>
  )
}
