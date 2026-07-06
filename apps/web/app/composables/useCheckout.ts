import type { Order } from '~/types'

export function useCheckout() {
  const { api } = useApi()
  const buying = ref(false)
  const lastOrder = ref<Order | null>(null)
  const error = ref('')

  async function buy(streamId: string, productId: string, qty = 1) {
    buying.value = true
    error.value = ''
    lastOrder.value = null
    try {
      lastOrder.value = await api<Order>('/api/checkout', {
        method: 'POST',
        body: { stream_id: streamId, product_id: productId, qty },
      })
      return lastOrder.value
    } catch (e: any) {
      error.value = e.data?.detail ?? 'Error en la compra'
      return null
    } finally {
      buying.value = false
    }
  }

  return { buy, buying, lastOrder, error }
}
