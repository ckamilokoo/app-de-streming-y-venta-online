<script setup lang="ts">
import { clp, type PinnedProduct } from '~/types'

const props = defineProps<{
  product: PinnedProduct
  canBuy: boolean
  maxStockRef?: number
}>()
const emit = defineEmits<{ buy: [] }>()

const { assetUrl } = useApi()

// Barra de stock relativa al máximo visto (urgencia visual)
const maxSeen = ref(props.product.stock)
watch(() => props.product.stock, (s) => { if (s > maxSeen.value) maxSeen.value = s })
const pct = computed(() => maxSeen.value ? Math.round((props.product.stock / maxSeen.value) * 100) : 0)
const level = computed(() =>
  props.product.stock <= 2 ? 'critical' : props.product.stock <= 5 ? 'low' : '',
)
</script>

<template>
  <div :key="product.id" class="pinned">
    <span class="tag">📌 Destacado ahora</span>
    <div class="body">
      <img v-if="product.imageUrl" :src="assetUrl(product.imageUrl) ?? undefined" alt="" />
      <div v-else class="noimg">🛍️</div>
      <div class="info">
        <h3>{{ product.name }}</h3>
        <p class="price">{{ clp(product.priceClp) }}</p>
        <div class="stock-bar" :class="level"><i :style="{ width: pct + '%' }" /></div>
        <p class="stock-label" :class="level">
          {{ product.stock < 1 ? 'AGOTADO' : product.stock <= 5 ? `¡Solo ${product.stock} disponibles!` : `Stock: ${product.stock}` }}
        </p>
      </div>
      <button
        v-if="canBuy"
        class="buy"
        :disabled="product.stock < 1"
        @click="emit('buy')"
      >
        {{ product.stock < 1 ? 'Agotado' : 'Comprar ahora' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.pinned {
  position: relative;
  background: var(--panel);
  border: 1px solid var(--accent);
  border-radius: 14px;
  padding: 1rem;
  box-shadow: 0 0 24px rgba(109, 92, 255, .18);
  animation: slide-up .3s ease;
}
.tag {
  position: absolute;
  top: -0.7rem;
  left: 1rem;
  background: var(--grad-live);
  color: #fff;
  font-size: .7rem;
  font-weight: 700;
  padding: .2rem .6rem;
  border-radius: 999px;
  letter-spacing: .05em;
}
.body { display: flex; gap: 1rem; align-items: center; }
img, .noimg {
  width: 84px; height: 84px;
  border-radius: 10px;
  object-fit: cover;
  flex-shrink: 0;
}
.noimg {
  display: flex; align-items: center; justify-content: center;
  background: var(--panel-2); font-size: 1.8rem;
}
.info { flex: 1; min-width: 0; }
.info h3 { margin: 0; font-size: 1.05rem; }
.price { font-size: 1.3rem; font-weight: 750; margin: .1rem 0 .4rem; }
.stock-label { margin: .3rem 0 0; font-size: .78rem; color: var(--muted); }
.stock-label.low { color: var(--warn); font-weight: 650; }
.stock-label.critical { color: var(--live); font-weight: 700; }
button.buy { padding: .7rem 1.3rem; font-size: 1rem; border-radius: 10px; }
@media (max-width: 600px) {
  .body { flex-wrap: wrap; }
  button.buy { width: 100%; }
}
</style>
