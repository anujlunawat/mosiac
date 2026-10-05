import { FileEdit, LogOut, User as UserIcon } from 'lucide-react'
import type { User, OnlineUser, WsStatus } from '../types'
import { getUserColor } from '../lib/colors'
import { UserPresence } from './UserPresence'
import { ConnectionStatus } from './ConnectionStatus'

interface Props {
  user: User
  wsStatus: WsStatus
  onlineUsers: OnlineUser[]
  onLogout: () => void
}

export function Header({ user, wsStatus, onlineUsers, onLogout }: Props) {
  return (
    <header className="header" role="banner">
      {/* Left: logo + doc title */}
      <div className="header-left">
        <div className="logo">
          <div className="logo-icon" aria-hidden="true">
            <FileEdit size={16} color="#fff" />
          </div>
          <span className="logo-text">CollabDocs</span>
        </div>
        <div className="header-divider" aria-hidden="true" />
        <span className="doc-title">Shared Document</span>
      </div>

      {/* Right: presence + status + user + logout */}
      <div className="header-right">
        <UserPresence
          users={onlineUsers}
          currentUserName={user.name}
          currentUserColor={getUserColor(user.id)}
        />
        <ConnectionStatus status={wsStatus} />
        <div className="user-menu" aria-label={`Logged in as ${user.name}`}>
          <UserIcon size={13} color="var(--accent-light)" />
          <span className="user-name">{user.name}</span>
        </div>
        <button
          id="btn-logout"
          className="logout-btn"
          onClick={onLogout}
          title="Sign out"
          aria-label="Sign out"
          type="button"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}
