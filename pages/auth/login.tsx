import { useState } from 'react'
import { useRouter } from 'next/router'
import { authApi } from '@/lib/api'
import { setAuth } from '@/lib/auth'
import toast from 'react-hot-toast'
import { Toaster } from 'react-hot-toast'
import { Eye, EyeOff, LogIn } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) { toast.error('Username dan password wajib diisi'); return }
    setLoading(true)
    try {
      const res = await authApi.login(username, password)
      setAuth(res.data.token, res.data.user)
      toast.success(`Selamat datang, ${res.data.user.full_name}!`)
      router.replace('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login gagal')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
      <Toaster position="top-right" toastOptions={{
        style: { background: '#180d28', color: '#c4b5d4', border: '1px solid #2d1a45' }
      }}/>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16
                          bg-gradient-to-br from-brand-700 to-brand-500 rounded-2xl mb-4">
            <span className="text-white font-black text-2xl tracking-widest">KLA</span>
          </div>
          <h1 className="text-2xl font-extrabold text-dark-50">Business Suite</h1>
          <p className="text-dark-300 text-sm mt-1">PT KLA Teknologi Indonesia</p>
          <p className="text-dark-400 text-xs mt-0.5">Komplit · Nyaman · Bergaransi</p>
        </div>

        {/* Card */}
        <div className="card border-dark-500 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-brand-700 via-brand-400 to-brand-700"/>
          <h2 className="text-dark-50 font-bold text-lg mb-6 text-center">Masuk ke Akun Anda</h2>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-dark-200 text-sm font-medium mb-1.5">Username</label>
              <input
                type="text" value={username} onChange={e => setUsername(e.target.value)}
                placeholder="Masukkan username"
                className="input" autoComplete="username"
              />
            </div>
            <div>
              <label className="block text-dark-200 text-sm font-medium mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'} value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Masukkan password"
                  className="input pr-10" autoComplete="current-password"
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-300 hover:text-dark-100">
                  {showPw ? <EyeOff size={16}/> : <Eye size={16}/>}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
                    className="btn-primary w-full flex items-center justify-center gap-2 py-3 mt-2">
              {loading ? (
                <svg className="animate-spin" width={18} height={18} viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              ) : <LogIn size={18}/>}
              {loading ? 'Memproses...' : 'Masuk'}
            </button>
          </form>

          <div className="mt-5 pt-5 border-t border-dark-600 text-center">
            <p className="text-dark-400 text-xs">Lupa password? Hubungi Super Admin KLA.</p>
          </div>
        </div>

        {/* Default creds hint - remove in production */}
        <details className="mt-4 text-center">
          <summary className="text-dark-400 text-xs cursor-pointer hover:text-dark-200">
            ℹ️ Info Login Default
          </summary>
          <div className="mt-2 bg-dark-700 border border-dark-500 rounded-lg p-3 text-xs font-mono text-dark-200">
            Username: admin<br/>Password: admin123<br/>Role: Super Admin
          </div>
        </details>
      </div>
    </div>
  )
}
