<script setup lang="ts">
import { clp, type Order, type Product, type Stream } from '~/types'

const route = useRoute()
const router = useRouter()
const streamId = route.params.streamId as string
const { api, assetUrl } = useApi()
const { user, token, isStreamer } = useAuth()

const stream = ref<Stream | null>(null)
const myProducts = ref<Product[]>([])
const orders = ref<Order[]>([])
const videoEl = ref<HTMLVideoElement>()
const busy = ref(false)
const now = ref(Date.now())

const room = useStreamRoom(streamId)
const cast = useWhipBroadcast()

const assigned = computed(() => stream.value?.products ?? [])
const unassigned = computed(() =>
  myProducts.value.filter((p) => !assigned.value.some((a) => a.id === p.id)),
)
const totalSales = computed(() => orders.value.reduce((s, o) => s + o.amountClp, 0))

// Ventas agrupadas por producto
const salesByProduct = computed(() => {
  const map = new Map<string, { name: string; units: number; total: number }>()
  for (const o of orders.value) {
    const e = map.get(o.productId) ?? { name: o.productName ?? '?', units: 0, total: 0 }
    e.units += o.qty
    e.total += o.amountClp
    map.set(o.productId, e)
  }
  return [...map.values()].sort((a, b) => b.total - a.total)
})

// Timer en vivo
const liveFor = computed(() => {
  if (stream.value?.status !== 'live' || !stream.value.startedAt) return ''
  const sec = Math.max(0, Math.floor(now.value / 1000) - stream.value.startedAt)
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60
  const mm = String(m).padStart(2, '0'), ss = String(s).padStart(2, '0')
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
})

async function load() {
  stream.value = await api<Stream>(`/api/streams/${streamId}`)
  myProducts.value = await api<Product[]>('/api/products', { params: { mine: 1 } })
}

async function loadOrders() {
  if (stream.value?.status !== 'live') return
  orders.value = await api<Order[]>('/api/orders', { params: { stream_id: streamId } })
}

let ordersPoll: ReturnType<typeof setInterval>
let clock: ReturnType<typeof setInterval>
onMounted(async () => {
  if (!token.value) return
  await load()
  room.connect()
  ordersPoll = setInterval(loadOrders, 5_000)
  clock = setInterval(() => { now.value = Date.now() }, 1000)
  room.onStock((productId, stock) => {
    const p = assigned.value.find((x) => x.id === productId)
    if (p) p.stock = stock
    loadOrders()
  })
})
onBeforeUnmount(() => { clearInterval(ordersPoll); clearInterval(clock) })

async function goLive() {
  if (!stream.value || !videoEl.value) return
  busy.value = true
  try {
    if (!cast.previewing.value) await cast.startPreview(videoEl.value)
    if (cast.error.value) return
    await cast.startBroadcast(stream.value.whipUrl!)
    if (cast.error.value) return
    await api(`/api/streams/${streamId}/start`, { method: 'POST' })
    await load()
    loadOrders()
  } finally {
    busy.value = false
  }
}

async function endStream() {
  if (!confirm('¿Terminar el stream? Se cierra la sala para todos los viewers.')) return
  busy.value = true
  try {
    await api(`/api/streams/${streamId}/end`, { method: 'POST' })
    await cast.stopBroadcast()
    cast.stopPreview()
    router.push(`/studio/summary/${streamId}`)
  } finally {
    busy.value = false
  }
}

async function assign(productId: string) {
  await api(`/api/streams/${streamId}/products`, {
    method: 'POST', body: { product_ids: [productId] },
  })
  await load()
}

async function unassign(productId: string) {
  await api(`/api/streams/${streamId}/products/${productId}`, { method: 'DELETE' })
  await load()
}

async function pin(productId: string | null) {
  await api(`/api/streams/${streamId}/pin`, {
    method: 'POST', body: { product_id: productId },
  })
}

async function bumpStock(p: Product, delta: number) {
  const next = Math.max(0, p.stock + delta)
  await api(`/api/products/${p.id}`, { method: 'PATCH', body: { stock: next } })
  p.stock = next
}
</script>

