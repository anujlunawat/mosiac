import axios from 'axios'
import { useAuthStore } from '../store/authStore'
// import type { AuthResponse } from '../types'

// ── Axios instance ────────────────────────────────────────────────────────────
// VITE_API_URL should be set in your .env file.
// During dev, Vite proxies /api → http://localhost:8000/api (see vite.config.ts),
// so you can also leave VITE_API_URL unset and use relative URLs.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT Bearer token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-logout on 401 (token expired / invalid)
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config
    // If 401 and not already retrying, and not the refresh endpoint itself
    if (
      err.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== '/auth/refresh'
    ) {
      originalRequest._retry = true
      try {
        const res = await authApi.refresh()
        const new_token = res.data.access_token
        const currentUser = useAuthStore.getState().user
        if (currentUser) {
          useAuthStore.getState().setAuth(new_token, currentUser)
        }
        originalRequest.headers.Authorization = `Bearer ${new_token}`
        return api(originalRequest)
      } catch (refreshErr) {
        useAuthStore.getState().logout()
        return Promise.reject(refreshErr)
      }
    } else if (err.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(err)
  },
)

// ── Auth endpoints ────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string; expires_in: number }>('/auth/login', { email, password }),

  register: (name: string, email: string, password: string) =>
    api.post<{ success: string; message: string }>('/auth/register', { name, email, password }),

  refresh: () =>
    api.post<{ access_token: string; token_type: string; expires_in: number }>('/auth/refresh'),

  logout: () =>
    api.post('/auth/logout'),

  getWsTicket: (docId: string) =>
    api.post<{ ticket: string; expires_in: number }>('/auth/ws-ticket', { doc_id: docId }),
}

export default api
