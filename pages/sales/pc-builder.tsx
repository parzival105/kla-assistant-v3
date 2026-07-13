import { useState } from 'react'
import Layout from '@/components/layout/Layout'
import { pcBuilderApi } from '@/lib/api'
import { formatRupiah, formatRupiahShort } from '@/lib/format'
import { Cpu, Loader2, Save, ChevronDown, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'

const BRANCH_FULL: Record<string,string> = {
  SMG:'Semarang',YK:'Yogyakarta',SLA:'Slawi',TGL:'Tegal',PKL:'Pekalongan',
  CRB:'Cirebon',KDR:'Kediri',NGL:'Ngaliyan',SKH:'Sukoharjo',
  MSBY:'Surabaya Merr',MJK:'Mojokerto',BSBY:'Surabaya Babatan',PWT:'Purwokerto'
}

const BUILD_TYPES = [
  'Office / Kerja','Gaming Entry','Gaming Mid-range','Gaming High-end',
  'Desain Grafis','Video Editing','Coding / Development','Workstation','HTPC / Media Center'
]
const BUDGET_TIERS = [
  {label:'Entry (Rp 3-5 juta)',min:3_000_000,max:5_000_000},
  {label:'Mid-Low (Rp 5-8 juta)',min:5_000_000,max:8_000_000},
  {label:'Mid (Rp 8-12 juta)',min:8_000_000,max:12_000_000},
  {label:'Mid-High (Rp 12-18 juta)',min:12_000_000,max:18_000_000},
  {label:'High (Rp 18-25 juta)',min:18_000_000,max:25_000_000},
  {label:'Premium (Rp 25-35 juta)',min:25_000_000,max:35_000_000},
]

function BranchStock({ bs }: { bs: Record<string,number> }) {
  if (!bs || Object.keys(bs).length === 0)
    return <span className="text-red-400 text-xs italic">Stok kosong semua cabang</span>
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {Object.entries(bs).sort((a,b)=>b[1]-a[1]).map(([br,qty])=>{
        const full = BRANCH_FULL[br] ?? br
        const col  = qty>=3 ? 'bg-emerald-900/30 text-emerald-400 border-emerald-700/40'
                   : qty>=1 ? 'bg-amber-900/30 text-amber-400 border-amber-700/40'
                   : 'bg-red-900/30 text-red-400 border-red-700/40'
        return <span key={br} className={`text-xs px-2 py-0.5 rounded border ${col}`}>{full}: {qty}</span>
      })}
    </div>
  )
}

