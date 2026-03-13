import { type ReactNode } from 'react'
import { cn } from '../../utils/cn'

interface Tab {
  id: string
  label: string
  icon?: ReactNode
}

interface ReportTabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (tabId: string) => void
}

export function ReportTabs({ tabs, activeTab, onChange }: ReportTabsProps) {
  return (
    <div className="border-b border-slate-700 mb-6">
      <nav className="-mb-px flex gap-1 overflow-x-auto" aria-label="Report sections">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              'flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-150',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:border-slate-600 hover:text-slate-300'
            )}
            aria-selected={activeTab === tab.id}
            role="tab"
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  )
}
