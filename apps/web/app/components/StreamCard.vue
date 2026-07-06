<script setup lang="ts">
import type { Stream } from '~/types'

defineProps<{ stream: Stream; hero?: boolean }>()

function fmtDate(ts: number | null) {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleString('es-CL', {
    weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <NuxtLink :to="`/watch/${stream.id}`" class="card" :class="{ hero, live: stream.status === 'live' }">
    <div class="thumb">
      <span class="emoji">{{ stream.status === 'live' ? '📺' : '🗓️' }}</span>
      <span v-if="stream.status === 'live'" class="badge live overlay">EN VIVO</span>
      <span v-else class="badge overlay">{{ fmtDate(stream.scheduledAt) }}</span>
    </div>
    <div class="info">
      <h3>{{ stream.title }}</h3>
      <p class="muted">{{ stream.streamerName }}</p>
      <div class="row meta">
        <span v-if="stream.status === 'live'" class="muted">👁 {{ stream.viewers ?? 0 }}</span>
        <span v-if="stream.productsCount" class="muted">🛍️ {{ stream.productsCount }} productos</span>
      </div>
    </div>
  </NuxtLink>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  transition: transform .15s, border-color .15s, box-shadow .15s;
}
.card:hover { transform: translateY(-3px); border-color: var(--accent); }
.card.live:hover { box-shadow: 0 6px 28px rgba(255, 77, 94, .18); }
.card.hero { flex-direction: row; }
.card.hero .thumb { flex: 1.4; min-height: 240px; }
.card.hero .info { flex: 1; align-self: center; padding: 1.5rem; }
.card.hero h3 { font-size: 1.5rem; }
@media (max-width: 700px) { .card.hero { flex-direction: column; } }

.thumb {
  position: relative;
  aspect-ratio: 16/9;
  background: radial-gradient(ellipse at 30% 20%, #241f45 0%, var(--panel-2) 70%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.card.hero .thumb { aspect-ratio: auto; }
.emoji { font-size: 2.6rem; opacity: .5; }
.overlay { position: absolute; top: .7rem; left: .7rem; }

.info { padding: .85rem 1rem 1rem; }
.info h3 { margin-bottom: .15rem; }
.info p { margin: 0 0 .4rem; }
.meta { font-size: .85rem; }
</style>
