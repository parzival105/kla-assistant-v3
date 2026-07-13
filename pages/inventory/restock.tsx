import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import DataTable from '@/components/ui/DataTable'
import KpiCard from '@/components/ui/KpiCard'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi } from '@/lib/api'
import { formatRupiahShort, formatNumber } from '@/lib/format'

export default function RestockPage() {
  const { data, isLoading } = useQuery({ queryKey:['restock'], queryFn:()=>inventoryApi.restock() })
  const items   = data?.data?.items ?? []
  const summary = data?.data?.summary ?? {}

  const columns = [
    { key:'prioritas',    label:'#', align:'center' as const, render:(v:any)=><span className="font-mono font-bold text-brand-400">#{v}</span> },
    { key:'nama_barang',  label:'Nama Barang', render:(v:any)=><span className="font-medium text-dark-50">{v}</span> },
    { key:'kategori',     label:'Kategori' },
    { key:'runrate_bulanan', label:'Runrate/Bln', align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{Number(v).toFixed(1)}</span> },
    { key:'total_stok',   label:'Stok',      align:'right' as const, render:(v:any)=><span className="font-mono">{formatNumber(v)}</span> },
    { key:'min_stock',    label:'Min Stock',  align:'right' as const, render:(v:any)=><span className="font-mono">{formatNumber(v)}</span> },
    { key:'qty_restock',  label:'Qty Restock',align:'right' as const, render:(v:any)=><span className="font-mono text-red-400 font-semibold">{formatNumber(v)}</span> },
    { key:'nilai_restock',label:'Nilai',      align:'right' as const, render:(v:any)=><span className="font-mono text-brand-300">{formatRupiahShort(v)}</span> },
  ]

  return (
    <Layout title="🛒 Restock Engine">
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard label="SKU Perlu Restock" value={formatNumber(summary.sku_count)}  sub="Di bawah minimum stok" color="orange"/>
        <KpiCard label="Total Qty"          value={formatNumber(summary.total_qty)}  sub="Unit dibutuhkan" color="blue"/>
        <KpiCard label="Est. Nilai Pembelian" value={formatRupiahShort(summary.total_value)} sub="Modal diperlukan" color="red"/>
      </div>
      {isLoading ? <PageLoading/> : items.length === 0 ? <NoData message="Semua SKU memenuhi minimum stok."/> : <DataTable columns={columns} data={items}/>}
    </Layout>
  )
}
