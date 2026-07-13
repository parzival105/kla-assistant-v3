import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import DataTable from '@/components/ui/DataTable'
import { CategoryBadge } from '@/components/ui/Badge'
import KpiCard from '@/components/ui/KpiCard'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi } from '@/lib/api'
import { formatRupiahShort, formatPercent } from '@/lib/format'

export default function PricingPage() {
  const { data, isLoading } = useQuery({ queryKey:['pricing'], queryFn:()=>inventoryApi.pricing() })
  const items      = data?.data?.items ?? []
  const showMargin = data?.data?.show_margin ?? false
  const showHpp    = data?.data?.show_hpp ?? false

  const columns = [
    { key:'nama_barang',       label:'Nama Barang', render:(v:any)=><span className="font-medium text-dark-50">{v}</span> },
    { key:'kategori',          label:'Kategori',    render:(v:any)=><CategoryBadge category={v}/> },
    ...(showHpp ? [{ key:'hpp', label:'HPP', align:'right' as const, render:(v:any)=><span className="font-mono text-xs text-dark-300">{formatRupiahShort(v)}</span> }] : []),
    { key:'h1', label:'H1', align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{formatRupiahShort(v)}</span> },
    { key:'h2', label:'H2', align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{formatRupiahShort(v)}</span> },
    { key:'harga_rekomendasi', label:'Harga Rekomendasi', align:'right' as const, render:(v:any)=><span className="font-mono font-semibold text-brand-300">{formatRupiahShort(v)}</span> },
    ...(showMargin ? [{ key:'margin_persen', label:'Margin %', align:'right' as const, render:(v:any)=>{
      const pct = Number(v)
      const color = pct >= 15 ? 'text-emerald-400' : pct >= 8 ? 'text-amber-400' : 'text-red-400'
      return <span className={`font-mono font-semibold ${color}`}>{formatPercent(pct)}</span>
    }}] : []),
  ]

  return (
    <Layout title="💰 Pricing Analysis">
      <div className="grid grid-cols-4 gap-4 mb-6">
        {['Very Fast','Fast','Slow','Dead Stock'].map(cat => {
          const catItems = items.filter((i:any)=>i.kategori===cat)
          const labels: Record<string,string> = {'Very Fast':'Jual di H2','Fast':'Jual di H1','Slow':'Turunkan ke HD','Dead Stock':'Clearance'}
          const colors: Record<string,string> = {'Very Fast':'green','Fast':'purple','Slow':'orange','Dead Stock':'red'}
          return <KpiCard key={cat} label={cat} value={catItems.length.toString()} sub={labels[cat]} color={colors[cat] as any}/>
        })}
      </div>
      {isLoading ? <PageLoading/> : items.length === 0 ? <NoData/> : <DataTable columns={columns} data={items}/>}
    </Layout>
  )
}

