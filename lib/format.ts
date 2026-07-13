/**
 * lib/format.ts — Number and currency formatters
 */
export const formatRupiah = (value: number): string => {
  if (!value && value !== 0) return 'Rp 0'
  return `Rp ${Math.round(value).toLocaleString('id-ID')}`
}

export const formatRupiahShort = (value: number): string => {
  if (!value && value !== 0) return 'Rp 0'
  const abs = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  if (abs >= 1_000_000_000) return `${sign}Rp ${(abs / 1_000_000_000).toFixed(2)}M`
  if (abs >= 1_000_000)     return `${sign}Rp ${(abs / 1_000_000).toFixed(1)}Jt`
  if (abs >= 1_000)         return `${sign}Rp ${(abs / 1_000).toFixed(0)}Rb`
  return `${sign}Rp ${abs.toLocaleString('id-ID')}`
}

export const formatNumber = (value: number, decimals = 0): string =>
  value?.toLocaleString('id-ID', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) ?? '0'

export const formatPercent = (value: number, decimals = 1): string =>
  `${(value ?? 0).toFixed(decimals)}%`

export const getCategoryClass = (cat: string): string => {
  const map: Record<string, string> = {
    'Very Fast': 'badge-vf',
    'Fast':      'badge-fast',
    'Slow':      'badge-slow',
    'Dead Stock':'badge-dead',
  }
  return map[cat] ?? 'badge-slow'
}

export const getCategoryColor = (cat: string): string => {
  const map: Record<string, string> = {
    'Very Fast': '#059669',
    'Fast':      '#7c3aed',
    'Slow':      '#d97706',
    'Dead Stock':'#dc2626',
  }
  return map[cat] ?? '#94a3b8'
}

export const getStockStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    'Overstock':  '#8b5cf6',
    'Normal':     '#059669',
    'Understock': '#d97706',
    'Critical':   '#dc2626',
  }
  return map[status] ?? '#94a3b8'
}
