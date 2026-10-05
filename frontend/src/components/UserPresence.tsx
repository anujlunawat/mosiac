import type { OnlineUser } from '../types'
import { getInitials } from '../lib/colors'

interface Props {
  users: OnlineUser[]
  currentUserName: string
  currentUserColor: string
}

const MAX_VISIBLE = 4

export function UserPresence({ users, currentUserName, currentUserColor }: Props) {
  const visible = users.slice(0, MAX_VISIBLE)
  const overflow = users.length - MAX_VISIBLE

  return (
    <div className="presence" aria-label="Online collaborators">
      {/* Current user (always first) */}
      <div
        className="presence-avatar"
        style={{ backgroundColor: currentUserColor }}
        title={`${currentUserName} (you)`}
      >
        {getInitials(currentUserName)}
        <span className="presence-tooltip">{currentUserName} (you)</span>
      </div>

      {/* Other online users */}
      {visible.map((u) => (
        <div
          key={u.clientId}
          className="presence-avatar"
          style={{ backgroundColor: u.color }}
        >
          {getInitials(u.name)}
          <span className="presence-tooltip">{u.name}</span>
        </div>
      ))}

      {/* Overflow count */}
      {overflow > 0 && (
        <div className="presence-count" title={`${overflow} more users`}>
          +{overflow}
        </div>
      )}
    </div>
  )
}
