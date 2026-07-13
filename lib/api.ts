/**
 * lib/api.ts — Axios API client with auth token injection
 */
import axios from 'axios'
import Cookies from 'js-cookie'

// Default kosong = path relatif (same-origin), jadi API dipanggil di domain yang
// sama dengan frontend. Set NEXT_PUBLIC_API_URL hanya kalau API di host berbeda.
const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Inject auth token on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get('kla_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      Cookies.remove('kla_token')
      Cookies.remove('kla_user')
      if (typeof window !== 'undefined') window.location.href = '/auth/login'
    }
    return Promise.reject(err)
  }
)

export default api

// Auth
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/api/auth/login', { username, password }),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
  getUsers: () => api.get('/api/auth/users'),
  getMeta: () => api.get('/api/auth/meta'),
  createUser: (data: any) => api.post('/api/auth/users', data),
  updateUser: (id: number, data: any) => api.put(`/api/auth/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/api/auth/users/${id}`),
}

// Inventory
export const inventoryApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/api/inventory/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  status: () => api.get('/api/inventory/status'),
  summary: () => api.get('/api/inventory/summary'),
  products: (params?: any) => api.get('/api/inventory/products', { params }),
  deadStock: () => api.get('/api/inventory/dead-stock'),
  restock: () => api.get('/api/inventory/restock'),
  transfer: () => api.get('/api/inventory/transfer'),
  recommendations: () => api.get('/api/inventory/recommendations'),
  pricing: () => api.get('/api/inventory/pricing'),
}

// Branch
export const branchApi = {
  summary: () => api.get('/api/branch/summary'),
  detail: (branch: string) => api.get(`/api/branch/detail/${branch}`),
  areaCompare: (area: string) => api.get(`/api/branch/area-compare/${encodeURIComponent(area)}`),
}

// PC Builder
export const pcBuilderApi = {
  config: () => api.get('/api/pc-builder/config'),
  build: (data: any) => api.post('/api/pc-builder/build', data),
  alternatives: (data: any) => api.post('/api/pc-builder/alternatives', data),
  save: (data: any) => api.post('/api/pc-builder/save', data),
  history: () => api.get('/api/pc-builder/history'),
}

// Sales Assistant
export const salesApi = {
  query: (query: string, top_n = 8) =>
    api.post('/api/sales/query', { query, top_n }),
}

// Export
export const exportApi = {
  excel: () => api.get('/api/export/excel', { responseType: 'blob' }),
}
