import { useState } from 'react'
import { FileEdit } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../lib/api'
import type { AxiosError } from 'axios'

type Tab = 'login' | 'register'

export function AuthModal() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const [tab, setTab] = useState<Tab>('login')
  const [loading, setLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [error, setError] = useState('')

  // Form fields
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const resetForm = () => {
    setName('')
    setEmail('')
    setPassword('')
    setError('')
    setSuccessMsg('')
  }

  const switchTab = (t: Tab) => {
    setTab(t)
    resetForm()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMsg('')

    // Basic client-side validation
    if (!email.trim() || !password.trim()) {
      setError('Email and password are required.')
      return
    }
    if (tab === 'register' && !name.trim()) {
      setError('Name is required.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    try {
      if (tab === 'login') {
        const res = await authApi.login(email, password)
        const { access_token } = res.data

        // Parse JWT to get the user ID
        const payloadBase64 = access_token.split('.')[1]
        const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/')))
        const userId = decodedPayload.sub

        const user = {
           id: userId,
           name: email.split('@')[0], // Fallback name since backend doesn't provide it
           email: email
        }
        setAuth(access_token, user)
      } else {
        const res = await authApi.register(name, email, password)
        if (res.data.success === 'true') {
           setSuccessMsg(res.data.message || 'Registration successful. Please log in.')
           setTab('login')
           setPassword('')
           setName('')
        }
      }
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>
      const detail = axiosErr.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('Something went wrong. Is the backend running?')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-overlay">
      <div className="auth-card" role="dialog" aria-modal="true" aria-label="Sign in to CollabDocs">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">
            <FileEdit size={24} color="#fff" />
          </div>
          <h1 className="auth-title">CollabDocs</h1>
          <p className="auth-subtitle">Real-time collaborative editing</p>
        </div>

        {/* Tabs */}
        <div className="auth-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={tab === 'login'}
            className={`auth-tab ${tab === 'login' ? 'active' : ''}`}
            onClick={() => switchTab('login')}
            id="tab-login"
          >
            Sign In
          </button>
          <button
            role="tab"
            aria-selected={tab === 'register'}
            className={`auth-tab ${tab === 'register' ? 'active' : ''}`}
            onClick={() => switchTab('register')}
            id="tab-register"
          >
            Sign Up
          </button>
        </div>

        {/* Form */}
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {tab === 'register' && (
            <div className="form-group">
              <label className="form-label" htmlFor="auth-name">
                Display Name
              </label>
              <input
                id="auth-name"
                type="text"
                className="form-input"
                placeholder="Alice Smith"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                autoFocus
                disabled={loading}
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="auth-email">
              Email
            </label>
            <input
              id="auth-email"
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              autoFocus={tab === 'login'}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="auth-password">
              Password
            </label>
            <input
              id="auth-password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
              disabled={loading}
            />
          </div>

          {error && <div className="auth-error" role="alert">{error}</div>}
          {successMsg && <div className="auth-success" role="alert" style={{ color: 'green', marginBottom: '1rem', fontSize: '0.875rem' }}>{successMsg}</div>}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
            id={`auth-submit-${tab}`}
          >
            {loading ? (
              <>
                <span className="spinner" />
                {tab === 'login' ? 'Signing in…' : 'Creating account…'}
              </>
            ) : tab === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
