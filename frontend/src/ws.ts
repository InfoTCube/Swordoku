export type WsMessage = Record<string, unknown>

export interface WsHandlers {
  onMessage: (data: WsMessage) => void
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
}

export interface WsConnection {
  send: (data: WsMessage) => void
  close: () => void
}

export function connectToMatch(matchId: string, token: string, handlers: WsHandlers): WsConnection {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${protocol}://${location.host}/ws/match/${matchId}`
  const socket = new WebSocket(url)

  socket.onopen = () => {
    // Send auth as first message so the token never appears in server access logs or URLs
    socket.send(JSON.stringify({ type: 'auth', token }))
    handlers.onOpen?.()
  }
  socket.onclose = (e) => handlers.onClose?.(e)
  socket.onerror = (e) => handlers.onError?.(e)
  socket.onmessage = (event) => {
    try {
      handlers.onMessage(JSON.parse(event.data))
    } catch {
      // ignore malformed messages
    }
  }

  return {
    send: (data) => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data))
      }
    },
    close: () => socket.close(),
  }
}
