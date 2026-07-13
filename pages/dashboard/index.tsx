import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import KpiCard from '@/components/ui/KpiCard'
import { CategoryDonut, CategoryValueBar, HealthScoreBar } from '@/components/charts/InventoryCharts'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi, branchApi } from '@/lib/api'
import { formatRupiahShort, formatNumber, formatPercent, getCategoryColor } from '@/lib/format'
import { getUser } from '@/lib/auth'
import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { Upload, AlertTriangle, TrendingUp, Package, ArrowLeftRight, ShoppingCart } from 'lucide-react'

function UploadZone({ onSuccess }: { onSuccess: () => void }) {
  const [uploading, setUploading] = useState(false)
  const onDrop = useCallback(async (files: File[]) => {
    if (!files[0]) return
    setUploading(true)
    try {
      const res = await inventoryApi.upload(files[0])
      toast.success(`✅ ${res.data.sku_count?.toLocaleString()} SKU berhasil dianalisa`)
      onSuccess()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload gagal')
    } finally { setUploading(false) }
  }, [onSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 'application/vnd.ms-excel': ['.xls'] }, maxFiles: 1
  })

  return (
    <div {...getRootProps()} className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all
      ${isDragActive ? 'border-brand-500 bg-brand-900/20' : 'border-dark-500 hover:border-brand-600 bg-dark-800'}`}>
      <input {...getInputProps()} />
      <Upload size={36} className="mx-auto mb-3 text-brand-400" />
      <p className="text-dark-100 font-semibold text-base mb-1">
        {uploading ? 'Menganalisa...' : isDragActive ? 'Lepaskan file di sini' : 'Upload File Stok Excel'}
      </p>
      <p className="text-dark-300 text-sm">Format .xlsx · Auto-detect kolom & 13 cabang</p>
      {uploading && (
        <div className="mt-4 flex justify-center">
          <svg className="animate-spin text-brand-400" width={24} height={24} viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </div>
      )}
    </div>
  )
}


export default function DashboardPage() {
  const user = getUser()
  const isAdmin = user?.role === 'super_admin' || user?.role === 'area_manager'

  const statusQ = useQuery({ queryKey: ['inv-status'], queryFn: () => inventoryApi.status() })
  const summaryQ = useQuery({
    queryKey: ['inv-summary'],
    queryFn: () => inventoryApi.summary(),
    enabled: statusQ.data?.data?.has_data === true,
  })
  const branchQ = useQuery({
    queryKey: ['branch-summary'],
    queryFn: () => branchApi.summary(),
    enabled: statusQ.data?.data?.has_data === true,
  })

  const hasData = statusQ.data?.data?.has_data
  const s = summaryQ.data?.data

  const catColors = { 'Very Fast':'#059669','Fast':'#7c3aed','Slow':'#d97706','Dead Stock':'#dc2626' }
  const catData = s ? Object.entries(s.category_counts || {}).map(([name, value]) => ({
    name, value: value as number, color: catColors[name as keyof typeof catColors] ?? '#94a3b8'
  })) : []
  const catValData = s ? Object.entries(s.category_values || {}).map(([name, value]) => ({
    name, value: value as number, color: catColors[name as keyof typeof catColors] ?? '#94a3b8'
  })) : []
  const branches = branchQ.data?.data?.branches ?? []

  return (
    <Layout title="Executive Dashboard">
      {/* Upload Section (Admin only) */}
      {isAdmin && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-dark-50 font-bold text-base">📂 Upload / Update File Stok</h2>
            {hasData && (
              <span className="text-xs text-emerald-400 bg-emerald-900/30 border border-emerald-700/40 px-3 py-1 rounded-full">
                ✓ Data aktif · {statusQ.data?.data?.filename}
              </span>
            )}
          </div>
          <UploadZone onSuccess={() => { statusQ.refetch(); summaryQ.refetch(); branchQ.refetch() }} />
        </div>
      )}

      {/* No data */}
      {!hasData && !summaryQ.isLoading && (
        <div className="card text-center py-16">
          <div className="text-5xl mb-4">📊</div>
          <h3 className="text-dark-100 font-bold text-lg mb-2">Belum ada data inventory</h3>
          <p className="text-dark-300 text-sm">
            {isAdmin ? 'Upload file Excel stok di atas untuk mulai analisa.' : 'Super Admin belum mengupload file stok. Mohon tunggu.'}
          </p>
        </div>
      )}

      {/* KPIs */}
      {s && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <KpiCard label="Total Nilai Inventory" value={formatRupiahShort(s.revenue_summary?.inventory_value)} sub={`${formatNumber(s.revenue_summary?.total_sku)} SKU aktif`} color="purple" />
            <KpiCard label="Modal Tertahan" value={formatRupiahShort(s.revenue_summary?.dead_stock_value)} sub={`${formatPercent(s.revenue_summary?.dead_stock_pct)} dari inventory`} color="red" />
            <KpiCard label="Potensi Profit" value={formatRupiahShort(s.revenue_summary?.potential_profit)} sub="Jika semua terjual optimal" color="green" />
            <KpiCard label="Potensi Revenue" value={formatRupiahShort(s.revenue_summary?.potential_revenue)} sub="Stok × harga rekomendasi" color="blue" />
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <KpiCard label="SKU Fast Moving" value={formatNumber(s.revenue_summary?.fast_sku)} sub="Very Fast + Fast" color="green" />
            <KpiCard label="SKU Dead Stock" value={formatNumber(s.revenue_summary?.dead_sku)} sub="Runrate < 4/bulan" color="red" />
            <KpiCard label="Rekomendasi Transfer" value={formatNumber(s.transfer_count)} sub="Transaksi antar cabang" color="purple" />
            <KpiCard label="SKU Perlu Restock" value={formatNumber(s.restock_count)} sub={formatRupiahShort(s.revenue_summary?.restock_value)} color="orange" />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="card">
              <h3 className="text-dark-100 font-semibold mb-4">📊 Distribusi Kategori Produk</h3>
              <CategoryDonut data={catData} />
            </div>
            <div className="card">
              <h3 className="text-dark-100 font-semibold mb-4">💰 Nilai Inventory per Kategori</h3>
              <CategoryValueBar data={catValData} />
            </div>
          </div>

          {/* Branch health snapshot */}
          {branches.length > 0 && (
            <div className="card mb-6">
              <h3 className="text-dark-100 font-semibold mb-4">🏢 Health Score Seluruh Cabang</h3>
              <HealthScoreBar data={branches} />
            </div>
          )}

          {/* AI Insights */}
          <div className="card">
            <h3 className="text-dark-100 font-semibold mb-4">🤖 AI Business Insights</h3>
            {(() => {
              const dp = s.revenue_summary?.dead_stock_pct ?? 0
              return (
                <div className="space-y-3">
                  {dp > 30 ? (
                    <div className="alert-danger">
                      <strong>🔴 KRITIS</strong> — Dead stock mencapai {formatPercent(dp)} ({formatRupiahShort(s.revenue_summary?.dead_stock_value)}). Lakukan clearance segera.
                    </div>
                  ) : dp > 15 ? (
                    <div className="alert-warning">
                      <strong>🟡 PERHATIAN</strong> — Dead stock {formatPercent(dp)}. Pertimbangkan bundling/promo.
                    </div>
                  ) : (
                    <div className="alert-success">
                      <strong>🟢 BAIK</strong> — Dead stock terkontrol di {formatPercent(dp)}.
                    </div>
                  )}
                  {s.transfer_count > 0 && (
                    <div className="alert-info">
                      <strong>💡 TRANSFER</strong> — {formatNumber(s.transfer_count)} rekomendasi transfer tersedia. Optimalkan sebelum purchase order baru.
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </>
      )}
    </Layout>
  )
}
