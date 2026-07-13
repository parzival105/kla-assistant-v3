export function Spinner({ size = 24 }: { size?: number }) {
  return (
    <div className="flex items-center justify-center">
      <svg className="animate-spin text-brand-400" width={size} height={size} viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
        <path className="opacity-75" fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>
  )
}

export function PageLoading() {
  return (
    <div className="flex items-center justify-center min-h-96">
      <div className="text-center">
        <Spinner size={36} />
        <div className="text-dark-300 text-sm mt-3">Memuat data...</div>
      </div>
    </div>
  )
}

export function NoData({ message = 'Belum ada data. Super Admin perlu upload file stok.' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-80 text-center">
      <div className="text-5xl mb-4">📂</div>
      <div className="text-dark-100 font-semibold text-lg mb-2">Tidak ada data</div>
      <div className="text-dark-300 text-sm max-w-sm">{message}</div>
    </div>
  )
}
