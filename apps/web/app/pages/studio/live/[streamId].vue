<script setup lang="ts">
import { clp, type Order, type Product, type Stream } from '~/types'

const route = useRoute()
const streamId = route.params.streamId as string
const { api } = useApi()
const { user, token, isStreamer } = useAuth()

const stream = ref<Stream | null>(null)
const myProducts = ref<Product[]>([])
const orders = ref<Order[]>([])
const videoEl = ref<HTMLVideoElement>()
const chatInput = ref('')
const busy = ref(false)

const room = useStreamRoom(streamId)
const cast = useWhipBroadcast()

const assigned = computed(() => stream.value?.products ?? [])
const unassigned = computed(() =>
  myProducts.value.filter((p) => !assigned.value.some((a) => a.id === p.id)),
)
const totalSales = computed(() =>
  orders.value.reduce((sum, o) => sum + o.amountClp, 0),
)

async function load() {
  stream.value = await api<Stream>(`/api/streams/${streamId}`)
  myProducts.value = await api<Product[]>('/api/products', { params: { mine: 1 } })
}

async function loadOrders() {
  if (stream.value?.status !== 'live') return
  orders.value = await api<Order[]>('/api/orders', { params: { stream_id: streamId } })
}

let ordersPoll: ReturnType<typeof setInterval>
onMounted(async () => {
  if (!token.value) return
  await load()
  room.connect()
  ordersPoll = setInterval(loadOrders, 5_000)
  // Stock en vivo sobre la lista asignada
  room.onStock((productId, stock) => {
    const p = assigned.value.find((x) => x.id === productId)
    if (p) p.stock = stock
    loadOrders()
  })
})
onBeforeUnmount(() => clearInterval(ordersPoll))

async function goLive() {
  if (!stream.value || !videoEl.value) return
  busy.value = true
  try {
    if (!cast.previewing.value) await cast.startPreview(videoEl.value)
    if (cast.error.value) return
    await cast.startBroadcast(stream.value.whipUrl!)
    if (cast.error.value) return
    await api(`/api/streams/${streamId}/start`, { method: 'POST' })
    stream.value.status = 'live'
    loadOrders()
  } finally {
    busy.value = false
  }
}

async function endStream() {
  if (!confirm('¿Terminar el stream? Esta acción cierra la sala para todos.')) return
  busy.value = true
  try {
    await api(`/api/streams/${streamId}/end`, { method: 'POST' })
    await cast.stopBroadcast()
    cast.stopPreview()
    if (stream.value) stream.value.status = 'ended'
  } finally {
    busy.value = false
  }
}

async function assign(productId: string) {
  await api(`/api/streams/${streamId}/products`, {
    method: 'POST',
    body: { product_ids: [productId] },
  })
  await load()
}

async function pin(productId: string | null) {
  await api(`/api/streams/${streamId}/pin`, {
    method: 'POST',
    body: { product_id: productId },
  })
}

function sendChat() {
  room.sendChat(chatInput.value)
  chatInput.value = ''
}
</script>

<template>
  <div class="container">
    <p v-if="!user || !isStreamer" class="muted">Requiere sesión de streamer.</p>

    <div v-else-if="stream" class="layout">
      <div class="main-col">
        <div class="row">
          <h2 style="flex:1">{{ stream.title }}</h2>
          <span class="badge" :class="{ live: stream.status === 'live' }">{{ stream.status }}</span>
          <span class="muted">👁 {{ room.viewers.value }}</span>
        </div>

        <!-- Preview + controles -->
        <div class="panel video-wrap">
          <video ref="videoEl" autoplay playsinline muted />
          <div v-if="!cast.previewing.value" class="video-overlay">
            <button class="primary" @click="cast.startPreview(videoEl!)">🎥 Iniciar cámara</button>
          </div>
        </div>
        <p v-if="cast.error.value" class="err-msg">{{ cast.error.value }}</p>
        <div class="row controls">
          <button
            v-if="stream.status !== 'live'"
            class="primary"
            :disabled="busy || stream.status === 'ended'"
            @click="goLive"
          >
            🔴 Salir en vivo
          </button>
          <template v-else>
            <span class="badge live">TRANSMITIENDO {{ cast.isMock.value ? '(mock)' : '' }}</span>
            <button class="danger" :disabled="busy" @click="endStream">Terminar stream</button>
          </template>
        </div>

        <!-- Productos del stream -->
        <section class="panel">
          <h3>Productos del stream</h3>
          <ul class="list">
            <li v-for="p in assigned" :key="p.id" class="row">
              <div style="flex:1">
                <strong>{{ p.name }}</strong>
                <span class="muted"> · {{ clp(p.priceClp) }} · stock {{ p.stock }}</span>
              </div>
              <button
                v-if="room.pinned.value?.id === p.id"
                class="danger"
                @click="pin(null)"
              >
                Quitar pin
              </button>
              <button v-else class="primary" @click="pin(p.id)">📌 Pin</button>
            </li>
            <li v-if="!assigned.length" class="muted">Sin productos asignados.</li>
          </ul>
          <template v-if="unassigned.length">
            <h4 class="muted">Agregar de mi catálogo</h4>
            <ul class="list">
              <li v-for="p in unassigned" :key="p.id" class="row">
                <span style="flex:1">{{ p.name }} <span class="muted">{{ clp(p.priceClp) }}</span></span>
                <button @click="assign(p.id)">＋ Asignar</button>
              </li>
            </ul>
          </template>
        </section>

        <!-- Ventas -->
        <section class="panel">
          <div class="row">
            <h3 style="flex:1">Ventas en vivo</h3>
            <strong>{{ clp(totalSales) }}</strong>
          </div>
          <ul class="list">
            <li v-for="o in orders" :key="o.id" class="row">
              <span style="flex:1">{{ o.buyerName }} compró {{ o.qty }}× {{ o.productName }}</span>
              <strong>{{ clp(o.amountClp) }}</strong>
            </li>
            <li v-if="!orders.length" class="muted">Todavía sin ventas.</li>
          </ul>
        </section>
      </div>

      <!-- Chat -->
      <aside class="panel chat">
        <h3>Chat</h3>
        <div class="chat-messages">
          <p v-for="(m, i) in room.messages.value" :key="i">
            <strong>{{ m.name }}:</strong> {{ m.text }}
          </p>
          <p v-if="!room.messages.value.length" class="muted">Sin mensajes aún.</p>
        </div>
        <form class="row" @submit.prevent="sendChat">
          <input v-model="chatInput" placeholder="Responder al chat" maxlength="280" style="flex:1" />
          <button type="submit" :disabled="!room.connected.value">Enviar</button>
        </form>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 1fr 300px; gap: 1rem; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.main-col { display: flex; flex-direction: column; gap: 1rem; }

.video-wrap { position: relative; padding: 0; overflow: hidden; aspect-ratio: 16/9; }
.video-wrap video { width: 100%; height: 100%; object-fit: contain; background: #000; }
.video-overlay {
  position: absolute; inset: 0; display: flex;
  align-items: center; justify-content: center; background: var(--panel-2);
}
.controls { margin-top: -.4rem; }
.err-msg { color: var(--live); margin: 0; }

.list { list-style: none; padding: 0; margin: .6rem 0 0; display: flex; flex-direction: column; gap: .5rem; }

.chat { display: flex; flex-direction: column; max-height: 80vh; position: sticky; top: 4.5rem; }
.chat-messages { flex: 1; overflow-y: auto; margin-bottom: .6rem; min-height: 200px; }
.chat-messages p { margin: .25rem 0; word-break: break-word; }
</style>
