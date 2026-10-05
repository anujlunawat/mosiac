// Shared TypeScript types across the frontend

export interface User {
  id: string
  name: string
  email: string
}

/** A user currently online in the document (from Yjs Awareness) */
export interface OnlineUser {
  clientId: number
  name: string
  color: string
}

/** WebSocket connection state */
export type WsStatus = 'connecting' | 'connected' | 'disconnected'

/** Auth API response shape — must match your FastAPI response */
export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}
