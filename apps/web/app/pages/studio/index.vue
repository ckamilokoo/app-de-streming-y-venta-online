<script setup lang="ts">
import { clp, type Product, type Stream, type StudioStats } from '~/types'

const { api, assetUrl } = useApi()
const { user, isStreamer } = useAuth()
const { show: showLogin } = useAuthModal()

const stats = ref<StudioStats | null>(null)
const products = ref<Product[]>([])
const streams = ref<Stream[]>([])

// Form producto nuevo
const pName = ref('')
const pPrice = ref<number | null>(null)
const pStock = ref<number | null>(null)
const pDesc = ref('')
const pImage = ref<File | null>(null)
const savingProduct = ref(false)

// Edición inline
const editingId = ref<string | null>(null)
const eName = ref('')
const ePrice = ref(0)
const eStock = ref(0)

// Form stream
const sTitle = ref('')
const sWhen = ref('')  // datetime-local
const savingStream = ref(false)

async function load() {
  if (!isStreamer.value) return
  ;[stats.value, products.value, streams.value] = await Promise.all([
    api<StudioStats>('/api/studio/stats'),
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

function startEdit(p: Product) {
  editingId.value = p.id
  eName.value = p.name
  ePrice.value = p.priceClp
  eStock.value = p.stock
}

async function saveEdit() {
  if (!editingId.value) return
  await api(`/api/products/${editingId.value}`, {
    method: 'PATCH',
    body: { name: eName.value, price_clp: ePrice.value, stock: eStock.value },
  })
  editingId.value = null
  await load()
}

async function removeProduct(p: Product) {
  if (!confirm(`¿Eliminar "${p.name}"? No se puede deshacer.`)) return
  try {
    await api(`/api/products/${p.id}`, { method: 'DELETE' })
    await load()
  } catch (e: any) {
    alert(e.data?.detail ?? 'No se pudo eliminar')
  }
}

async function createStream() {
  if (!sTitle.value.trim()) return
  savingStream.value = true
  try {
    const body: any = { title: sTitle.value.trim() }
    if (sWhen.value) body.scheduled_at = Math.floor(new Date(sWhen.value).getTime() / 1000)
    await api('/api/streams', { method: 'POST', body })
    sTitle.value = ''; sWhen.value = ''
    await load()
  } finally {
    savingStream.value = false
  }
}

function fmtDate(ts: number | null) {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleString('es-CL', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="container">
    <div v-if="!user || !isStreamer" class="panel gate">
      <span style="font-size:2.2rem">🎥</span>
      <h2>El Studio es para streamers</h2>
      <p class="muted">
        Crea tu catálogo de productos, sal en vivo con tu cámara y vende
        destacando productos mientras transmites.
      </p>
      <button class="buy" @click="showLogin('streamer')">
        {{ user ? 'Entrar como streamer' : 'Iniciar sesión como streamer' }}
      </button>
      <p v-if="user" class="muted hint">Estás como comprador — vuelve a entrar eligiendo el rol Streamer.</p>
    </div>

    <template v-else>
      <h1>Studio</h1>

      <!-- Stats -->
      <div v-if="stats" class="stats-grid">
        <StatCard icon="💰" label="Total vendido" :value="clp(stats.totalClp)" />
        <StatCard icon="🧾" label="Órdenes" :value="String(stats.ordersCount)" />
        <StatCard icon="📦" label="Unidades vendidas" :value="String(stats.unitsSold)" />
        <StatCard icon="🎥" label="Streams" :value="String(stats.streamsCount)" />
      </div>

      <div class="grid">
        <!-- Streams -->
        <section class="panel">
          <h2>Mis streams</h2>
          <form class="sform" @submit.prevent="createStream">
            <input v-model="sTitle" placeholder="Título del stream" required />
            <div class="row">
              <input v-model="sWhen" type="datetime-local" style="flex:1" title="Programar (opcional)" />
              <button type="submit" class="primary" :disabled="savingStream">Crear</button>
            </div>
            <p class="muted hint">Deja la fecha vacía para transmitir cuando quieras.</p>
          </form>
          <ul class="list">
            <li v-for="s in streams" :key="s.id" class="row">
              <span class="badge" :class="{ live: s.status === 'live' }">{{ s.status }}</span>
              <div style="flex:1">
                <strong>{{ s.title }}</strong>
                <div v-if="s.scheduledAt && s.status === 'scheduled'" class="muted hint">
                  🗓️ {{ fmtDate(s.scheduledAt) }}
                </div>
              </div>
              <NuxtLink v-if="s.status !== 'ended'" :to="`/studio/live/${s.id}`">
                <button class="primary">Consola</button>
              </NuxtLink>
              <NuxtLink v-else :to="`/studio/summary/${s.id}`">
                <button>Resumen</button>
              </NuxtLink>
            </li>
            <li v-if="!streams.length" class="muted">Aún no tienes streams.</li>
          </ul>
        </section>

        <!-- Productos -->
        <section class="panel">
          <h2>Mis productos <span v-if="stats" class="muted count">({{ stats.productsCount }})</span></h2>
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
            <li v-for="p in products" :key="p.id" class="product-item">
              <div class="row">
                <img v-if="p.imageUrl" :src="assetUrl(p.imageUrl) ?? undefined" class="thumb" alt="" />
                <div v-else class="thumb placeholder">📦</div>
                <div style="flex:1">
                  <strong>{{ p.name }}</strong>
                  <div class="muted">{{ clp(p.priceClp) }} · stock {{ p.stock }}</div>
                </div>
                <button class="ghost" @click="editingId === p.id ? editingId = null : startEdit(p)">
                  {{ editingId === p.id ? 'Cancelar' : '✏️ Editar' }}
                </button>
                <button class="ghost del" @click="removeProduct(p)">🗑️</button>
              </div>
              <form v-if="editingId === p.id" class="edit-form row" @submit.prevent="saveEdit">
                <input v-model="eName" required style="flex:2" />
                <input v-model.number="ePrice" type="number" min="1" style="width:110px" title="Precio CLP" />
                <input v-model.number="eStock" type="number" min="0" style="width:80px" title="Stock" />
                <button type="submit" class="primary">Guardar</button>
              </form>
            </li>
            <li v-if="!products.length" class="muted">Sin productos todavía.</li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: .8rem;
  margin-bottom: 1.2rem;
}
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
.list { list-style: none; padding: 0; margin: 1rem 0 0; display: flex; flex-direction: column; gap: .6rem; }
.pform, .sform { display: flex; flex-direction: column; gap: .6rem; }
.hint { font-size: .75rem; margin: 0; }
.count { font-size: .9rem; font-weight: 400; }
.thumb { width: 48px; height: 48px; border-radius: 8px; object-fit: cover; }
.thumb.placeholder { display: flex; align-items: center; justify-content: center; background: var(--panel-2); }
.product-item { display: flex; flex-direction: column; gap: .5rem; }
.edit-form { background: var(--panel-2); border-radius: 10px; padding: .6rem; }
.del:hover { border-color: var(--live); }
.gate {
  text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: .5rem;
  padding: 3rem 1rem;
  max-width: 520px;
  margin: 2rem auto;
}
.gate p { max-width: 42ch; margin: 0; }

</style>
