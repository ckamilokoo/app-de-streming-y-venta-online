<script setup lang="ts">
import { clp, type Order, type Product, type Stream } from '~/types'

const route = useRoute()
const streamId = route.params.streamId as string
const { api } = useApi()
const { user, token } = useAuth()
const { show: showLogin } = useAuthModal()

const stream = ref<Stream | null>(null)
const notFound = ref(false)
const videoEl = ref<HTMLVideoElement>()
const muted = ref(true)

const room = useStreamRoom(streamId)
const player = useWhepPlayer()
const { buy, buying, error: buyError } = useCheckout()

// Checkout sheet
const sheetOpen = ref(false)
const sheetProduct = ref<Product | null>(null)
const myOrders = ref<Order[]>([])
const lastSuccess = ref('')

onMounted(async () => {
  try {
    stream.value = await api<Stream>(`/api/streams/${streamId}`)
  } catch {
    notFound.value = true
    return
  }
  if (token.value) room.connect()
  if (stream.value.status === 'live' && videoEl.value) {
    player.play(stream.value.whepUrl, videoEl.value)
  }
  // Stock en vivo también sobre el rail de catálogo
  room.onStock((productId, stock) => {
    const p = stream.value?.products?.find((x) => x.id === productId)
    if (p) p.stock = stock
    if (sheetProduct.value?.id === productId) sheetProduct.value.stock = stock
  })
})

watch(token, (t) => { if (t) room.connect() })

const isLive = computed(() => stream.value?.status === 'live' && !room.ended.value)

function unmute() {
  muted.value = false
  if (videoEl.value) videoEl.value.muted = false
}

function openSheet(p: Product | null) {
  if (!p) return
  buyError.value = ''
  sheetProduct.value = { ...p }
  sheetOpen.value = true
}

function openSheetFromPinned() {
  if (!room.pinned.value) return
  const pin = room.pinned.value
  openSheet({
    id: pin.id, name: pin.name, priceClp: pin.priceClp,
    imageUrl: pin.imageUrl, stock: pin.stock,
    streamerId: '', description: null,
  })
}

async function confirmBuy(qty: number) {
  if (!sheetProduct.value) return
  const order = await buy(streamId, sheetProduct.value.id, qty)
  if (order) {
    order.productName = sheetProduct.value.name
    myOrders.value.unshift(order)
    lastSuccess.value = `${qty}× ${sheetProduct.value.name} — ${clp(order.amountClp)}`
    sheetOpen.value = false
    setTimeout(() => { lastSuccess.value = '' }, 5000)
  }
}

const myTotal = computed(() => myOrders.value.reduce((s, o) => s + o.amountClp, 0))
</script>

<template>
  <div class="container">
    <p v-if="notFound" class="muted">Stream no encontrado.</p>

    <div v-else-if="stream" class="layout">
      <div class="video-col">
        <!-- Video + reacciones -->
        <div class="video-wrap panel">
          <video ref="videoEl" autoplay playsinline :muted="muted" />
          <div v-if="player.isMock.value && isLive" class="video-placeholder">
            <span class="badge live">MOCK</span>
            <p>Video simulado (sin cuenta Cloudflare).<br />Chat, reacciones y compras funcionan igual.</p>
          </div>
          <div v-else-if="!isLive" class="video-placeholder">
            <template v-if="stream.status === 'scheduled'">
              <span style="font-size:2rem">🗓️</span>
              <p>Este stream aún no comienza.</p>
            </template>
            <template v-else>
              <span style="font-size:2rem">👋</span>
              <p>El stream terminó. ¡Gracias por venir!</p>
            </template>
          </div>
          <div v-else-if="player.error.value" class="video-placeholder">
            <p>{{ player.error.value }}</p>
          </div>
          <ReactionOverlay
            :reactions="room.reactions.value"
            :can-react="!!user && isLive && room.connected.value"
            @react="room.sendReact"
          />
          <button v-if="muted && player.playing.value" class="unmute primary" @click="unmute">
            🔊 Activar sonido
          </button>
        </div>

        <div class="row stream-meta">
          <h2 style="margin:0">{{ stream.title }}</h2>
          <span v-if="isLive" class="badge live">EN VIVO</span>
          <span class="muted">{{ stream.streamerName }}</span>
          <span v-if="isLive" class="muted">👁 {{ room.viewers.value }}</span>
        </div>

        <p v-if="lastSuccess" class="success-banner">✅ Compra realizada: {{ lastSuccess }}</p>

        <!-- Producto destacado -->
        <template v-if="room.pinned.value && isLive">
          <PinnedCard
            :product="room.pinned.value"
            :can-buy="!!user"
            @buy="openSheetFromPinned"
          />
          <button v-if="!user" class="buy guest-cta" @click="showLogin('buyer')">
            Inicia sesión para comprar
          </button>
        </template>
        <p v-else-if="isLive" class="muted pin-hint">
          El streamer aún no destaca ningún producto — mira el catálogo 👇
        </p>

        <!-- Catálogo completo -->
        <ProductRail
          :products="stream.products ?? []"
          :can-buy="!!user && isLive"
          :pinned-id="room.pinned.value?.id"
          @buy="openSheet"
        />

        <!-- Mis compras de este stream -->
        <div v-if="myOrders.length" class="panel my-orders">
          <div class="row" style="justify-content:space-between">
            <h3 style="margin:0">🧾 Mis compras de este stream</h3>
            <strong>{{ clp(myTotal) }}</strong>
          </div>
          <ul>
            <li v-for="o in myOrders" :key="o.id">
              {{ o.qty }}× {{ o.productName }} — {{ clp(o.amountClp) }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Chat -->
      <aside class="chat-col">
        <ChatPanel
          :messages="room.messages.value"
          :connected="room.connected.value"
          :can-write="!!user"
          @send="room.sendChat"
          @login="showLogin('buyer')"
        />
      </aside>
    </div>

    <CheckoutSheet
      :open="sheetOpen"
      :product="sheetProduct"
      :busy="buying"
      :error="buyError"
      @confirm="confirmBuy"
      @close="sheetOpen = false"
    />
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 1fr 330px; gap: 1rem; align-items: start; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.video-col { display: flex; flex-direction: column; gap: 1rem; min-width: 0; }

.video-wrap { position: relative; padding: 0; overflow: hidden; aspect-ratio: 16/9; }
.video-wrap video { width: 100%; height: 100%; object-fit: contain; background: #000; display: block; }
.video-placeholder {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: .5rem; text-align: center;
  background: radial-gradient(ellipse at 30% 20%, #241f45 0%, var(--panel-2) 70%);
}
.unmute { position: absolute; bottom: 1rem; left: 1rem; z-index: 2; }

.stream-meta { margin: -.3rem 0 0; }

.success-banner {
  margin: 0;
  padding: .6rem .9rem;
  border-radius: 10px;
  background: rgba(46, 204, 143, .12);
  border: 1px solid var(--ok);
  color: var(--ok);
  font-size: .9rem;
  animation: slide-up .25s ease;
}

.pin-hint { margin: 0; font-size: .85rem; }
.guest-cta { margin-top: -.4rem; }

.my-orders ul { margin: .5rem 0 0; padding-left: 1.1rem; }
.my-orders li { font-size: .88rem; margin: .2rem 0; }

.chat-col { position: sticky; top: 4.5rem; }
.chat-col :deep(.chat) { max-height: calc(100vh - 6rem); min-height: 420px; }
</style>
