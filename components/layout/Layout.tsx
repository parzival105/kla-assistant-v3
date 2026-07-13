import { ReactNode, useEffect } from 'react'
import { useRouter } from 'next/router'
import { isLoggedIn } from '@/lib/auth'
import Sidebar from './Sidebar'
import { Toaster } from 'react-hot-toast'

interface LayoutProps { children: ReactNode; title?: string }

export default function Layout({ children, title }: LayoutProps) {
  const router = useRouter()

  useEffect(() => {
    if (!isLoggedIn()) router.replace('/auth/login')
  }, [router])

  if (!isLoggedIn()) return null

  return (
    <div className="min-h-screen bg-dark-900 flex">
      <Sidebar />
      <main className="ml-60 flex-1 p-6 overflow-y-auto min-h-screen">
        {title && (
          <div className="mb-6">
            <h1 className="text-2xl font-extrabold bg-gradient-to-r from-brand-400 to-brand-200
                           bg-clip-text text-transparent">{title}</h1>
          </div>
        )}
        {children}
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#180d28', color: '#c4b5d4', border: '1px solid #2d1a45' },
          success: { iconTheme: { primary: '#059669', secondary: '#180d28' } },
          error:   { iconTheme: { primary: '#dc2626', secondary: '#180d28' } },
        }}
      />
    </div>
  )
}
