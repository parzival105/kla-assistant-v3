import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import DataTable from '@/components/ui/DataTable'
import { CategoryBadge } from '@/components/ui/Badge'
import { PageLoading, NoData } from '@/components/ui/Loading'
import KpiCard from '@/components/ui/KpiCard'
import { inventoryApi } from '@/lib/api'
import { formatRupiahShort, formatNumber } from '@/lib/format'
import { Search } from 'lucide-react'

export default function InventoryPage() {
  const [search, setSearch] = useState('')
  const [kategori, setKategori] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['products', search, kategori, page],
    queryFn: () => inventoryApi.products({ search, kategori: kategori||undefined, page, per_page: 50 }),
  })

  const summaryQ = useQuery({ queryKey:['inv-summary'], queryFn: () => inventoryApi.summary() })
  const s = summaryQ.data?.data?.revenue_summary

  const products = data?.data?.products ?? []
  const total    = data?.data?.total ?? 0
  const filters  = data?.data?.filters ?? {}

  const columns = [
    { key:'nama_barang', label:'Nama Barang', render:(v:any)=><span className="font-medium text-dark-50">{v}</span> },
    { key:'kategori',   label:'Kategori', render:(v:any)=><CategoryBadge category={v}/> },
    { key:'segment',    label:'Segment', render:(v:any)=><span className="text-dark-300 text-xs">{v||'—'}</span> },
    { key:'runrate_bulanan', label:'Runrate/Bln', align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{Number(v).toFixed(1)}</span> },
    { key:'total_stok',      label:'Total Stok', align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{formatNumber(v)}</span> },
    { key:'min_stock',       label:'Min Stock',  align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{formatNumber(v)}</span> },
    { key:'stock_day',       label:'Stock Day',  align:'right' as const, render:(v:any)=>{
      const d = Number(v)
      const color = d < 30 ? 'text-red-400' : d < 60 ? 'text-amber-400' : 'text-emerald-400'
      return <span className={`font-mono text-sm ${color}`}>{d >= 999 ? '999+' : Math.round(d)}</span>
    }},
    { key:'qty_restock', label:'Qty Restock', align:'right' as const, render:(v:any)=>(
      v > 0 ? <span className="font-mono text-sm text-red-400">{formatNumber(v)}</span> : <span className="text-dark-400">—</span>
    )},
    { key:'h1', label:'Harga H1', align:'right' as const, render:(v:any)=><span className="font-mono text-sm text-brand-300">{formatRupiahShort(v)}</span> },
  ]

  return (
    <Layout title="📦 Inventory Analysis">
      {s && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiCard label="Total SKU" value={formatNumber(s.total_sku)} color="purple"/>
          <KpiCard label="Fast Moving" value={formatNumber(s.fast_sku)} sub="Very Fast + Fast" color="green"/>
          <KpiCard label="Dead Stock" value={formatNumber(s.dead_sku)} color="red"/>
          <KpiCard label="Nilai Inventory" value={formatRupiahShort(s.inventory_value)} color="blue"/>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-4">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-48">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-300"/>
            <input className="input pl-9" placeholder="Cari nama barang..." value={search}
              onChange={e=>{ setSearch(e.target.value); setPage(1) }}/>
          </div>
          <select className="input w-44" value={kategori} onChange={e=>{ setKategori(e.target.value); setPage(1) }}>
            <option value="">Semua Kategori</option>
            {['Very Fast','Fast','Slow','Dead Stock'].map(k=><option key={k} value={k}>{k}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? <PageLoading/> : products.length === 0 ? <NoData/> : (
        <>
          <div className="text-dark-300 text-sm mb-3">Menampilkan {products.length} dari {total.toLocaleString()} produk</div>
          <DataTable columns={columns} data={products}/>
          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <button className="btn-secondary text-sm" onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page===1}>← Sebelumnya</button>
            <span className="text-dark-300 text-sm">Hal. {page} dari {Math.ceil(total/50)}</span>
            <button className="btn-secondary text-sm" onClick={()=>setPage(p=>p+1)} disabled={page*50>=total}>Selanjutnya →</button>
          </div>
        </>
      )}
    </Layout>
  )
}
