import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import DataTable from '@/components/ui/DataTable'
import KpiCard from '@/components/ui/KpiCard'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi } from '@/lib/api'
import { formatRupiahShort, formatNumber } from '@/lib/format'

export default function DeadStockPage() {
  const { data, isLoading } = useQuery({ queryKey:['dead-stock'], queryFn:()=>inventoryApi.deadStock() })
  const items    = data?.data?.items ?? []
  const total    = data?.data?.total_value ?? 0
  const byAction = data?.data?.by_action ?? {}

  const actionColor: Record<string,string> = {
    'Clearance':      'text-red-400',
    'Bundling':       'text-violet-400',
    'Turunkan ke HD': 'text-amber-400',
    'Monitor':        'text-blue-400',
  }

  const columns = [
    { key:'nama_barang',            label:'Nama Barang',  render:(v:any)=><span className="font-medium text-dark-50">{v}</span> },
    { key:'total_stok',             label:'Stok',         align:'right' as const, render:(v:any)=><span className="font-mono">{formatNumber(v)}</span> },
    { key:'dead_stock_value',       label:'Nilai Modal',  align:'right' as const, render:(v:any)=><span className="font-mono text-red-400">{formatRupiahShort(v)}</span> },
    { key:'estimasi_bulan_tersimpan',label:'Est. Bulan',  align:'right' as const, render:(v:any)=><span className="font-mono">{Number(v).toFixed(0)}</span> },
    { key:'rekomendasi_aksi',       label:'Aksi',         render:(v:any)=><span className={`font-semibold text-sm ${actionColor[v]??'text-dark-200'}`}>{v}</span> },
    { key:'alasan',                 label:'Alasan',       render:(v:any)=><span className="text-dark-300 text-xs">{v}</span> },
  ]

  return (
    <Layout title="☠️ Dead Stock Center">
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total SKU Dead Stock"  value={formatNumber(items.length)}               sub="Runrate < 4/bulan" color="red"/>
        <KpiCard label="Nilai Modal Tertahan"  value={formatRupiahShort(total)}                 sub="Berdasarkan HPP"   color="red"/>
        <KpiCard label="Perlu Clearance"       value={formatNumber(byAction['Clearance']?.count??0)} sub="> 12 bulan"  color="orange"/>
        <KpiCard label="Perlu Bundling"        value={formatNumber(byAction['Bundling']?.count??0)}  sub="6-12 bulan"  color="purple"/>
      </div>
      {Object.entries(byAction).length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {Object.entries(byAction).map(([action, info]: any) => (
            <div key={action} className="bg-dark-700 border border-dark-500 rounded-xl p-4">
              <div className={`font-semibold text-sm mb-1 ${actionColor[action]??'text-dark-200'}`}>{action}</div>
              <div className="font-mono text-xl text-dark-50 font-bold">{info.count}</div>
              <div className="text-dark-300 text-xs mt-1">{formatRupiahShort(info.value)}</div>
            </div>
          ))}
        </div>
      )}
      {isLoading ? <PageLoading/> : items.length === 0 ? <NoData message="Tidak ada dead stock. Inventory sehat!"/> : <DataTable columns={columns} data={items}/>}
    </Layout>
  )
}
