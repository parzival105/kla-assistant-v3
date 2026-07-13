import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import KpiCard from '@/components/ui/KpiCard'
import DataTable from '@/components/ui/DataTable'
import { HealthScoreBar } from '@/components/charts/InventoryCharts'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { branchApi } from '@/lib/api'
import { formatRupiahShort, formatNumber } from '@/lib/format'

function HealthGauge({ score }: { score: number }) {
  const color = score>=80?'#059669':score>=60?'#7c3aed':score>=40?'#d97706':'#dc2626'
  const label = score>=80?'Sangat Sehat':score>=60?'Sehat':score>=40?'Perlu Perhatian':'Bermasalah'
  const pct   = Math.min(100, score)
  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={160} height={90} viewBox="0 0 160 90">
        <path d="M20 80 A60 60 0 0 1 140 80" fill="none" stroke="#2d1a45" strokeWidth="14" strokeLinecap="round"/>
        <path d="M20 80 A60 60 0 0 1 140 80" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
              strokeDasharray={`${(pct/100)*188} 188`}/>
        <text x="80" y="75" textAnchor="middle" fill="#f1f5f9" fontSize="22" fontWeight="700" fontFamily="monospace">{score}</text>
      </svg>
      <span className="text-sm font-semibold" style={{color}}>{label}</span>
    </div>
  )
}

export default function BranchPage() {
  const [selected, setSelected] = useState<string|null>(null)
  const { data, isLoading } = useQuery({ queryKey:['branch-summary'], queryFn:()=>branchApi.summary() })
  const branches = data?.data?.branches ?? []
  const detailQ  = useQuery({ queryKey:['branch-detail', selected], queryFn:()=>branchApi.detail(selected!), enabled:!!selected })

  const best  = [...branches].sort((a:any,b:any)=>b.health_score-a.health_score)[0]
  const worst = [...branches].sort((a:any,b:any)=>a.health_score-b.health_score)[0]

  const prodCols = [
    { key:'nama_barang',    label:'Nama Barang', render:(v:any)=><span className="font-medium text-dark-50">{v}</span> },
    { key:'kategori',       label:'Kategori' },
    { key:'stok_cabang',    label:'Stok',      align:'right' as const, render:(v:any)=><span className="font-mono">{formatNumber(v)}</span> },
    { key:'runrate_cabang', label:'Runrate/Bln',align:'right' as const, render:(v:any)=><span className="font-mono">{Number(v).toFixed(1)}</span> },
    { key:'stock_day_cabang',label:'Stock Day', align:'right' as const, render:(v:any)=>{
      const d=Number(v); const c=d<30?'text-red-400':d<60?'text-amber-400':'text-emerald-400'
      return <span className={`font-mono ${c}`}>{d>=999?'999+':Math.round(d)}</span>
    }},
    { key:'status', label:'Status', render:(v:any)=>{
      const c: Record<string,string>={Critical:'text-red-400',Understock:'text-amber-400',Normal:'text-emerald-400',Overstock:'text-violet-400'}
      return <span className={`font-semibold text-sm ${c[v]??'text-dark-200'}`}>{v}</span>
    }},
  ]

  return (
    <Layout title="🏢 Branch Intelligence">
      {isLoading ? <PageLoading/> : branches.length===0 ? <NoData message="Data per-cabang tidak tersedia di file stok."/> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <KpiCard label="Cabang Paling Sehat" value={best?.branch??'—'} sub={`Score ${best?.health_score?.toFixed(0)}/100`} color="green"/>
            <KpiCard label="Cabang Bermasalah"   value={worst?.branch??'—'} sub={`Score ${worst?.health_score?.toFixed(0)}/100`} color="red"/>
            <KpiCard label="Rata-rata Score"      value={`${(branches.reduce((s:number,b:any)=>s+b.health_score,0)/branches.length).toFixed(0)}/100`} sub={`${branches.length} cabang`} color="blue"/>
            <KpiCard label="Total SKU Critical"   value={formatNumber(branches.reduce((s:number,b:any)=>s+b.critical_count,0))} sub="Stok < 30 hari" color="orange"/>
          </div>

          <div className="card mb-6">
            <h3 className="text-dark-100 font-semibold mb-4">🏆 Ranking Health Score</h3>
            <HealthScoreBar data={branches}/>
          </div>

          <div className="card mb-6">
            <h3 className="text-dark-100 font-semibold mb-4">📋 Detail Semua Cabang</h3>
            <DataTable columns={[
              { key:'rank',           label:'#',    align:'center' as const, render:(v:any)=><span className="font-mono font-bold text-brand-400">#{v}</span> },
              { key:'branch',         label:'Kode', render:(v:any)=><span className="font-mono font-semibold text-dark-50">{v}</span> },
              { key:'branch_name',    label:'Cabang' },
              { key:'area',           label:'Area', render:(v:any)=><span className="text-dark-300 text-xs">{v}</span> },
              { key:'health_score',   label:'Score', align:'right' as const, render:(v:any)=>{
                const c=Number(v); const col=c>=80?'#059669':c>=60?'#7c3aed':c>=40?'#d97706':'#dc2626'
                return <span className="font-mono font-bold" style={{color:col}}>{c.toFixed(0)}</span>
              }},
              { key:'inventory_value',label:'Nilai Inv.', align:'right' as const, render:(v:any)=><span className="font-mono text-sm">{formatRupiahShort(v)}</span> },
              { key:'dead_stock_value',label:'Dead Stock', align:'right' as const, render:(v:any)=><span className="font-mono text-sm text-red-400">{formatRupiahShort(v)}</span> },
              { key:'critical_count', label:'Critical', align:'center' as const, render:(v:any)=>(
                <span className={`font-mono font-bold ${Number(v)>0?'text-red-400':'text-dark-400'}`}>{v}</span>
              )},
              { key:'branch', label:'Detail', sortable:false, render:(_:any,row:any)=>(
                <button onClick={()=>setSelected(selected===row.branch?null:row.branch)}
                  className={`text-xs px-3 py-1 rounded-lg transition-all ${selected===row.branch?'bg-brand-700 text-white':'bg-dark-600 text-dark-200 hover:bg-dark-500'}`}>
                  {selected===row.branch?'Tutup':'Lihat'}
                </button>
              )},
            ]} data={branches}/>
          </div>

          {/* Branch drill-down */}
          {selected && (
            <div className="card">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-4">
                  <HealthGauge score={branches.find((b:any)=>b.branch===selected)?.health_score??0}/>
                  <div>
                    <h3 className="text-dark-50 font-bold text-lg">{detailQ.data?.data?.branch_name} ({selected})</h3>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-1 mt-2 text-sm">
                      {[
                        ['Total SKU', formatNumber(detailQ.data?.data?.summary?.total_sku??0)],
                        ['Inventory', formatRupiahShort(detailQ.data?.data?.summary?.inventory_value??0)],
                        ['Overstock',  formatNumber(detailQ.data?.data?.summary?.overstock_count??0)],
                        ['Critical',   formatNumber(detailQ.data?.data?.summary?.critical_count??0)],
                      ].map(([l,v])=>(
                        <div key={l} className="flex gap-2">
                          <span className="text-dark-300">{l}:</span>
                          <span className="text-dark-100 font-mono font-semibold">{v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              {detailQ.isLoading ? <PageLoading/> : (
                <DataTable columns={prodCols} data={detailQ.data?.data?.products??[]}/>
              )}
            </div>
          )}
        </>
      )}
    </Layout>
  )
}
