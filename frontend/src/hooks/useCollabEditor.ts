import { useEditor } from '@tiptap/react'
import { useEffect, useRef, useState } from 'react'
import { authApi } from '../lib/api'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { IndexeddbPersistence } from 'y-indexeddb'
import StarterKit from '@tiptap/starter-kit'
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'
import Underline from '@tiptap/extension-underline'
import Highlight from '@tiptap/extension-highlight'
import TextAlign from '@tiptap/extension-text-align'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import type { User, OnlineUser, WsStatus } from '../types'
import { getUserColor } from '../lib/colors'

// ── Constants ─────────────────────────────────────────────────────────────────
const DOC_ID = import.meta.env.VITE_DOC_ID || 'shared-doc'
// WS URL: during dev, Vite proxies /ws → ws://localhost:8000/ws (see vite.config.ts)
// The WebsocketProvider appends: /{DOC_ID}?token={jwt}
const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`

// ── Hook ──────────────────────────────────────────────────────────────────────
/**
 * useCollabEditor — sets up the full real-time collab stack:
 *   1. Y.Doc         — the CRDT document
 *   2. WebsocketProvider  — syncs with the Python backend via WS (JWT in query param)
 *   3. IndexeddbPersistence — offline editing & fast page load from local cache
 *   4. Tiptap editor — rich text editing layer on top of Yjs
 *
 * Returns: { editor, wsStatus, onlineUsers }
 *
 * FastAPI WebSocket endpoint format expected:
 *   ws://{host}/ws/{doc_id}?token={jwt}
 */
export function useCollabEditor(token: string, user: User) {
  const [wsStatus, setWsStatus] = useState<WsStatus>('connecting')
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([])

  // ── Yjs initialisation (synchronous, once) ────────────────────────────────
  // We use refs with lazy init so these are created on first render and
  // available synchronously for useEditor below. Cleanup happens in useEffect.
  const ydocRef = useRef<Y.Doc | null>(null)
  const wsProviderRef = useRef<WebsocketProvider | null>(null)
  const idbProviderRef = useRef<IndexeddbPersistence | null>(null)

  if (!ydocRef.current) {
    const ydoc = new Y.Doc()

    // WebSocket provider — starts disconnected, waits for ticket
    const wsProvider = new WebsocketProvider(WS_URL, DOC_ID, ydoc, {
      connect: false,
    })

    // Prevent reconnection loop if unauthorized
    wsProvider.on('connection-close', (event: CloseEvent | null) => {
      if (event === null) return;
      if (event.code === 4001) {
        console.error('WebSocket unauthorized:', event.reason)
        wsProvider.shouldConnect = false
      }
    })

    // IndexedDB provider — persists doc state in the browser for offline use
    const idbProvider = new IndexeddbPersistence(`collab-docs:${DOC_ID}`, ydoc)

    ydocRef.current = ydoc
    wsProviderRef.current = wsProvider
    idbProviderRef.current = idbProvider
  }

  const ydoc = ydocRef.current!
  const wsProvider = wsProviderRef.current!

  // ── Fetch WS ticket and connect ───────────────────────────────────────────
  useEffect(() => {
    let active = true

    async function fetchTicket() {
      try {
        const res = await authApi.getWsTicket(DOC_ID)
        if (active && wsProviderRef.current) {
          wsProviderRef.current.params = { ticket: res.data.ticket }
          wsProviderRef.current.connect()
        }
      } catch (err) {
        console.error('Failed to get WS ticket', err)
        if (active) {
          setWsStatus('disconnected')
        }
      }
    }

    fetchTicket()

    return () => {
      active = false
    }
  }, [token])

  // ── Cleanup on unmount ────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      wsProviderRef.current?.destroy()
      idbProviderRef.current?.destroy()
      ydocRef.current?.destroy()
      wsProviderRef.current = null
      idbProviderRef.current = null
      ydocRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Track WebSocket connection status ─────────────────────────────────────
  useEffect(() => {
    const handler = ({ status }: { status: string }) => {
      setWsStatus(status as WsStatus)
    }
    wsProvider.on('status', handler)
    return () => { wsProvider.off('status', handler) }
  }, [wsProvider])

  // ── Set own Awareness state (name + cursor color) ─────────────────────────
  useEffect(() => {
    wsProvider.awareness.setLocalStateField('user', {
      name: user.name,
      color: getUserColor(user.id),
    })
  }, [wsProvider, user])

  // ── Track online users from Awareness ─────────────────────────────────────
  useEffect(() => {
    const updateUsers = () => {
      const users: OnlineUser[] = []
      wsProvider.awareness.getStates().forEach((state, clientId) => {
        // Exclude our own cursor from the presence list
        if (state.user && clientId !== wsProvider.awareness.clientID) {
          users.push({ clientId, name: state.user.name, color: state.user.color })
        }
      })
      setOnlineUsers(users)
    }
    wsProvider.awareness.on('change', updateUsers)
    updateUsers() // populate immediately
    return () => { wsProvider.awareness.off('change', updateUsers) }
  }, [wsProvider])

  // ── Tiptap editor ─────────────────────────────────────────────────────────
  const editor = useEditor({
    extensions: [
      // history: false — Yjs provides its own undo/redo (CRDT-aware)
      StarterKit.configure({ history: false }),

      // Connect Tiptap to the Yjs document
      Collaboration.configure({ document: ydoc }),

      // Render other users' cursors via Yjs Awareness
      CollaborationCursor.configure({
        provider: wsProvider,
        user: { name: user.name, color: getUserColor(user.id) },
      }),

      Underline,
      Highlight.configure({ multicolor: true }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: { rel: 'noopener noreferrer', target: '_blank' },
      }),
      Placeholder.configure({
        placeholder: 'Start writing… your thoughts deserve a home.',
      }),
      TaskList,
      TaskItem.configure({ nested: true }),
    ],
    editorProps: {
      attributes: {
        class: 'prose-editor',
        spellcheck: 'true',
      },
    },
  })

  return { editor, wsStatus, onlineUsers }
}
