<script setup lang="ts">
import { clp, type Stream } from '~/types'

const route = useRoute()
const streamId = route.params.streamId as string
const { api, assetUrl } = useApi()
const { user, token } = useAuth()

const stream = ref<Stream | null>(null)
const notFound = ref(false)
const videoEl = ref<HTMLVideoElement>()
const muted = ref(true)
const qty = ref(1)

const room = useStreamRoom(streamId)
const player = useWhepPlayer()
const { buy, buying, lastOrder, error: buyError } = useCheckout()
const chatInput = ref('')

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
})

// Al loguearse dentro de la página, conectar sala
watch(token, (t) => { if (t) room.connect() })

function unmute() {
  muted.value = false
  if (videoEl.value) videoEl.value.muted = false
}

function sendChat() {
  room.sendChat(chatInput.value)
  chatInput.value = ''
}

async function buyPinned() {
  if (!room.pinned.value) return
  await buy(streamId, room.pinned.value.id, qty.value)
  if (lastOrder.value) qty.value = 1
}
</script>

<template>
  <div class="container">
    <p v-if="notFound" class="muted">Stream no encontrado.</p>

    <div v-else-if="stream" class="layout">
      <!-- Video -->
      <div class="video-col">
        <div class="video-wrap panel">
          <video ref="videoEl" autoplay playsinline :muted="muted" />
          <div v-if="player.isMock.value" class="video-placeholder">
            <span class="badge live">MOCK</span>
            <p>Video simulado (sin cuenta Cloudflare).<br />Chat, pins y compras funcionan igual.</p>
          </div>
          <div v-else-if="room.ended.value || stream.status === 'ended'" class="video-placeholder">
            <p>El stream terminó. ¡Gracias por venir!</p>
          </div>
          <div v-else-if="player.error.value" class="video-placeholder">
            <p>{{ player.error.value }}</p>
          </div>
          <button v-if="muted && player.playing.value" class="unmute primary" @click="unmute">
            🔊 Activar sonido
          </button>
        </div>

        <div class="row stream-meta">
          <h2>{{ stream.title }}</h2>
          <span v-if="stream.status === 'live' && !room.ended.value" class="badge live">EN VIVO</span>
          <span class="muted">{{ stream.streamerName }}</span>
          <span class="muted">👁 {{ room.viewers.value }}</span>
        </div>

        <!-- Producto pineado -->
        <div v-if="room.pinned.value" class="panel pinned">
          <img
            v-if="room.pinned.value.imageUrl"
            :src="assetUrl(room.pinned.value.imageUrl) ?? undefined"
            alt=""
          />
          <div class="pinned-info">
            <h3>{{ room.pinned.value.name }}</h3>
            <p class="price">{{ clp(room.pinned.value.priceClp) }}</p>
            <p class="muted">Stock: {{ room.pinned.value.stock }}</p>
          </div>
          <div class="pinned-buy">
            <template v-if="user">
              <input v-model.number="qty" type="number" min="1" :max="room.pinned.value.stock" />
              <button
                class="primary"
                :disabled="buying || room.pinned.value.stock < 1"
                @click="buyPinned"
              >
                {{ room.pinned.value.stock < 1 ? 'Agotado' : buying ? 'Comprando…' : 'Comprar' }}
              </button>
            </template>
            <p v-else class="muted">Inicia sesión para comprar</p>
            <p v-if="lastOrder" class="ok-msg">✅ Compra realizada — {{ clp(lastOrder.amountClp) }}</p>
            <p v-if="buyError" class="err-msg">{{ buyError }}</p>
          </div>
        </div>
      </div>

      <!-- Chat -->
      <aside class="panel chat">
        <h3>Chat</h3>
        <div class="chat-messages">
          <p v-for="(m, i) in room.messages.value" :key="i">
            <strong>{{ m.name }}:</strong> {{ m.text }}
          </p>
          <p v-if="!room.messages.value.length" class="muted">Sé el primero en escribir…</p>
        </div>
        <form v-if="user" class="row" @submit.prevent="sendChat">
          <input v-model="chatInput" placeholder="Escribe un mensaje" maxlength="280" style="flex:1" />
          <button type="submit" :disabled="!room.connected.value">Enviar</button>
        </form>
        <p v-else class="muted">Inicia sesión para chatear</p>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 1fr 320px; gap: 1rem; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }

.video-wrap { position: relative; padding: 0; overflow: hidden; aspect-ratio: 16/9; }
.video-wrap video { width: 100%; height: 100%; object-fit: contain; background: #000; }
.video-placeholder {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: .5rem; text-align: center;
  background: var(--panel-2);
}
.unmute { position: absolute; bottom: 1rem; left: 1rem; }

.stream-meta { margin: .8rem 0; }
.stream-meta h2 { margin: 0; }

.pinned { display: flex; gap: 1rem; align-items: center; }
.pinned img { width: 90px; height: 90px; object-fit: cover; border-radius: 8px; }
.pinned-info { flex: 1; }
.price { font-size: 1.2rem; font-weight: 700; margin: .2rem 0; }
.pinned-buy { display: flex; flex-direction: column; gap: .4rem; align-items: flex-end; }
.pinned-buy input { width: 70px; }
.ok-msg { color: var(--ok); margin: 0; font-size: .85rem; }
.err-msg { color: var(--live); margin: 0; font-size: .85rem; }

.chat { display: flex; flex-direction: column; max-height: 75vh; }
.chat-messages { flex: 1; overflow-y: auto; margin-bottom: .6rem; min-height: 200px; }
.chat-messages p { margin: .25rem 0; word-break: break-word; }
</style>
