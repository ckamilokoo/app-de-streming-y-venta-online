<script setup lang="ts">
import { clp, type Product } from '~/types'

defineProps<{
  products: Product[]
  canBuy: boolean
  pinnedId?: string | null
}>()
const emit = defineEmits<{ buy: [product: Product] }>()

const { assetUrl } = useApi()
</script>

<template>
  <div v-if="products.length" class="rail-wrap">
    <h3>Catálogo del stream</h3>
    <div class="rail">
      <div
        v-for="p in products"
        :key="p.id"
        class="item"
        :class="{ pinned: p.id === pinnedId, out: p.stock < 1 }"
      >
        <img v-if="p.imageUrl" :src="assetUrl(p.imageUrl) ?? undefined" alt="" />
        <div v-else class="noimg">📦</div>
        <div class="name" :title="p.name">{{ p.name }}</div>
        <div class="price">{{ clp(p.priceClp) }}</div>
        <div class="stock muted">{{ p.stock < 1 ? 'Agotado' : `Stock ${p.stock}` }}</div>
        <button
          v-if="canBuy"
          class="primary"
          :disabled="p.stock < 1"
          @click="emit('buy', p)"
        >Comprar</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rail-wrap h3 { margin: 0 0 .6rem; font-size: 1rem; }
.rail {
  display: flex;
  gap: .8rem;
  overflow-x: auto;
  padding-bottom: .5rem;
}
.item {
  flex: 0 0 150px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: .6rem;
  display: flex;
  flex-direction: column;
  gap: .25rem;
}
.item.pinned { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }
.item.out { opacity: .55; }
img, .noimg {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  object-fit: cover;
}
.noimg {
  display: flex; align-items: center; justify-content: center;
  background: var(--panel-2); font-size: 1.6rem;
}
.name {
  font-weight: 650; font-size: .85rem;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.price { font-weight: 700; }
.stock { font-size: .75rem; }
button { padding: .35rem .5rem; font-size: .82rem; margin-top: .2rem; }
</style>
