import { getCategoryClass } from '@/lib/format'
import clsx from 'clsx'

export function CategoryBadge({ category }: { category: string }) {
  return <span className={getCategoryClass(category)}>{category}</span>
}

export function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    Overstock:  'bg-violet-900/40 text-violet-400 border-violet-700/40',
    Normal:     'bg-emerald-900/40 text-emerald-400 border-emerald-700/40',
    Understock: 'bg-amber-900/40 text-amber-400 border-amber-700/40',
    Critical:   'bg-red-900/40 text-red-400 border-red-700/40',
  }
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border',
      cls[status] ?? 'bg-dark-600 text-dark-200 border-dark-500'
    )}>{status}</span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  const cls: Record<string, string> = {
    'Priority A': 'bg-emerald-900/40 text-emerald-400 border-emerald-700/40',
    'Priority B': 'bg-amber-900/40 text-amber-400 border-amber-700/40',
    'Priority C': 'bg-red-900/40 text-red-400 border-red-700/40',
  }
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border',
      cls[priority] ?? 'bg-dark-600 text-dark-200 border-dark-500'
    )}>{priority}</span>
  )
}

export function RoleBadge({ role, label }: { role: string; label: string }) {
  const cls: Record<string, string> = {
    super_admin:  'bg-brand-900/40 text-brand-400 border-brand-700/40',
    area_manager: 'bg-blue-900/40 text-blue-400 border-blue-700/40',
    store_leader: 'bg-emerald-900/40 text-emerald-400 border-emerald-700/40',
    sales:        'bg-amber-900/40 text-amber-400 border-amber-700/40',
  }
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border',
      cls[role] ?? 'bg-dark-600 text-dark-200 border-dark-500'
    )}>{label}</span>
  )
}
