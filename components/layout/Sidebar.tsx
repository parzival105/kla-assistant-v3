import { useRouter } from 'next/router'
import Link from 'next/link'
import { getUser, clearAuth, hasRole, ROLES } from '@/lib/auth'
import { authApi } from '@/lib/api'
import {
  LayoutDashboard, Package, Building2, ArrowLeftRight, ShoppingCart,
  TrendingUp, Skull, BarChart3, Bot, Download, Users, Monitor, Search,
  LogOut, ChevronRight
} from 'lucide-react'

const allMenuItems = [
  { href:'/dashboard',          label:'Executive Dashboard', icon:LayoutDashboard, roles:['super_admin','area_manager','store_leader'] },
  { href:'/dashboard/users',    label:'User Management',     icon:Users,           roles:['super_admin'] },
  { href:'/inventory',          label:'Inventory Analysis',  icon:Package,         roles:['super_admin','area_manager','store_leader'] },
  { href:'/branch',             label:'Branch Intelligence', icon:Building2,       roles:['super_admin','area_manager','store_leader'] },
  { href:'/inventory/transfer', label:'Transfer Engine',     icon:ArrowLeftRight,  roles:['super_admin','area_manager','store_leader'] },
  { href:'/inventory/restock',  label:'Restock Engine',      icon:ShoppingCart,    roles:['super_admin','area_manager','store_leader'] },
  { href:'/inventory/pricing',  label:'Pricing',             icon:TrendingUp,      roles:['super_admin','area_manager','store_leader'] },
  { href:'/inventory/deadstock',label:'Dead Stock',          icon:Skull,           roles:['super_admin','area_manager','store_leader'] },
  { href:'/inventory/revenue',  label:'Revenue',             icon:BarChart3,       roles:['super_admin','area_manager'] },
  { href:'/inventory/recs',     label:'AI Recommendation',   icon:Bot,             roles:['super_admin','area_manager','store_leader'] },
  { href:'/sales/assistant',    label:'Sales Assistant',     icon:Search,          roles:['super_admin','area_manager','store_leader','sales'] },
  { href:'/sales/pc-builder',   label:'PC Builder',          icon:Monitor,         roles:['super_admin','area_manager','store_leader','sales'] },
  { href:'/export',             label:'Export Excel',        icon:Download,        roles:['super_admin'] },
]

export default function Sidebar() {
  const router  = useRouter()
  const user    = getUser()
  if (!user) return null

  const visibleItems = allMenuItems.filter(item => hasRole(user, ...item.roles))

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    clearAuth()
    router.push('/auth/login')
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-dark-800 border-r border-dark-500 flex flex-col z-40 overflow-y-auto">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-dark-500">
        <div className="flex items-center gap-3 mb-3">
          <div className="bg-gradient-to-br from-brand-700 to-brand-500 rounded-xl px-3 py-1.5 text-white font-black text-lg tracking-widest">
            KLA
          </div>
          <div>
            <div className="text-dark-50 font-bold text-sm leading-tight">Business Suite</div>
            <div className="text-dark-300 text-xs">PT KLA Teknologi Indonesia</div>
          </div>
        </div>
        {/* User info */}
        <div className="bg-dark-700 rounded-xl p-3 border border-dark-500">
          <div className="text-dark-50 font-semibold text-sm truncate">{user.full_name}</div>
          <div className="text-brand-400 text-xs mt-0.5">{user.role_label}</div>
          {user.branch_name && (
            <div className="text-dark-300 text-xs mt-0.5">📍 {user.branch_name}</div>
          )}
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-0.5">
        {visibleItems.map((item) => {
          const Icon = item.icon
          const active = router.pathname === item.href || router.pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group
                ${active
                  ? 'bg-brand-700/30 text-brand-300 border border-brand-600/30'
                  : 'text-dark-200 hover:bg-dark-600 hover:text-dark-50'
                }`}
            >
              <Icon size={16} className={active ? 'text-brand-400' : 'text-dark-300 group-hover:text-dark-100'} />
              <span className="truncate">{item.label}</span>
              {active && <ChevronRight size={14} className="ml-auto text-brand-500 shrink-0" />}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-dark-500">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-dark-300
                     hover:bg-red-950/40 hover:text-red-400 transition-all duration-150"
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>
        <div className="text-center text-dark-400 text-xs mt-3">
          Komplit · Nyaman · Bergaransi<br/>
          <span className="text-dark-500">© 2025 PT KLA Teknologi Indonesia</span>
        </div>
      </div>
    </aside>
  )
}
