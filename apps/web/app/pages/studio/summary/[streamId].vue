<script setup lang="ts">
import { clp, type StreamSummary } from '~/types'

const route = useRoute()
const streamId = route.params.streamId as string
const { api } = useApi()
const { user, isStreamer } = useAuth()

const summary = ref<StreamSummary | null>(null)
const error = ref('')

onMounted(async () => {
  try {
    summary.value = await api<StreamSummary>(`/api/streams/${streamId}/summary`)
  } catch (e: any) {
    error.value = e.data?.detail ?? 'No se pudo cargar el resumen'
  }
})

function fmtDuration(sec: number | null) {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60)
  return h ? `${h}h ${m}m` : `${m} min`
}
</script>

<template>
  <div class="container" style="max-width:820px">
    <p v-if="!user || !isStreamer" class="muted">Requiere sesión de streamer.</p>
    <p v-else-if="error" class="muted">{{ error }}</p>

    <template v-else-if="summary">
      <NuxtLink to="/studio" class="muted">← Studio</NuxtLink>
      <div class="head">
        <h1>{{ summary.title }}</h1>
        <p class="muted">
          Resumen del stream ·
          <span class="badge" :class="{ live: summary.status === 'live' }">{{ summary.status }}</span>
        </p>
      </div>

      <div class="stats-grid">
        <StatCard icon="💰" label="Total vendido" :value="clp(summary.totalClp)" />
        <StatCard icon="🧾" label="Órdenes" :value="String(summary.ordersCount)" />
        <StatCard icon="📦" label="Unidades" :value="String(summary.units)" />
        <StatCard icon="👁" label="Peak de viewers" :value="String(summary.peakViewers)" />
        <StatCard icon="⏱️" label="Duración" :value="fmtDuration(summary.durationSec)" />
      </div>

      <section class="panel" style="margin-top:1rem">
        <h3>Ventas por producto</h3>
        <table v-if="summary.byProduct.length" class="table">
          <thead>
            <tr><th>Producto</th><th>Unidades</th><th class="right">Total</th></tr>
          </thead>
          <tbody>
            <tr v-for="p in summary.byProduct" :key="p.productId">
              <td>{{ p.name }}</td>
              <td>{{ p.units }}</td>
              <td class="right"><strong>{{ clp(p.totalClp) }}</strong></td>
            </tr>
          </tbody>
        </table>
        <p v-else class="muted">Este stream no registró ventas.</p>
      </section>

      <div class="row" style="margin-top:1.2rem">
        <NuxtLink to="/studio"><button class="primary">Volver al Studio</button></NuxtLink>
      </div>
    </template>
    <p v-else class="muted">Cargando…</p>
  </div>
</template>

<style scoped>
.head { margin: .6rem 0 1.2rem; }
.head h1 { margin-bottom: .2rem; }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: .8rem;
}
.table { width: 100%; border-collapse: collapse; }
.table th { text-align: left; color: var(--muted); font-size: .78rem; font-weight: 600; padding: .3rem 0; }
.table td { padding: .45rem 0; border-top: 1px solid var(--border); }
.right { text-align: right; }
</style>
