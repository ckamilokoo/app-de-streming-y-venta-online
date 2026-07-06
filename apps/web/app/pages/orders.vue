<script setup lang="ts">
import { clp, type Order } from '~/types'

const { api } = useApi()
const { user } = useAuth()
const orders = ref<Order[]>([])
const loading = ref(true)

onMounted(async () => {
  if (!user.value) { loading.value = false; return }
  try {
    orders.value = await api<Order[]>('/api/orders', { params: { mine: 1 } })
  } finally {
    loading.value = false
  }
})

const total = computed(() => orders.value.reduce((s, o) => s + o.amountClp, 0))

function fmtDate(ts: number) {
  return new Date(ts * 1000).toLocaleString('es-CL', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="container" style="max-width:760px">
    <h1>Mis compras</h1>
    <p v-if="!user" class="muted">Inicia sesión para ver tu historial.</p>
    <p v-else-if="loading" class="muted">Cargando…</p>
    <template v-else>
      <div v-if="orders.length" class="row summary panel">
        <span>{{ orders.length }} {{ orders.length === 1 ? 'compra' : 'compras' }}</span>
        <strong style="margin-left:auto">{{ clp(total) }}</strong>
      </div>
      <ul class="list">
        <li v-for="o in orders" :key="o.id" class="panel row">
          <div style="flex:1">
            <strong>{{ o.qty }}× {{ o.productName }}</strong>
            <div class="muted sub">
              en «{{ o.streamTitle }}» de {{ o.streamerName }} · {{ fmtDate(o.createdAt) }}
            </div>
          </div>
          <div class="right">
            <strong>{{ clp(o.amountClp) }}</strong>
            <span class="badge ok">{{ o.paymentStatus === 'mock_paid' ? 'pagado (mock)' : o.paymentStatus }}</span>
          </div>
        </li>
      </ul>
      <div v-if="!orders.length" class="panel empty">
        <span style="font-size:2rem">🛍️</span>
        <p class="muted">Aún no compras nada. Entra a un stream en vivo y aprovecha las ofertas.</p>
        <NuxtLink to="/"><button class="primary">Ver streams en vivo</button></NuxtLink>
      </div>
    </template>
  </div>
</template>

<style scoped>
.summary { margin-bottom: 1rem; }
.list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: .6rem; }
.sub { font-size: .8rem; }
.right { display: flex; flex-direction: column; align-items: flex-end; gap: .3rem; }
.empty { text-align: center; display: flex; flex-direction: column; align-items: center; gap: .5rem; padding: 2.5rem 1rem; }
</style>