export default function PCBuilderPage() {
  const [buildType, setBuildType]   = useState('Gaming Mid-range')
  const [tierIdx, setTierIdx]       = useState(2)
  const [budget, setBudget]         = useState(10_000_000)
  const [brand, setBrand]           = useState('Tidak Ada')
  const [notes, setNotes]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [build, setBuild]           = useState<any>(null)
  const [showAlt, setShowAlt]       = useState(false)
  const [alternatives, setAlts]     = useState<any[]>([])
  const [buildName, setBuildName]   = useState('')
  const [saving, setSaving]         = useState(false)

  const tier = BUDGET_TIERS[tierIdx]

  const handleTierChange = (idx: number) => {
    setTierIdx(idx)
    setBudget(Math.floor((BUDGET_TIERS[idx].min + BUDGET_TIERS[idx].max) / 2))
  }

  const handleBuild = async () => {
    setLoading(true); setBuild(null); setAlts([])
    try {
      const [buildRes, altRes] = await Promise.all([
        pcBuilderApi.build({ build_type:buildType, budget, preferred_brand:brand==='Tidak Ada'?null:brand, customer_notes:notes, generate_ai:true }),
        pcBuilderApi.alternatives({ build_type:buildType, budget }),
      ])
      setBuild(buildRes.data)
      setAlts(altRes.data.alternatives ?? [])
      setBuildName(`${buildType} Rp${(buildRes.data.total_price/1_000_000).toFixed(0)}Jt`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Gagal generate build')
    } finally { setLoading(false) }
  }

  const handleSave = async () => {
    if (!build || !buildName) return
    setSaving(true)
    try {
      const comps: Record<string,any> = {}
      build.components?.forEach((c:any) => { comps[c.kategori] = { nama:c.nama, harga:c.harga_jual, branch_stock:c.branch_stock } })
      await pcBuilderApi.save({ build_name:buildName, build_type:build.build_type, budget:build.budget, total_price:build.total_price, components:comps, ai_notes:build.ai_explanation?.slice(0,400)??'' })
      toast.success('Build tersimpan ke history')
    } catch { toast.error('Gagal menyimpan') } finally { setSaving(false) }
  }

  return (
    <Layout title="🖥️ PC Builder">
      {/* Config Form */}
      <div className="card mb-6">
        <h3 className="text-dark-100 font-semibold mb-4">⚙️ Konfigurasi Build</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div>
            <label className="block text-dark-300 text-xs font-medium mb-1.5">Tipe Build</label>
            <select className="input" value={buildType} onChange={e=>setBuildType(e.target.value)}>
              {BUILD_TYPES.map(t=><option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-dark-300 text-xs font-medium mb-1.5">Range Budget</label>
            <select className="input mb-2" value={tierIdx} onChange={e=>handleTierChange(Number(e.target.value))}>
              {BUDGET_TIERS.map((t,i)=><option key={i} value={i}>{t.label}</option>)}
            </select>
            <input type="range" min={tier.min} max={tier.max} step={500_000} value={budget}
              onChange={e=>setBudget(Number(e.target.value))} className="w-full accent-brand-500"/>
            <div className="text-brand-300 font-mono text-sm font-bold mt-1">{formatRupiahShort(budget)}</div>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-dark-300 text-xs font-medium mb-1.5">Preferensi CPU</label>
              <select className="input" value={brand} onChange={e=>setBrand(e.target.value)}>
                {['Tidak Ada','Intel','AMD'].map(b=><option key={b}>{b}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-dark-300 text-xs font-medium mb-1.5">Catatan Customer (opsional)</label>
              <input className="input" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Gaming FPS, streaming, dll..."/>
            </div>
          </div>
        </div>
        <button onClick={handleBuild} disabled={loading} className="btn-primary mt-5 flex items-center gap-2 px-8 py-3">
          {loading ? <Loader2 size={18} className="animate-spin"/> : <Cpu size={18}/>}
          {loading ? 'Memilih komponen...' : 'Generate Rekomendasi Build'}
        </button>
      </div>

      {/* Build Result */}
      {build && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Components */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-dark-100 font-semibold">📋 Komponen Terpilih</h3>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2.5 py-1 rounded-full border ${build.is_within_budget?'bg-emerald-900/30 text-emerald-400 border-emerald-700/40':'bg-amber-900/30 text-amber-400 border-amber-700/40'}`}>
                  {build.is_within_budget?'✓ Dalam budget':'⚠️ Melebihi budget'}
                </span>
              </div>
            </div>

            {build.compatibility_warnings?.length > 0 && (
              <div className="alert-danger mb-4 text-xs space-y-1">
                {build.compatibility_warnings.map((w:string,i:number)=><p key={i}><strong>⚠️</strong> {w}</p>)}
              </div>
            )}

            <div className="space-y-3 mb-4">
              {build.components?.map((comp:any,i:number)=>(
                <div key={i} className="bg-dark-800 border border-dark-600 rounded-xl p-3.5">
                  <div className="flex justify-between items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="text-dark-400 text-xs font-bold uppercase tracking-widest mb-1">{comp.kategori_label}</div>
                      <div className="text-dark-50 text-sm font-semibold leading-snug">{comp.nama}</div>
                    </div>
                    <span className="font-mono font-bold text-brand-300 text-sm shrink-0">{formatRupiah(comp.harga_jual)}</span>
                  </div>
                  <BranchStock bs={comp.branch_stock}/>
                </div>
              ))}
            </div>

            {/* Total */}
            <div className="flex justify-between items-center border-t border-dark-500 pt-4 mt-2">
              <span className="text-dark-200 font-bold text-sm">TOTAL HARGA BUILD</span>
              <span className="font-mono font-bold text-emerald-400 text-xl">{formatRupiah(build.total_price)}</span>
            </div>
            <div className="text-dark-400 text-xs mt-1 text-right">
              Budget: {formatRupiah(build.budget)} · Sisa: {formatRupiahShort(Math.max(0,build.budget-build.total_price))}
            </div>

            {/* Compat notes */}
            {build.compatibility_notes?.length > 0 && (
              <div className="mt-4 space-y-1.5">
                {build.compatibility_notes.map((n:string,i:number)=>(
                  <p key={i} className={`text-xs ${n.includes('✅')?'text-emerald-400':n.includes('⚠️')?'text-amber-400':'text-dark-300'}`}>{n}</p>
                ))}
              </div>
            )}

            {/* Save */}
            <div className="mt-5 pt-4 border-t border-dark-600 flex gap-3">
              <input className="input flex-1 text-sm" value={buildName} onChange={e=>setBuildName(e.target.value)} placeholder="Nama build..."/>
              <button onClick={handleSave} disabled={saving} className="btn-success flex items-center gap-2 px-4 shrink-0">
                {saving ? <Loader2 size={14} className="animate-spin"/> : <Save size={14}/>} Simpan
              </button>
            </div>
          </div>

          {/* AI Explanation */}
          <div className="space-y-5">
            {build.ai_explanation && (
              <div className="card">
                <h3 className="text-dark-100 font-semibold mb-3">🤖 Penjelasan untuk Customer</h3>
                <p className="text-dark-100 text-sm leading-relaxed whitespace-pre-line">{build.ai_explanation}</p>
              </div>
            )}

            {/* Alternatives */}
            {alternatives.length > 0 && (
              <div className="card">
                <button className="flex items-center justify-between w-full" onClick={()=>setShowAlt(!showAlt)}>
                  <h3 className="text-dark-100 font-semibold">🔀 Alternatif Build</h3>
                  {showAlt ? <ChevronUp size={18} className="text-dark-300"/> : <ChevronDown size={18} className="text-dark-300"/>}
                </button>
                {showAlt && (
                  <div className="mt-4 space-y-4">
                    {alternatives.map((alt:any,i:number)=>(
                      <div key={i} className="bg-dark-800 border border-dark-600 rounded-xl p-4">
                        <div className="flex justify-between items-center mb-3">
                          <span className="text-dark-200 text-sm font-semibold">
                            {alt.total_price < build.total_price ? '💰 Budget Hemat' : '⬆️ Upgrade Option'}
                          </span>
                          <span className="font-mono font-bold text-brand-300">{formatRupiahShort(alt.total_price)}</span>
                        </div>
                        <div className="space-y-2">
                          {alt.components?.map((c:any,j:number)=>(
                            <div key={j}>
                              <div className="flex justify-between text-xs">
                                <span className="text-dark-300">{c.kategori_label}</span>
                                <span className="font-mono text-dark-100">{formatRupiah(c.harga_jual)}</span>
                              </div>
                              <p className="text-dark-400 text-xs">{c.nama}</p>
                              <BranchStock bs={c.branch_stock}/>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}
