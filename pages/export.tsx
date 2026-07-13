import Layout from '@/components/layout/Layout'
import { exportApi } from '@/lib/api'
import { useState } from 'react'
import { Download, FileSpreadsheet, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const SHEETS = [
  { name:'📊 Executive Summary',   desc:'KPI utama, revenue, dead stock' },
  { name:'🤖 AI Recommendation',   desc:'Daftar rekomendasi bisnis otomatis' },
  { name:'📦 Inventory Analysis',  desc:'Runrate, kategori, min stock semua SKU' },
  { name:'🏢 Branch Analysis',     desc:'Health score dan status stok per cabang' },
  { name:'🛒 Restock',             desc:'Prioritas pembelian baru' },
  { name:'🔄 Transfer',            desc:'Pemindahan stok antar cabang' },
  { name:'☠️ Dead Stock',          desc:'Produk tidak bergerak & rekomendasi aksi' },
  { name:'💰 Pricing',             desc:'Harga optimal per produk' },
  { name:'📈 Profit',              desc:'Margin dan potensi profit' },
]

export default function ExportPage() {
  const [loading, setLoading] = useState(false)

  const handleDownload = async () => {
    setLoading(true)
    try {
      const res = await exportApi.excel()
      const blob = new Blob([res.data], { type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `KLA_Report_${new Date().toISOString().slice(0,10)}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Laporan berhasil didownload!')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Gagal export')
    } finally { setLoading(false) }
  }

  return (
    <Layout title="📥 Export Excel">
      <div className="max-w-2xl mx-auto">
        <div className="card text-center mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-brand-700 via-brand-400 to-brand-700"/>
          <FileSpreadsheet size={52} className="mx-auto mb-4 text-brand-400"/>
          <h2 className="text-dark-50 font-bold text-xl mb-2">Export Siap</h2>
          <p className="text-dark-300 text-sm mb-6">9 sheet analisa lengkap dalam satu file Excel</p>
          <button onClick={handleDownload} disabled={loading}
            className="btn-success inline-flex items-center gap-3 px-8 py-3.5 text-base">
            {loading ? <Loader2 size={20} className="animate-spin"/> : <Download size={20}/>}
            {loading ? 'Menyiapkan file...' : 'Download Laporan Lengkap (.xlsx)'}
          </button>
        </div>

        <div className="card">
          <h3 className="text-dark-100 font-semibold mb-4">📋 Sheet yang Tersedia</h3>
          <div className="space-y-2">
            {SHEETS.map((s,i)=>(
              <div key={i} className="flex items-start gap-3 py-2.5 border-b border-dark-600 last:border-0">
                <span className="text-dark-50 font-medium text-sm w-48 shrink-0">{s.name}</span>
                <span className="text-dark-300 text-sm">{s.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
