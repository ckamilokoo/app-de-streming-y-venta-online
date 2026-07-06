import type { ChatMsg, PinnedProduct } from '~/types'

const MAX_MESSAGES = 200

export function useStreamRoom(streamId: string) {
  const config = useRuntimeConfig()
  const { token } = useAuth()

  const messages = ref<ChatMsg[]>([])
  const pinned = ref<PinnedProduct | null>(null)
  const viewers = ref(0)
  const ended = ref(false)
  const connected = ref(false)
  const stockListeners: Array<(productId: string, stock: number) => void> = []

  let ws: WebSocket | null = null
  let backoff = 1000
  let closedByUs = false
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function wsUrl(): string {
    const base = config.public.apiBase.replace(/^http/, 'ws')
    return `${base}/api/streams/${streamId}/ws?token=${token.value ?? ''}`
  }

  function connect() {
    if (!token.value || ended.value || closedByUs) return
    ws = new WebSocket(wsUrl())

    ws.onopen = () => {
      connected.value = true
      backoff = 1000
      ws?.send(JSON.stringify({ t: 'sync' }))
    }

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      switch (msg.t) {
        case 'chat':
          messages.value.push(msg)
          if (messages.value.length > MAX_MESSAGES) {
            messages.value.splice(0, messages.value.length - MAX_MESSAGES)
          }
          break
        case 'pinned':
          pinned.value = msg.product
          break
        case 'viewers':
          viewers.value = msg.count
          break
        case 'stock':
          if (pinned.value?.id === msg.productId) pinned.value.stock = msg.stock
          stockListeners.forEach((fn) => fn(msg.productId, msg.stock))
          break
        case 'stream_ended':
          ended.value = true
          break
      }
    }

    ws.onclose = () => {
      connected.value = false
      if (closedByUs || ended.value) return
      // Reconexión exponencial 1s -> 30s
      reconnectTimer = setTimeout(connect, backoff)
      backoff = Math.min(backoff * 2, 30_000)
    }
  }

  function sendChat(text: string) {
    if (ws?.readyState === WebSocket.OPEN && text.trim()) {
      ws.send(JSON.stringify({ t: 'chat', text: text.trim().slice(0, 280) }))
    }
  }

  function onStock(fn: (productId: string, stock: number) => void) {
    stockListeners.push(fn)
  }

  function close() {
    closedByUs = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
  }

  onBeforeUnmount(close)

  return { messages, pinned, viewers, ended, connected, connect, sendChat, onStock, close }
}
