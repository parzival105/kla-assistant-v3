import { useState, useRef } from 'react'
import Layout from '@/components/layout/Layout'
import { salesApi, pcBuilderApi } from '@/lib/api'
import { formatRupiahShort, formatRupiah, formatNumber } from '@/lib/format'
import { getUser } from '@/lib/auth'
import { Search, Cpu, Wrench, Package, ChevronRight, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const BRANCH_FULL: Record<string,string> = {
  SMG:'Semarang',YK:'Yogyakarta',SLA:'Slawi',TGL:'Tegal',PKL:'Pekalongan',
  CRB:'Cirebon',KDR:'Kediri',NGL:'Ngaliyan',SKH:'Sukoharjo',
  MSBY:'Surabaya Merr',MJK:'Mojokerto',BSBY:'Surabaya Babatan',PWT:'Purwokerto'
}

const SHORTCUTS = [
  'Monitor gaming 144Hz budget 2 juta',
  'Laptop tipis ringan budget 8 juta',
  'Printer wireless untuk kantor',
  'PC gaming budget 12 juta',
  'Mouse wireless Logitech',
  'Headset gaming under 500 ribu',
  'Tinta Epson L3250',
  'RAM laptop ASUS VivoBook upgrade',
]

function IntentBadge({ intent }: { intent: string }) {
  const map: Record<string, { label: string; icon: any; cls: string }> = {
    PRODUCT_SEARCH:  { label:'Product Search', icon:Search,  cls:'bg-emerald-900/30 text-emerald-400 border-emerald-700/40' },
    PC_BUILDER:      { label:'PC Builder',     icon:Cpu,     cls:'bg-violet-900/30 text-violet-400 border-violet-700/40' },
    COMPATIBILITY:   { label:'Compatibility',  icon:Wrench,  cls:'bg-amber-900/30 text-amber-400 border-amber-700/40' },
    STOCK_CHECK:     { label:'Stock Check',    icon:Package, cls:'bg-blue-900/30 text-blue-400 border-blue-700/40' },
    GENERAL:         { label:'General',        icon:Search,  cls:'bg-dark-600 text-dark-200 border-dark-500' },
  }
  const m = map[intent] ?? map.GENERAL
  const Icon = m.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${m.cls}`}>
      <Icon size={12}/>{m.label}
    </span>
  )
}

function BranchStock({ branchStock }: { branchStock: Record<string,number> }) {
  if (!branchStock || Object.keys(branchStock).length === 0)
    return <span className="text-red-400 text-xs">⚠️ Stok kosong semua cabang</span>
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {Object.entries(branchStock).sort((a,b)=>b[1]-a[1]).map(([br,qty])=>{
        const full = BRANCH_FULL[br] ?? br
        const col  = qty>=3?'bg-emerald-900/30 text-emerald-400 border-emerald-700/40'
                   : qty>=1?'bg-amber-900/30 text-amber-400 border-amber-700/40'
                   : 'bg-red-900/30 text-red-400 border-red-700/40'
        return (
          <span key={br} className={`text-xs px-2 py-0.5 rounded border ${col}`}>
            {full}: {qty}
          </span>
        )
      })}
    </div>
  )
}

function ProductCard({ product, index, role }: { product: any; index: number; role: string }) {
  const isTop = index === 0
  return (
    <div className={`bg-dark-700 border rounded-xl p-4 transition-all hover:border-brand-600/50 ${isTop?'border-brand-600/40':'border-dark-500'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {isTop && <span className="text-xs bg-brand-700/40 text-brand-300 px-2 py-0.5 rounded-full border border-brand-600/40">🥇 Teratas</span>}
            <span className="text-dark-50 font-semibold text-sm leading-snug">{product.nama_barang}</span>
          </div>
          <div className="text-dark-300 text-xs mb-2">{product.kategori} · {product.brand || product.segment}</div>
          <BranchStock branchStock={product.branch_stock}/>
        </div>
        <div className="text-right shrink-0">
          <div className="font-mono font-bold text-brand-300 text-lg">{formatRupiahShort(product.harga_jual)}</div>
          {product.margin_persen != null && (
            <div className={`text-xs font-semibold mt-0.5 ${product.margin_persen>=15?'text-emerald-400':product.margin_persen>=8?'text-amber-400':'text-red-400'}`}>
              Margin {product.margin_persen?.toFixed(1)}%
            </div>
          )}
          {product.hpp != null && <div className="text-dark-400 text-xs mt-0.5">HPP: {formatRupiahShort(product.hpp)}</div>}
          <div className="text-dark-300 text-xs mt-1">Stok: {formatNumber(product.total_stok)} · {product.runrate_bulanan?.toFixed(1)}/bln</div>
        </div>
      </div>
    </div>
  )
}

function PcBuilderRedirect({ data, onConfirm }: { data: any; onConfirm: (type:string,budget:number)=>void }) {
  const [budget, setBudget] = useState(data.suggested_budget || 10_000_000)
  const [buildType, setBuildType] = useState(data.suggested_build_type || 'Gaming Mid-range')
  const BUILD_TYPES = ['Office / Kerja','Gaming Entry','Gaming Mid-range','Gaming High-end','Desain Grafis','Video Editing','Coding / Development','Workstation']
  return (
    <div className="bg-dark-700 border border-violet-700/40 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Cpu size={18} className="text-violet-400"/>
        <span className="text-dark-50 font-semibold">Mode PC Builder</span>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-dark-300 text-xs font-medium mb-1.5 block">Tipe Build</label>
          <select className="input text-sm" value={buildType} onChange={e=>setBuildType(e.target.value)}>
            {BUILD_TYPES.map(t=><option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label className="text-dark-300 text-xs font-medium mb-1.5 block">Budget: {formatRupiahShort(budget)}</label>
          <input type="range" min={3_000_000} max={35_000_000} step={500_000} value={budget}
            onChange={e=>setBudget(Number(e.target.value))} className="w-full accent-brand-500"/>
        </div>
      </div>
      <button onClick={()=>onConfirm(buildType,budget)} className="btn-primary flex items-center gap-2">
        <Cpu size={16}/> Generate Build
      </button>
    </div>
  )
}

function PcBuildResult({ build }: { build: any }) {
  return (
    <div className="bg-dark-700 border border-dark-500 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-dark-50 font-bold">🖥️ {build.build_type}</span>
        <span className="font-mono font-bold text-emerald-400 text-lg">{formatRupiah(build.total_price)}</span>
      </div>
      {build.compatibility_warnings?.length > 0 && (
        <div className="alert-danger mb-3 text-xs">
          {build.compatibility_warnings.map((w:string,i:number)=><p key={i}>{w}</p>)}
        </div>
      )}
      <div className="space-y-2 mb-4">
        {build.components?.map((comp:any, i:number)=>(
          <div key={i} className="bg-dark-800 rounded-lg p-3">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-dark-400 text-xs font-semibold uppercase tracking-wider mb-0.5">{comp.kategori_label}</div>
                <div className="text-dark-100 text-sm font-medium">{comp.nama}</div>
              </div>
              <span className="font-mono text-brand-300 font-semibold text-sm shrink-0 ml-3">{formatRupiah(comp.harga_jual)}</span>
            </div>
            <BranchStock branchStock={comp.branch_stock}/>
          </div>
        ))}
      </div>
      {build.compatibility_notes?.map((n:string,i:number)=>(
        <p key={i} className="text-xs text-dark-300 mb-1">{n}</p>
      ))}
      {build.ai_explanation && (
        <div className="mt-4 p-4 bg-dark-800 rounded-xl border border-dark-600">
          <p className="text-dark-300 text-xs font-semibold mb-2">🤖 Penjelasan untuk Customer:</p>
          <p className="text-dark-100 text-sm leading-relaxed whitespace-pre-line">{build.ai_explanation}</p>
        </div>
      )}
    </div>
  )
}

export default function AssistantPage() {
  const user    = getUser()
  const role    = user?.role ?? 'sales'
  const [query, setQuery]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState<any>(null)
  const [buildResult, setBuildResult] = useState<any>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleQuery = async (q: string) => {
    if (!q.trim()) return
    setQuery(q)
    setLoading(true)
    setResult(null)
    setBuildResult(null)
    try {
      const res = await salesApi.query(q)
      setResult(res.data)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Gagal memproses query')
    } finally { setLoading(false) }
  }

  const handleBuild = async (buildType: string, budget: number) => {
    setLoading(true)
    try {
      const res = await pcBuilderApi.build({ build_type:buildType, budget, generate_ai:true })
      setBuildResult(res.data)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Gagal generate build')
    } finally { setLoading(false) }
  }

  return (
    <Layout title="🤖 Sales Assistant">
      {/* Main Input */}
      <div className="bg-gradient-to-br from-dark-700 to-dark-600 border-2 border-brand-700/40 rounded-2xl p-6 mb-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-brand-700 via-brand-400 to-brand-700"/>
        <label className="block text-brand-400 text-xs font-bold uppercase tracking-widest mb-3">
          💬 APA YANG SEDANG DICARI CUSTOMER?
        </label>
        <div className="flex gap-3">
          <input
            ref={inputRef}
            value={query}
            onChange={e=>setQuery(e.target.value)}
            onKeyDown={e=>e.key==='Enter' && handleQuery(query)}
            className="input flex-1 text-base"
            placeholder='Contoh: "Monitor 24 inch IPS budget 2 juta" atau "PC gaming 12 juta" atau "Tinta Epson L3250"'
          />
          <button onClick={()=>handleQuery(query)} disabled={loading || !query.trim()} className="btn-primary px-6 flex items-center gap-2 shrink-0">
            {loading ? <Loader2 size={18} className="animate-spin"/> : <Search size={18}/>}
            {loading ? 'Mencari...' : 'Cari'}
          </button>
        </div>

        {/* Shortcuts */}
        <div className="mt-4 flex flex-wrap gap-2">
          {SHORTCUTS.map(s=>(
            <button key={s} onClick={()=>handleQuery(s)}
              className="text-xs px-3 py-1.5 bg-dark-700 border border-dark-500 rounded-full text-dark-200 hover:border-brand-600/50 hover:text-brand-300 transition-all">
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <Loader2 size={36} className="animate-spin text-brand-400"/>
          <p className="text-dark-300 text-sm">Menganalisa kebutuhan customer...</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-4">
          {/* Intent badge + meta */}
          <div className="flex items-center gap-3 flex-wrap">
            <IntentBadge intent={result.intent}/>
            {result.category_hint && <span className="text-dark-300 text-xs">Kategori: <span className="text-dark-100">{result.category_hint}</span></span>}
            {result.budget_hint   && <span className="text-dark-300 text-xs">Budget: <span className="text-brand-300 font-mono">{formatRupiahShort(result.budget_hint)}</span></span>}
            {result.brand_hint    && <span className="text-dark-300 text-xs">Brand: <span className="text-dark-100">{result.brand_hint}</span></span>}
          </div>

          {/* Notes */}
          {result.notes?.map((note:string, i:number)=>(
            <div key={i} className="alert-info text-xs">{note}</div>
          ))}

          {/* Product Search Results */}
          {result.mode === 'product_search' && (
            <>
              <p className="text-dark-300 text-sm">Ditemukan <strong className="text-dark-100">{result.total_found}</strong> produk relevan</p>
              {result.products?.length === 0
                ? <div className="alert-warning">Tidak ada produk cocok. Coba kata kunci berbeda.</div>
                : <div className="space-y-3">{result.products.map((p:any,i:number)=><ProductCard key={i} product={p} index={i} role={role}/>)}</div>
              }
            </>
          )}

          {/* Compatibility Results */}
          {result.mode === 'compatibility' && (
            <div className="space-y-4">
              <div className="bg-dark-700 border border-dark-500 rounded-xl p-5">
                <p className="text-dark-300 text-xs font-semibold mb-2">🔧 Analisa Kompatibilitas</p>
                <p className="text-dark-100 text-sm leading-relaxed whitespace-pre-line">{result.answer}</p>
              </div>
              {result.recommended_products?.length > 0 && (
                <>
                  <p className="text-dark-200 font-semibold text-sm">Produk yang Direkomendasikan:</p>
                  <div className="space-y-2">
                    {result.recommended_products.map((p:any,i:number)=>(
                      <div key={i} className="bg-dark-700 border border-dark-500 rounded-xl p-4 flex justify-between">
                        <div>
                          <p className="text-dark-50 font-medium text-sm">{p.nama}</p>
                          <p className="text-dark-300 text-xs mt-0.5">Stok: {p.stok} unit · Laku {p.runrate?.toFixed(1)}/bulan</p>
                        </div>
                        <span className="font-mono font-bold text-brand-300">{formatRupiah(p.h1)}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
              {result.upsell_suggestions?.length > 0 && (
                <>
                  <p className="text-dark-200 font-semibold text-sm mt-2">💡 Produk Tambahan (Upsell):</p>
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                    {result.upsell_suggestions.map((p:any,i:number)=>(
                      <div key={i} className="bg-dark-700 border border-dark-500 rounded-xl p-3 text-center">
                        <p className="text-dark-100 text-xs font-semibold mb-1 line-clamp-2">{p.nama}</p>
                        <p className="font-mono text-brand-300 font-bold">{formatRupiahShort(p.h1)}</p>
                        <p className="text-dark-400 text-xs mt-0.5">Stok: {p.stok}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* PC Builder redirect */}
          {result.mode === 'pc_builder' && !buildResult && (
            <PcBuilderRedirect data={result} onConfirm={handleBuild}/>
          )}
          {buildResult && <PcBuildResult build={buildResult}/>}
        </div>
      )}

      {/* Examples (when empty) */}
      {!result && !loading && (
        <div className="card">
          <h3 className="text-dark-100 font-semibold mb-5">💡 Contoh Pertanyaan</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title:'🖥️ PC Rakitan', items:['PC gaming budget 15 juta','PC kantor budget 5 juta','PC editing 4K budget 25 juta'] },
              { title:'🛒 Cari Produk', items:['Monitor curved 27 inch','Printer laser untuk kantor','Headset gaming wireless'] },
              { title:'🔧 Kompatibilitas', items:['RAM laptop ASUS VivoBook','Tinta Epson L3250','SSD untuk Acer Aspire'] },
              { title:'📦 Lainnya',     items:['Mouse wireless Logitech','Webcam zoom meeting','UPS 1200VA'] },
            ].map(group=>(
              <div key={group.title}>
                <p className="text-dark-300 text-xs font-semibold mb-2">{group.title}</p>
                <div className="space-y-1.5">
                  {group.items.map(item=>(
                    <button key={item} onClick={()=>handleQuery(item)}
                      className="w-full text-left text-xs px-3 py-2 bg-dark-700 hover:bg-dark-600 border border-dark-500 hover:border-brand-600/40 rounded-lg text-dark-200 hover:text-dark-50 transition-all flex items-center justify-between group">
                      <span>{item}</span>
                      <ChevronRight size={12} className="text-dark-500 group-hover:text-brand-400 shrink-0"/>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Layout>
  )
}
