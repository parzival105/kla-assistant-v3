import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'

interface Column {
  key: string
  label: string
  render?: (value: any, row: any) => React.ReactNode
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
}

interface DataTableProps {
  columns: Column[]
  data: any[]
  maxHeight?: string
}

export default function DataTable({ columns, data, maxHeight = '480px' }: DataTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const sorted = [...data].sort((a, b) => {
    if (!sortKey) return 0
    const av = a[sortKey], bv = b[sortKey]
    if (av === bv) return 0
    const cmp = av < bv ? -1 : 1
    return sortDir === 'asc' ? cmp : -cmp
  })

  return (
    <div className="overflow-auto rounded-xl border border-dark-500" style={{ maxHeight }}>
      <table className="w-full text-sm text-left">
        <thead className="sticky top-0 bg-dark-700 border-b border-dark-500 z-10">
          <tr>
            {columns.map(col => (
              <th
                key={col.key}
                onClick={() => col.sortable !== false && handleSort(col.key)}
                className={`px-4 py-3 text-dark-200 font-semibold uppercase tracking-wider text-xs
                  ${col.sortable !== false ? 'cursor-pointer hover:text-brand-400 select-none' : ''}
                  ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}`}
              >
                <span className="flex items-center gap-1 whitespace-nowrap">
                  {col.label}
                  {col.sortable !== false && sortKey === col.key && (
                    sortDir === 'asc' ? <ChevronUp size={12}/> : <ChevronDown size={12}/>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={i} className="border-b border-dark-600 hover:bg-dark-700/50 transition-colors">
              {columns.map(col => (
                <td
                  key={col.key}
                  className={`px-4 py-3 text-dark-100
                    ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}`}
                >
                  {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr><td colSpan={columns.length} className="text-center py-12 text-dark-300">Tidak ada data</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
