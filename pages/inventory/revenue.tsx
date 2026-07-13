import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import { RevenueWaterfall } from '@/components/charts/InventoryCharts'
import { PageLoading, NoData } from '@/components/ui/Loading'
import { inventoryApi } from '@/lib/api'
import { formatRupiahShort, formatPercent, formatNumber } from '@/lib/format'

export default function RevenuePage() {
  const { data, isLoading } = useQuery({ queryKey:['inv-summary'], queryFn:()=>inventoryApi.summary() })
  const s = data?.data?.revenue_summary

  const waterfallData = s ? [
    { name:'Nilai Inventory',    value: s.inventory_value },
    { name:'Dead Stock (Risiko)',value: -s.dead_stock_value },
    { name:'Potensi Profit',     value: s.potential_profit },
    { name:'Butuh Restock',      value: -s.restock_value },
    { name:'Hemat Transfer',     value: s.transfer_value || 0 },
  ] : []

  const rows = s ? [
    ['Total Nilai Inventory (HPP)', formatRupiahShort(s.inventory_value)],
    ['Dead Stock — Modal Tertahan', formatRupiahShort(s.dead_stock_value)],
    ['Dead Stock % dari Inventory', formatPercent(s.dead_stock_pct)],
    ['Potensi Profit', formatRupiahShort(s.potential_profit)],
    ['Potensi Revenue (jika semua terjual)', formatRupiahShort(s.potential_revenue)],
    ['Nilai Restock Dibutuhkan', formatRupiahShort(s.restock_value)],
    ['Total SKU', formatNumber(s.total_sku)],
    ['SKU Fast Moving', formatNumber(s.fast_sku)],
    ['SKU Dead Stock', formatNumber(s.dead_sku)],
  ] : []

  return (
    <Layout title="📊 Revenue Opportunity">
      {isLoading ? <PageLoading/> : !s ? <NoData/> : (
        <>
          <div className="card mb-6">
            <h3 className="text-dark-100 font-semibold mb-4">Revenue & Risiko Overview</h3>
            <RevenueWaterfall data={waterfallData}/>
          </div>
          <div className="card mb-6">
            <h3 className="text-dark-100 font-semibold mb-4">📋 Ringkasan Finansial</h3>
            <div className="divide-y divide-dark-600">
              {rows.map(([label,value],i) => (
                <div key={i} className="flex justify-between py-3">
                  <span className="text-dark-200 text-sm">{label}</span>
                  <span className="font-mono text-dark-50 font-semibold text-sm">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="alert-info">
            <strong>📊 Strategi Utama</strong> — Gerakkan dead stock ({formatRupiahShort(s.dead_stock_value)}) → Optimalkan transfer → Restock fast moving → Naikkan Very Fast ke H2.
          </div>
        </>
      )}
    </Layout>
  )
}
