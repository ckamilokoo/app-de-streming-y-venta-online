<script setup lang="ts">
import type { Stream } from '~/types'

const { api } = useApi()
const live = ref<Stream[]>([])
const scheduled = ref<Stream[]>([])
const loading = ref(true)

async function load() {
  try {
    const [l, s] = await Promise.all([
      api<Stream[]>('/api/streams', { params: { status: 'live' } }),
      api<Stream[]>('/api/streams', { params: { status: 'scheduled' } }),
    ])
    live.value = l.sort((a, b) => (b.viewers ?? 0) - (a.viewers ?? 0))
    scheduled.value = s.filter((x) => x.scheduledAt)
  } finally {
    loading.value = false
  }
}

let poll: ReturnType<typeof setInterval>
onMounted(() => {
  load()
  poll = setInterval(load, 10_000)
})
onBeforeUnmount(() => clearInterval(poll))

const hero = computed(() => live.value[0] ?? null)
const rest = computed(() => live.value.slice(1))

const { user } = useAuth()
const { show } = useAuthModal()
</script>

<template>
  <div class="container">
    <!-- Landing para visitantes: qué es la app y cómo se usa -->
    <section v-if="!user" class="welcome">
      <div class="welcome-text">
        <h1>Compra en vivo,<br /><span class="grad">directo del streamer</span></h1>
        <p class="muted">
          LiveCommerce es live shopping: mira demostraciones de productos en tiempo real,
          pregunta por el chat y compra con un click antes de que se agote el stock.
        </p>
        <div class="row ctas">
          <button class="buy" @click="show('buyer')">🛍️ Quiero comprar</button>
          <button @click="show('streamer')">🎥 Quiero vender en vivo</button>
        </div>
      </div>
      <div class="steps">
        <div class="step panel">
          <span class="n">1</span>
          <strong>📺 Mira</strong>
          <p class="muted">Streams en vivo mostrando productos reales, sin fotos retocadas.</p>
        </div>
        <div class="step panel">
          <span class="n">2</span>
          <strong>💬 Participa</strong>
          <p class="muted">Chatea con el streamer, reacciona y resuelve tus dudas al instante.</p>
        </div>
        <div class="step panel">
          <span class="n">3</span>
          <strong>🛒 Compra</strong>
          <p class="muted">Stock limitado en vivo: checkout en segundos desde el mismo stream.</p>
        </div>
      </div>
    </section>

    <p v-if="loading" class="muted">Cargando…</p>

    <template v-else>
      <section v-if="hero">
        <h1 class="section-title"><span class="badge live">EN VIVO</span> Ahora</h1>
        <StreamCard :stream="hero" hero />
        <div v-if="rest.length" class="grid" style="margin-top:1rem">
          <StreamCard v-for="s in rest" :key="s.id" :stream="s" />
        </div>
      </section>

      <div v-else class="empty panel">
        <span style="font-size:2.5rem">📭</span>
        <h2>Nadie está transmitiendo</h2>
        <p class="muted">Si eres streamer, crea un stream desde el Studio y sal en vivo.</p>
      </div>

      <section v-if="scheduled.length" style="margin-top:2rem">
        <h2 class="section-title">🗓️ Próximos streams</h2>
        <div class="grid">
          <StreamCard v-for="s in scheduled" :key="s.id" :stream="s" />
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.welcome {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 2rem;
  align-items: center;
  padding: 1.5rem 0 2.5rem;
}
@media (max-width: 850px) { .welcome { grid-template-columns: 1fr; } }
.welcome-text h1 { font-size: 2.2rem; line-height: 1.15; margin-bottom: .6rem; }
.grad {
  background: var(--grad-live);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.welcome-text p { max-width: 46ch; }
.ctas { margin-top: 1.2rem; }
.ctas .buy { padding: .7rem 1.2rem; font-size: 1rem; }
.ctas button:not(.buy) { padding: .7rem 1.2rem; font-size: 1rem; }

.steps { display: flex; flex-direction: column; gap: .7rem; }
.step { position: relative; padding: .8rem 1rem .8rem 3rem; }
.step .n {
  position: absolute; left: .9rem; top: 50%; transform: translateY(-50%);
  width: 1.6rem; height: 1.6rem; border-radius: 50%;
  background: var(--grad-live); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: .85rem;
}
.step p { margin: .15rem 0 0; font-size: .82rem; }

.section-title { display: flex; align-items: center; gap: .6rem; font-size: 1.3rem; margin: .5rem 0 1rem; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}
.empty {
  text-align: center;
  padding: 3rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .3rem;
}
</style>
