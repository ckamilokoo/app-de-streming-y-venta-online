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
  productsCount?: number
  viewers?: number
}

export interface StreamSummary {
  streamId: string
  title: string
  status: string
  startedAt: number | null
  endedAt: number | null
  durationSec: number | null
  peakViewers: number
  totalClp: number
  ordersCount: number
  units: number
  byProduct: { productId: string; name: string; units: number; totalClp: number }[]
}

export interface StudioStats {
  totalClp: number
  ordersCount: number
  unitsSold: number
  streamsCount: number
  productsCount: number
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
  role?: 'buyer' | 'streamer' | 'admin'
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
  streamTitle?: string
  streamerName?: string
}

export const REACTIONS = ['❤️', '🔥', '👏', '😍', '🎉'] as const

export const clp = (n: number) =>
  new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(n)
