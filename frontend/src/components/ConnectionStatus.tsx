import type { WsStatus } from '../types'

interface Props {
  status: WsStatus
}

const CONFIG: Record<WsStatus, { label: string; cls: string }> = {
  connected:    { label: 'Live',         cls: 'connected'    },
  connecting:   { label: 'Connecting…',  cls: 'connecting'   },
  disconnected: { label: 'Offline',      cls: 'disconnected' },
}

export function ConnectionStatus({ status }: Props) {
  const { label, cls } = CONFIG[status]
  return (
    <div className="conn-status" title={`WebSocket: ${status}`}>
      <span className={`conn-dot ${cls}`} />
      {label}
    </div>
  )
}
