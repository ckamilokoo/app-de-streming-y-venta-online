<script setup lang="ts">
import type { Stream } from '~/types'

const { api } = useApi()
const streams = ref<Stream[]>([])
const loading = ref(true)

async function load() {
  try {
    streams.value = await api<Stream[]>('/api/streams', { params: { status: 'live' } })
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
</script>

<template>
  <div class="container">
    <h1>En vivo ahora</h1>
    <p v-if="loading" class="muted">Cargando…</p>
    <p v-else-if="!streams.length" class="muted">
      Nadie está transmitiendo. Si eres streamer, crea un stream desde el Studio.
    </p>
    <div class="grid">
      <NuxtLink v-for="s in streams" :key="s.id" :to="`/watch/${s.id}`" class="panel card">
        <span class="badge live">EN VIVO</span>
        <h3>{{ s.title }}</h3>
        <p class="muted">{{ s.streamerName }}</p>
      </NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}
.card:hover { border-color: var(--accent); }
.card h3 { margin-top: .6rem; }
</style>