<template>
  <div class="container">
    <p v-if="!user || !isStreamer" class="muted">
      Requiere sesión de streamer — <NuxtLink to="/studio" style="text-decoration:underline">ir al Studio</NuxtLink>.
    </p>

    <div v-else-if="stream">
      <!-- Header consola -->
      <div class="row console-head">
        <NuxtLink to="/studio" class="muted">← Studio</NuxtLink>
        <h2 style="margin:0; flex:1">{{ stream.title }}</h2>
        <span v-if="stream.status === 'live'" class="badge live">EN VIVO {{ liveFor }}</span>
        <span v-else class="badge">{{ stream.status }}</span>
        <span class="badge">👁 {{ room.viewers.value }}</span>
      </div>

      <div class="layout">
        <!-- Zona 1: video + control -->
        <div class="zone video-zone">
          <div class="panel video-wrap">
            <video ref="videoEl" autoplay playsinline muted />
            <div v-if="!cast.previewing.value" class="video-overlay">
              <button class="primary" @click="cast.startPreview(videoEl!)">🎥 Iniciar cámara</button>
            </div>
            <ReactionOverlay :reactions="room.reactions.value" :can-react="false" />
          </div>
          <p v-if="cast.error.value" class="err-msg">{{ cast.error.value }}</p>
          <div class="row">
            <button
              v-if="stream.status !== 'live'"
              class="buy go-live"
              :disabled="busy || stream.status === 'ended'"
              @click="goLive"
            >🔴 Salir en vivo</button>
            <template v-else>
              <span class="badge live">TRANSMITIENDO {{ cast.isMock.value ? '(mock)' : '' }}</span>
              <button class="danger" :disabled="busy" @click="endStream">Terminar stream</button>
            </template>
          </div>

          <!-- Ventas -->
          <section class="panel">
            <div class="row" style="justify-content:space-between">
              <h3 style="margin:0">💰 Ventas</h3>
              <strong class="total">{{ clp(totalSales) }}</strong>
            </div>
            <table v-if="salesByProduct.length" class="sales-table">
              <tbody>
                <tr v-for="s in salesByProduct" :key="s.name">
                  <td>{{ s.name }}</td>
                  <td class="muted">{{ s.units }} uds</td>
                  <td class="amount">{{ clp(s.total) }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="muted" style="margin:.5rem 0 0">Todavía sin ventas.</p>
            <ul v-if="orders.length" class="feed">
              <li v-for="o in orders.slice(0, 6)" :key="o.id">
                🛒 {{ o.buyerName }} — {{ o.qty }}× {{ o.productName }}
              </li>
            </ul>
          </section>
        </div>

        <!-- Zona 2: productos -->
        <div class="zone">
          <section class="panel">
            <h3>Productos del stream</h3>
            <ul class="list">
              <li v-for="p in assigned" :key="p.id" class="prod">
                <div class="row">
                  <img v-if="p.imageUrl" :src="assetUrl(p.imageUrl) ?? undefined" class="thumb" alt="" />
                  <div v-else class="thumb placeholder">📦</div>
                  <div style="flex:1; min-width:0">
                    <strong class="pname">{{ p.name }}</strong>
                    <div class="muted psub">{{ clp(p.priceClp) }}</div>
                  </div>
                </div>
                <div class="row actions">
                  <div class="stepper" title="Stock en caliente">
                    <button @click="bumpStock(p, -1)" :disabled="p.stock <= 0">−</button>
                    <span class="stock" :class="{ zero: p.stock === 0 }">{{ p.stock }}</span>
                    <button @click="bumpStock(p, 1)">＋</button>
                  </div>
                  <button
                    v-if="room.pinned.value?.id === p.id"
                    class="danger pin-btn"
                    @click="pin(null)"
                  >Quitar pin</button>
                  <button v-else class="primary pin-btn" @click="pin(p.id)">📌 Pin</button>
                  <button class="ghost" title="Quitar del stream" @click="unassign(p.id)">✕</button>
                </div>
              </li>
              <li v-if="!assigned.length" class="muted">Sin productos asignados.</li>
            </ul>

            <template v-if="unassigned.length">
              <h4 class="muted" style="margin-top:1rem">Agregar de mi catálogo</h4>
              <ul class="list">
                <li v-for="p in unassigned" :key="p.id" class="row">
                  <span style="flex:1" class="pname">{{ p.name }} <span class="muted">{{ clp(p.priceClp) }}</span></span>
                  <button @click="assign(p.id)">＋ Asignar</button>
                </li>
              </ul>
            </template>
          </section>
        </div>

        <!-- Zona 3: chat -->
        <div class="zone chat-zone">
          <ChatPanel
            :messages="room.messages.value"
            :connected="room.connected.value"
            :can-write="true"
            placeholder="Responder al chat"
            @send="room.sendChat"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.console-head { margin-bottom: 1rem; }
.layout {
  display: grid;
  grid-template-columns: 1.25fr 1fr .95fr;
  gap: 1rem;
  align-items: start;
}
@media (max-width: 1100px) { .layout { grid-template-columns: 1fr 1fr; } .chat-zone { grid-column: span 2; } }
@media (max-width: 750px) { .layout { grid-template-columns: 1fr; } .chat-zone { grid-column: auto; } }
.zone { display: flex; flex-direction: column; gap: 1rem; min-width: 0; }

.video-wrap { position: relative; padding: 0; overflow: hidden; aspect-ratio: 16/9; }
.video-wrap video { width: 100%; height: 100%; object-fit: contain; background: #000; display: block; }
.video-overlay {
  position: absolute; inset: 0; display: flex;
  align-items: center; justify-content: center;
  background: radial-gradient(ellipse at 30% 20%, #241f45 0%, var(--panel-2) 70%);
}
.go-live { padding: .7rem 1.4rem; font-size: 1rem; }
.err-msg { color: var(--live); margin: 0; }

.total { font-size: 1.15rem; }
.sales-table { width: 100%; border-collapse: collapse; margin-top: .5rem; font-size: .88rem; }
.sales-table td { padding: .3rem 0; border-bottom: 1px solid var(--border); }
.sales-table .amount { text-align: right; font-weight: 650; }
.feed { list-style: none; padding: 0; margin: .6rem 0 0; font-size: .8rem; color: var(--muted); }
.feed li { margin: .2rem 0; }

.list { list-style: none; padding: 0; margin: .6rem 0 0; display: flex; flex-direction: column; gap: .6rem; }
.prod { background: var(--panel-2); border-radius: 10px; padding: .6rem; display: flex; flex-direction: column; gap: .5rem; }
.thumb { width: 42px; height: 42px; border-radius: 8px; object-fit: cover; }
.thumb.placeholder { display: flex; align-items: center; justify-content: center; background: var(--bg); }
.pname { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
.psub { font-size: .78rem; }
.actions { gap: .4rem; }
.stepper { display: flex; align-items: center; gap: .15rem; }
.stepper button { width: 28px; height: 28px; padding: 0; border-radius: 6px; }
.stock { min-width: 2rem; text-align: center; font-weight: 700; }
.stock.zero { color: var(--live); }
.pin-btn { font-size: .82rem; padding: .35rem .6rem; }

.chat-zone :deep(.chat) { max-height: calc(100vh - 9rem); min-height: 380px; }
</style>
