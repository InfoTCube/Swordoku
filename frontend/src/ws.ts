export type WsMessage = Record<string, unknown>

export interface WsHandlers {
  onMessage: (data: WsMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (event: Event) => void
}

export interface WsConnection {
  send: (data: WsMessage) => void
  close: () => void
}

export function connectToMatch(matchId: string, token: string, handlers: WsHandlers): WsConnection {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${protocol}://${location.host}/ws/match/${matchId}?token=${encodeURIComponent(token)}`
  const socket = new WebSocket(url)

  socket.onopen = () => handlers.onOpen?.()
  socket.onclose = () => handlers.onClose?.()
  socket.onerror = (e) => handlers.onError?.(e)
  socket.onmessage = (event) => {
    try {
      handlers.onMessage(JSON.parse(event.data))
    } catch {
      // ignore malformed messages
    }
  }

  return {
    send: (data) => socket.send(JSON.stringify(data)),
    close: () => socket.close(),
  }
}
