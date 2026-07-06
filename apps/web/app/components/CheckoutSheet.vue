<script setup lang="ts">
import { clp } from '~/types'

const props = defineProps<{
  open: boolean
  product: { id: string; name: string; priceClp: number; imageUrl: string | null; stock: number } | null
  busy: boolean
  error: string
}>()
const emit = defineEmits<{ confirm: [qty: number]; close: [] }>()

const { assetUrl } = useApi()
const qty = ref(1)

watch(() => props.product?.id, () => { qty.value = 1 })

const total = computed(() => (props.product?.priceClp ?? 0) * qty.value)
const max = computed(() => Math.min(props.product?.stock ?? 1, 20))

function dec() { if (qty.value > 1) qty.value-- }
function inc() { if (qty.value < max.value) qty.value++ }
</script>

<template>
  <Teleport to="body">
    <div v-if="open && product" class="backdrop" @click.self="emit('close')">
      <div class="sheet">
        <div class="row" style="justify-content:space-between">
          <h3 style="margin:0">Confirmar compra</h3>
          <button class="ghost" @click="emit('close')">✕</button>
        </div>
        <div class="prod">
          <img v-if="product.imageUrl" :src="assetUrl(product.imageUrl) ?? undefined" alt="" />
          <div v-else class="noimg">🛍️</div>
          <div>
            <strong>{{ product.name }}</strong>
            <div class="muted">{{ clp(product.priceClp) }} c/u · stock {{ product.stock }}</div>
          </div>
        </div>
        <div class="row qty-row">
          <span>Cantidad</span>
          <div class="stepper">
            <button @click="dec" :disabled="qty <= 1">−</button>
            <span class="qty">{{ qty }}</span>
            <button @click="inc" :disabled="qty >= max">＋</button>
          </div>
        </div>
        <div class="row total-row">
          <span>Total</span>
          <strong class="total">{{ clp(total) }}</strong>
        </div>
        <p class="muted pay-note">Pago simulado (MercadoPago llega en fase 3)</p>
        <p v-if="error" class="err">{{ error }}</p>
        <button class="buy confirm" :disabled="busy" @click="emit('confirm', qty)">
          {{ busy ? 'Procesando…' : `Pagar ${clp(total)}` }}
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0, 0, 0, .55);
  display: flex; align-items: flex-end; justify-content: center;
}
.sheet {
  width: min(460px, 100%);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px 16px 0 0;
  padding: 1.2rem;
  animation: slide-up .25s ease;
}
@media (min-width: 700px) {
  .backdrop { align-items: center; }
  .sheet { border-radius: 16px; }
}
.prod { display: flex; gap: .8rem; align-items: center; margin: 1rem 0; }
.prod img, .noimg { width: 56px; height: 56px; border-radius: 8px; object-fit: cover; }
.noimg { display: flex; align-items: center; justify-content: center; background: var(--panel-2); }
.qty-row, .total-row { justify-content: space-between; margin: .6rem 0; }
.stepper { display: flex; align-items: center; gap: .2rem; }
.stepper button { width: 34px; height: 34px; padding: 0; font-size: 1.1rem; border-radius: 8px; }
.qty { min-width: 2.2rem; text-align: center; font-weight: 700; }
.total { font-size: 1.25rem; }
.pay-note { font-size: .75rem; margin: .2rem 0 .6rem; }
.err { color: var(--live); font-size: .85rem; margin: .3rem 0; }
.confirm { width: 100%; padding: .8rem; font-size: 1rem; border-radius: 10px; }
</style>
