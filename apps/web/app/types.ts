export interface Stream {
  id: string
  streamerId: string
  streamerName?: string
  title: string
  status: 'scheduled' | 'live' | 'ended'
  ingestType: 'whip' | 'rtmp'
  whepUrl: string
  whipUrl?: string
  scheduledAt: number | null
  startedAt: number | null
  endedAt: number | null
  products?: Product[]
}

export interface Product {
  id: string
  streamerId: string
  name: string
  description: string | null
  priceClp: number
  stock: number
  imageUrl: string | null
}

export interface PinnedProduct {
  id: string
  name: string
  priceClp: number
  imageUrl: string | null
  stock: number
}

export interface ChatMsg {
  userId: string
  name: string
  text: string
  ts: number
}

export interface Order {
  id: string
  streamId: string
  productId: string
  buyerId: string
  qty: number
  amountClp: number
  paymentStatus: string
  createdAt: number
  productName?: string
  buyerName?: string
}

export const clp = (n: number) =>
  new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(n)
