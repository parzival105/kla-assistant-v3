interface KpiCardProps {
  label: string
  value: string
  sub?: string
  color?: 'purple' | 'blue' | 'green' | 'orange' | 'red'
  icon?: React.ReactNode
}

export default function KpiCard({ label, value, sub, color = 'purple', icon }: KpiCardProps) {
  return (
    <div className={`kpi-card ${color}`}>
      <div className="flex items-start justify-between">
        <div className="text-dark-300 text-xs font-bold uppercase tracking-widest mb-3">{label}</div>
        {icon && <div className="text-dark-300 opacity-60">{icon}</div>}
      </div>
      <div className="font-mono text-2xl font-bold text-dark-50 leading-none">{value}</div>
      {sub && <div className="text-dark-300 text-xs mt-2">{sub}</div>}
    </div>
  )
}
