/**
 * lib/auth.ts — Auth state helpers using cookies
 */
import Cookies from 'js-cookie'

const TOKEN_KEY = 'kla_token'
const USER_KEY  = 'kla_user'

export interface User {
  id: number
  username: string
  full_name: string
  role: string
  role_label: string
  branch?: string
  branch_name?: string
  area?: string
}

export const setAuth = (token: string, user: User) => {
  Cookies.set(TOKEN_KEY, token, { expires: 1, sameSite: 'lax' })
  Cookies.set(USER_KEY, JSON.stringify(user), { expires: 1, sameSite: 'lax' })
}

export const clearAuth = () => {
  Cookies.remove(TOKEN_KEY)
  Cookies.remove(USER_KEY)
}

export const getToken = (): string | undefined => Cookies.get(TOKEN_KEY)

export const getUser = (): User | null => {
  const raw = Cookies.get(USER_KEY)
  if (!raw) return null
  try { return JSON.parse(raw) } catch { return null }
}

export const isLoggedIn = (): boolean => !!getToken() && !!getUser()

export const hasRole = (user: User | null, ...roles: string[]): boolean =>
  !!user && roles.includes(user.role)

export const ROLES = {
  SUPER_ADMIN:  'super_admin',
  AREA_MANAGER: 'area_manager',
  STORE_LEADER: 'store_leader',
  SALES:        'sales',
}
