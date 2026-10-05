import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'

interface AuthState {
  token: string | null
  user: User | null
  /** Called after a successful login or register */
  setAuth: (token: string, user: User) => void
  /** Clears all auth state (logout) */
  logout: () => void
}

/**
 * Global auth store.
 * Persisted to localStorage under the key 'collab-docs-auth'.
 * On page reload, the token & user are rehydrated automatically.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'collab-docs-auth' },
  ),
)
