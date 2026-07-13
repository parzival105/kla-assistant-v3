import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, LineChart, Line, CartesianGrid
} from 'recharts'
import { formatRupiahShort } from '@/lib/format'

const DARK_TOOLTIP = {
  contentStyle: { background: '#180d28', border: '1px solid #2d1a45', borderRadius: 8, color: '#c4b5d4' },
  labelStyle: { color: '#e2e8f0', fontWeight: 600 },
}

// Donut chart for category distribution
export function CategoryDonut({ data }: { data: { name: string; value: number; color: string }[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%"
             innerRadius={70} outerRadius={110} paddingAngle={3}>
          {data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
        </Pie>
        <Tooltip {...DARK_TOOLTIP} formatter={(v: any) => [v.toLocaleString('id-ID'), 'SKU']} />
        <Legend formatter={(v) => <span className="text-dark-200 text-xs">{v}</span>} />
      </PieChart>
    </ResponsiveContainer>
  )
}

// Horizontal bar for category values
export function CategoryValueBar({ data }: { data: { name: string; value: number; color: string }[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical" margin={{ left: 20, right: 60, top: 10, bottom: 10 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={80}
               tick={{ fill: '#9d7fba', fontSize: 12 }} />
        <Tooltip {...DARK_TOOLTIP} formatter={(v: any) => [formatRupiahShort(v), 'Nilai']} />
        <Bar dataKey="value" radius={[0,6,6,0]}>
          {data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// Health score ranking bar
export function HealthScoreBar({ data }: { data: { branch: string; health_score: number }[] }) {
  const getColor = (score: number) =>
    score >= 80 ? '#059669' : score >= 60 ? '#7c3aed' : score >= 40 ? '#d97706' : '#dc2626'

  return (
    <ResponsiveContainer width="100%" height={Math.max(300, data.length * 36)}>
      <BarChart data={[...data].sort((a,b) => a.health_score - b.health_score)}
                layout="vertical" margin={{ left: 20, right: 60, top: 10, bottom: 10 }}>
        <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b4f8a', fontSize: 11 }} />
        <YAxis type="category" dataKey="branch" width={50} tick={{ fill: '#9d7fba', fontSize: 12 }} />
        <Tooltip {...DARK_TOOLTIP} formatter={(v: any) => [`${Number(v).toFixed(1)}/100`, 'Health Score']} />
        <Bar dataKey="health_score" radius={[0,6,6,0]}>
          {[...data].sort((a,b) => a.health_score - b.health_score)
            .map((entry, i) => <Cell key={i} fill={getColor(entry.health_score)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// Waterfall-style bar for revenue
export function RevenueWaterfall({ data }: { data: { name: string; value: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={data} margin={{ top: 20, right: 20, bottom: 60, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d1a45" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: '#9d7fba', fontSize: 11 }}
               angle={-30} textAnchor="end" height={60} />
        <YAxis tickFormatter={formatRupiahShort} tick={{ fill: '#6b4f8a', fontSize: 11 }} />
        <Tooltip {...DARK_TOOLTIP} formatter={(v: any) => [formatRupiahShort(Math.abs(v)), '']} />
        <Bar dataKey="value" radius={[6,6,0,0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.value >= 0 ? '#7c3aed' : '#dc2626'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
