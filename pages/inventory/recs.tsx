import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import KpiCard from '@/components/ui/KpiCard'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi } from '@/lib/api'
import { formatNumber } from '@/lib/format'

const PRIORITY_ORDER: Record<string,number> = { Tinggi:0, Sedang:1, Rendah:2 }
const PRIORITY_CLASS: Record<string,string> = { Tinggi:'tinggi', Sedang:'sedang', Rendah:'rendah' }

export default function RecsPage() {
  const { data, isLoading } = useQuery({ queryKey:['recs'], queryFn:()=>inventoryApi.recommendations() })
  const recs = data?.data?.recommendations ?? []
  const [selCats, setSelCats] = useState<string[]>([])
  const [selPrios, setSelPrios] = useState<string[]>([])

  const allCats  = [...new Set(recs.map((r:any) => r.category))].sort()
  const allPrios = ['Tinggi','Sedang','Rendah']

  const filtered = recs
    .filter((r:any) => (selCats.length===0 || selCats.includes(r.category)) && (selPrios.length===0 || selPrios.includes(r.priority)))
    .sort((a:any,b:any) => (PRIORITY_ORDER[a.priority]??3)-(PRIORITY_ORDER[b.priority]??3))

  const nHigh = recs.filter((r:any)=>r.priority==='Tinggi').length
  const nMed  = recs.filter((r:any)=>r.priority==='Sedang').length

  return (
    <Layout title="🤖 AI Recommendation">
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Rekomendasi" value={formatNumber(recs.length)}  color="blue"/>
        <KpiCard label="Prioritas Tinggi"  value={formatNumber(nHigh)} sub="Tindakan segera" color="red"/>
        <KpiCard label="Prioritas Sedang"  value={formatNumber(nMed)}  sub="Perlu ditindaklanjuti" color="orange"/>
        <KpiCard label="Area Bisnis"       value={formatNumber(allCats.length)} color="purple"/>
      </div>

      <div className="card mb-4 flex flex-wrap gap-3">
        <div>
          <p className="text-dark-300 text-xs font-medium mb-2">Filter Kategori:</p>
          <div className="flex flex-wrap gap-1.5">
            {allCats.map(cat => (
              <button key={cat} onClick={()=>setSelCats(p=>p.includes(cat)?p.filter(c=>c!==cat):[...p,cat])}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${selCats.includes(cat)?'bg-brand-700 text-white':'bg-dark-600 text-dark-200 hover:bg-dark-500'}`}>{cat}</button>
            ))}
          </div>
        </div>
        <div>
          <p className="text-dark-300 text-xs font-medium mb-2">Filter Prioritas:</p>
          <div className="flex gap-1.5">
            {allPrios.map(p=>(
              <button key={p} onClick={()=>setSelPrios(prev=>prev.includes(p)?prev.filter(x=>x!==p):[...prev,p])}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${selPrios.includes(p)?'bg-brand-700 text-white':'bg-dark-600 text-dark-200 hover:bg-dark-500'}`}>{p}</button>
            ))}
          </div>
        </div>
      </div>

      <p className="text-dark-300 text-sm mb-3">Menampilkan {filtered.length} dari {recs.length} rekomendasi</p>

      {isLoading ? <PageLoading/> : filtered.length === 0 ? <NoData message="Tidak ada data. Upload file stok terlebih dahulu."/> : (
        <div className="space-y-2">
          {filtered.map((rec:any, i:number) => (
            <div key={i} className={`rec-card ${PRIORITY_CLASS[rec.priority]??'rendah'}`}>
              <div className="flex items-center gap-2 mb-1">
                <span>{rec.icon}</span>
                <span className="text-dark-300 text-xs font-semibold uppercase tracking-wider">[{rec.category}]</span>
                <span className={`text-xs font-bold ${rec.priority==='Tinggi'?'text-red-400':rec.priority==='Sedang'?'text-amber-400':'text-dark-400'}`}>{rec.priority}</span>
              </div>
              <p className="text-dark-100 text-sm leading-relaxed">{rec.text}</p>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
