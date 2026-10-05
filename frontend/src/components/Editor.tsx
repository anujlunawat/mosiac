import { EditorContent } from '@tiptap/react'
import type { User } from '../types'
import { useCollabEditor } from '../hooks/useCollabEditor'
import { useAuthStore } from '../store/authStore'
import { Header } from './Header'
import { Toolbar } from './Toolbar'
import { authApi } from '../lib/api'

interface Props {
  token: string
  user: User
}

/**
 * Editor — the main view after authentication.
 *
 * Wires together:
 *   Header (presence, status, logout)
 *   Toolbar (formatting buttons)
 *   EditorContent (Tiptap + Yjs CRDT)
 *
 * The useCollabEditor hook owns all Yjs/WebSocket lifecycle.
 */

export function Editor({ token, user }: Props) {
  const storeLogout = useAuthStore((s) => s.logout)
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (err) {
      console.error('Logout failed on backend:', err)
    } finally {
      storeLogout()
    }
  }
  const { editor, wsStatus, onlineUsers } = useCollabEditor(token, user)

  // Show a loading state while Tiptap initialises
  if (!editor) {
    return (
      <div className="app-layout">
        <Header
          user={user}
          wsStatus="connecting"
          onlineUsers={[]}
          onLogout={logout}
        />
        <div className="editor-loading" aria-live="polite">
          <span className="spinner" />
          Loading document…
        </div>
      </div>
    )
  }

  return (
    <div className="app-layout">
      <Header
        user={user}
        wsStatus={wsStatus}
        onlineUsers={onlineUsers}
        onLogout={logout}
      />
      <Toolbar editor={editor} />

      <main className="editor-wrapper" id="editor-main">
        <div className="editor-content-area fade-in">
          {/*
            EditorContent renders the contenteditable div.
            Tiptap applies collaboration cursors, Yjs sync, and all
            extensions configured in useCollabEditor automatically.
          */}
          <EditorContent editor={editor} />
        </div>
      </main>
    </div>
  )
}
