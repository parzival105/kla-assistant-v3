import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import DataTable from '@/components/ui/DataTable'
import KpiCard from '@/components/ui/KpiCard'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi } from '@/lib/api'
import { formatRupiahShort, formatNumber } from '@/lib/format'

export default function TransferPage() {
  const { data, isLoading } = useQuery({ queryKey:['transfer'], queryFn:()=>inventoryApi.transfer() })
  const items   = data?.data?.items ?? []
  const summary = data?.data?.summary ?? {}

  const columns = [
    { key:'nama_barang',  label:'Nama Barang', render:(v:any)=><span className="font-medium text-dark-50">{v}</span> },
    { key:'area',         label:'Area' },
    { key:'dari_cabang',  label:'Dari', render:(v:any)=><span className="text-amber-400 font-mono font-semibold">{v}</span> },
    { key:'ke_cabang',    label:'Ke',   render:(v:any)=><span className="text-emerald-400 font-mono font-semibold">{v}</span> },
    { key:'qty_transfer', label:'Qty',  align:'right' as const, render:(v:any)=><span className="font-mono">{formatNumber(v)}</span> },
    { key:'nilai_transfer',label:'Nilai', align:'right' as const, render:(v:any)=><span className="font-mono text-brand-300">{formatRupiahShort(v)}</span> },
  ]

  return (
    <Layout title="🔄 Transfer Engine">
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard label="Total Transfer" value={formatNumber(summary.total_transactions)} color="purple"/>
        <KpiCard label="Nilai Transfer"  value={formatRupiahShort(summary.total_value)} sub="Hemat vs beli baru" color="green"/>
        <KpiCard label="Area Terlibat"   value={formatNumber((summary.areas??[]).length)} color="blue"/>
      </div>
      <div className="alert-info mb-4">
        <strong>💡 Prioritaskan transfer sebelum purchase order baru.</strong> Total penghematan potensial: <strong>{formatRupiahShort(summary.total_value)}</strong>
      </div>
      {isLoading ? <PageLoading/> : items.length === 0 ? <NoData message="Tidak ada rekomendasi transfer."/> : <DataTable columns={columns} data={items}/>}
    </Layout>
  )
}
