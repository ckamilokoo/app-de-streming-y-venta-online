<script setup lang="ts">
import { clp, type Product, type Stream } from '~/types'

const { api, assetUrl } = useApi()
const { user, isStreamer } = useAuth()

const products = ref<Product[]>([])
const streams = ref<Stream[]>([])

// Formulario producto
const pName = ref('')
const pPrice = ref<number | null>(null)
const pStock = ref<number | null>(null)
const pDesc = ref('')
const pImage = ref<File | null>(null)
const savingProduct = ref(false)

// Formulario stream
const sTitle = ref('')
const savingStream = ref(false)

async function load() {
  if (!isStreamer.value) return
  ;[products.value, streams.value] = await Promise.all([
    api<Product[]>('/api/products', { params: { mine: 1 } }),
    api<Stream[]>('/api/streams', { params: { mine: 1 } }),
  ])
}
onMounted(load)

function onFile(e: Event) {
  pImage.value = (e.target as HTMLInputElement).files?.[0] ?? null
}

async function createProduct() {
  if (!pName.value || !pPrice.value) return
  savingProduct.value = true
  try {
    const form = new FormData()
    form.set('name', pName.value)
    form.set('price_clp', String(pPrice.value))
    form.set('stock', String(pStock.value ?? 0))
    form.set('description', pDesc.value)
    if (pImage.value) form.set('image', pImage.value)
    await api('/api/products', { method: 'POST', body: form })
    pName.value = ''; pPrice.value = null; pStock.value = null; pDesc.value = ''; pImage.value = null
    await load()
  } finally {
    savingProduct.value = false
  }
}

async function createStream() {
  if (!sTitle.value.trim()) return
  savingStream.value = true
  try {
    await api('/api/streams', { method: 'POST', body: { title: sTitle.value.trim() } })
    sTitle.value = ''
    await load()
  } finally {
    savingStream.value = false
  }
}
</script>

<template>
  <div class="container">
    <p v-if="!user" class="muted">Inicia sesión como streamer para usar el Studio.</p>
    <p v-else-if="!isStreamer" class="muted">Tu cuenta es de comprador. Entra con rol "Streamer".</p>

    <div v-else class="grid">
      <!-- Streams -->
      <section class="panel">
        <h2>Mis streams</h2>
        <form class="row" @submit.prevent="createStream">
          <input v-model="sTitle" placeholder="Título del stream" style="flex:1" required />
          <button type="submit" class="primary" :disabled="savingStream">Crear</button>
        </form>
        <ul class="list">
          <li v-for="s in streams" :key="s.id" class="row">
            <span class="badge" :class="{ live: s.status === 'live' }">{{ s.status }}</span>
            <strong style="flex:1">{{ s.title }}</strong>
            <NuxtLink v-if="s.status !== 'ended'" :to="`/studio/live/${s.id}`">
              <button class="primary">Consola</button>
            </NuxtLink>
          </li>
          <li v-if="!streams.length" class="muted">Aún no tienes streams.</li>
        </ul>
      </section>

      <!-- Productos -->
      <section class="panel">
        <h2>Mis productos</h2>
        <form class="pform" @submit.prevent="createProduct">
          <input v-model="pName" placeholder="Nombre" required />
          <div class="row">
            <input v-model.number="pPrice" type="number" min="1" placeholder="Precio CLP" required style="flex:1" />
            <input v-model.number="pStock" type="number" min="0" placeholder="Stock" style="flex:1" />
          </div>
          <textarea v-model="pDesc" placeholder="Descripción (opcional)" rows="2" />
          <input type="file" accept="image/jpeg,image/png,image/webp" @change="onFile" />
          <button type="submit" class="primary" :disabled="savingProduct">Agregar producto</button>
        </form>
        <ul class="list">
          <li v-for="p in products" :key="p.id" class="row">
            <img v-if="p.imageUrl" :src="assetUrl(p.imageUrl) ?? undefined" class="thumb" alt="" />
            <div v-else class="thumb placeholder">📦</div>
            <div style="flex:1">
              <strong>{{ p.name }}</strong>
              <div class="muted">{{ clp(p.priceClp) }} · stock {{ p.stock }}</div>
            </div>
          </li>
          <li v-if="!products.length" class="muted">Sin productos todavía.</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
.list { list-style: none; padding: 0; margin: 1rem 0 0; display: flex; flex-direction: column; gap: .6rem; }
.pform { display: flex; flex-direction: column; gap: .6rem; }
.thumb { width: 48px; height: 48px; border-radius: 8px; object-fit: cover; }
.thumb.placeholder { display: flex; align-items: center; justify-content: center; background: var(--panel-2); }
</style>
