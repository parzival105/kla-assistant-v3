import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Layout from '@/components/layout/Layout'
import { authApi } from '@/lib/api'
import { RoleBadge } from '@/components/ui/Badge'
import { PageLoading } from '@/components/ui/Loading'
import KpiCard from '@/components/ui/KpiCard'
import { formatNumber } from '@/lib/format'
import toast from 'react-hot-toast'
import { UserPlus, Pencil, Trash2, X, Check } from 'lucide-react'

export default function UsersPage() {
  const qc = useQueryClient()
  const usersQ  = useQuery({ queryKey:['users'], queryFn: () => authApi.getUsers() })
  const metaQ   = useQuery({ queryKey:['meta'],  queryFn: () => authApi.getMeta() })
  const users   = usersQ.data?.data?.users ?? []
  const branches = metaQ.data?.data?.branches ?? []
  const areas    = metaQ.data?.data?.areas ?? []
  const roles    = metaQ.data?.data?.roles ?? []

  const [tab, setTab] = useState<'list'|'create'|'edit'>('list')
  const [editUser, setEditUser] = useState<any>(null)
  const [form, setForm] = useState({ username:'',password:'',password2:'',full_name:'',role:'sales',branch:'',area:'',is_active:true,new_password:'' })

  const active   = users.filter((u:any) => u.is_active)
  const inactive = users.filter((u:any) => !u.is_active)

  const createMut = useMutation({
    mutationFn: (data:any) => authApi.createUser(data),
    onSuccess: () => { toast.success('User berhasil dibuat'); qc.invalidateQueries({queryKey:['users']}); setTab('list') },
    onError: (e:any) => toast.error(e.response?.data?.detail || 'Gagal membuat user'),
  })
  const updateMut = useMutation({
    mutationFn: ({id,data}:{id:number,data:any}) => authApi.updateUser(id, data),
    onSuccess: () => { toast.success('User berhasil diupdate'); qc.invalidateQueries({queryKey:['users']}); setTab('list') },
    onError: (e:any) => toast.error(e.response?.data?.detail || 'Gagal update user'),
  })
  const deleteMut = useMutation({
    mutationFn: (id:number) => authApi.deleteUser(id),
    onSuccess: () => { toast.success('User dinonaktifkan'); qc.invalidateQueries({queryKey:['users']}) },
    onError: (e:any) => toast.error(e.response?.data?.detail || 'Gagal'),
  })

  const handleCreate = (e:any) => {
    e.preventDefault()
    if (form.password !== form.password2) { toast.error('Password tidak cocok'); return }
    if (form.password.length < 6) { toast.error('Password minimal 6 karakter'); return }
    createMut.mutate({ username:form.username, password:form.password, full_name:form.full_name, role:form.role, branch:form.branch||null, area:form.area||null })
  }
  const handleEdit = (e:any) => {
    e.preventDefault()
    updateMut.mutate({ id:editUser.id, data:{ full_name:form.full_name, role:form.role, branch:form.branch||null, area:form.area||null, is_active:form.is_active, new_password:form.new_password||null } })
  }

  const needsBranch = (role:string) => ['store_leader','sales'].includes(role)
  const needsArea   = (role:string) => role === 'area_manager'

  if (usersQ.isLoading) return <Layout title="User Management"><PageLoading/></Layout>

  return (
    <Layout title="👥 User Management">
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Aktif"   value={formatNumber(active.length)}                                            color="purple"/>
        <KpiCard label="Admin"         value={formatNumber(active.filter((u:any)=>u.role==='super_admin').length)}   color="red"/>
        <KpiCard label="Store Leader"  value={formatNumber(active.filter((u:any)=>u.role==='store_leader').length)}  color="green"/>
        <KpiCard label="Sales"         value={formatNumber(active.filter((u:any)=>u.role==='sales').length)}          color="orange"/>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {(['list','create'] as const).map(t => (
          <button key={t} onClick={()=>setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab===t ? 'bg-brand-700 text-white' : 'bg-dark-700 text-dark-200 hover:bg-dark-600'}`}>
            {t === 'list' ? '📋 Daftar User' : '➕ Buat User Baru'}
          </button>
        ))}
      </div>

      {/* List */}
      {tab === 'list' && (
        <div className="space-y-3">
          {active.map((u:any) => (
            <div key={u.id} className="card flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-dark-50 font-semibold">{u.full_name}</span>
                  <span className="text-dark-300 text-sm">@{u.username}</span>
                  <RoleBadge role={u.role} label={u.role_label||u.role}/>
                </div>
                <div className="text-dark-300 text-xs mt-1">
                  {u.branch_name && `📍 ${u.branch_name} (${u.branch})`}
                  {u.area && `🗺️ ${u.area}`}
                  {u.last_login ? ` · Login terakhir: ${u.last_login?.slice(0,16)}` : ' · Belum pernah login'}
                </div>
              </div>
              {u.username !== 'admin' && (
                <div className="flex gap-2 shrink-0">
                  <button onClick={()=>{ setEditUser(u); setForm({...form,full_name:u.full_name,role:u.role,branch:u.branch||'',area:u.area||'',is_active:true,new_password:'',username:'',password:'',password2:''}); setTab('edit') }}
                    className="p-2 rounded-lg bg-dark-600 hover:bg-brand-700/30 text-dark-200 hover:text-brand-300 transition-all">
                    <Pencil size={14}/>
                  </button>
                  <button onClick={()=>{ if(confirm(`Nonaktifkan @${u.username}?`)) deleteMut.mutate(u.id) }}
                    className="p-2 rounded-lg bg-dark-600 hover:bg-red-900/30 text-dark-200 hover:text-red-400 transition-all">
                    <Trash2 size={14}/>
                  </button>
                </div>
              )}
            </div>
          ))}
          {inactive.length > 0 && (
            <div className="card opacity-50">
              <p className="text-dark-300 text-sm font-medium mb-2">User Nonaktif:</p>
              {inactive.map((u:any) => <p key={u.id} className="text-dark-400 text-sm line-through">@{u.username} — {u.full_name}</p>)}
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Form */}
      {(tab === 'create' || tab === 'edit') && (
        <div className="card max-w-xl">
          <h3 className="text-dark-50 font-bold mb-5">{tab==='create' ? 'Buat Akun Baru' : `Edit: ${editUser?.full_name}`}</h3>
          <form onSubmit={tab==='create' ? handleCreate : handleEdit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-dark-200 text-sm font-medium mb-1.5">Nama Lengkap *</label>
                <input className="input" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} required/>
              </div>
              {tab === 'create' && (
                <div>
                  <label className="block text-dark-200 text-sm font-medium mb-1.5">Username *</label>
                  <input className="input" value={form.username} onChange={e=>setForm({...form,username:e.target.value.toLowerCase()})} required/>
                </div>
              )}
            </div>
            {tab === 'create' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-dark-200 text-sm font-medium mb-1.5">Password *</label>
                  <input className="input" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required/>
                </div>
                <div>
                  <label className="block text-dark-200 text-sm font-medium mb-1.5">Konfirmasi Password *</label>
                  <input className="input" type="password" value={form.password2} onChange={e=>setForm({...form,password2:e.target.value})} required/>
                </div>
              </div>
            )}
            {tab === 'edit' && (
              <div>
                <label className="block text-dark-200 text-sm font-medium mb-1.5">Password Baru (kosongkan jika tidak diubah)</label>
                <input className="input" type="password" value={form.new_password} onChange={e=>setForm({...form,new_password:e.target.value})}/>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-dark-200 text-sm font-medium mb-1.5">Role *</label>
                <select className="input" value={form.role} onChange={e=>setForm({...form,role:e.target.value,branch:'',area:''})}>
                  {roles.map((r:any) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              {needsBranch(form.role) && (
                <div>
                  <label className="block text-dark-200 text-sm font-medium mb-1.5">Cabang *</label>
                  <select className="input" value={form.branch} onChange={e=>setForm({...form,branch:e.target.value})} required>
                    <option value="">Pilih cabang...</option>
                    {branches.map((b:any) => <option key={b.code} value={b.code}>{b.code} — {b.name}</option>)}
                  </select>
                </div>
              )}
              {needsArea(form.role) && (
                <div>
                  <label className="block text-dark-200 text-sm font-medium mb-1.5">Area *</label>
                  <select className="input" value={form.area} onChange={e=>setForm({...form,area:e.target.value})} required>
                    <option value="">Pilih area...</option>
                    {areas.map((a:string) => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
              )}
            </div>
            {tab === 'edit' && (
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.is_active} onChange={e=>setForm({...form,is_active:e.target.checked})} className="w-4 h-4 accent-brand-500"/>
                <span className="text-dark-200 text-sm">User aktif</span>
              </label>
            )}
            <div className="flex gap-3 pt-2">
              <button type="submit" className="btn-primary flex items-center gap-2" disabled={createMut.isPending || updateMut.isPending}>
                <Check size={16}/> {tab==='create' ? 'Buat User' : 'Simpan'}
              </button>
              <button type="button" onClick={()=>setTab('list')} className="btn-secondary flex items-center gap-2">
                <X size={16}/> Batal
              </button>
            </div>
          </form>
        </div>
      )}
    </Layout>
  )
}
