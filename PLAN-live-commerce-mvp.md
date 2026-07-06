# PLAN DE EJECUCIÓN — MVP Live Commerce (streaming + venta en vivo)

> Documento diseñado como input para Claude Code. Las decisiones están cerradas salvo las marcadas como PENDIENTE. Etiquetas de confianza: [Seguro] verificado en docs/evidencia, [Probable] inferencia fuerte, [Suposición] verificar contra docs antes de implementar.

---

## 0. Decisiones cerradas y pendientes

| Área | Decisión | Estado |
|---|---|---|
| Video ingest | Cloudflare Stream Live Inputs — WHIP desde navegador (streamer) | Cerrada |
| Video playback | WHEP (WebRTC) — obligatorio: [Seguro] WHIP no permite playback HLS/DASH aún | Cerrada |
| Fallback ingest | RTMP/SRT del mismo Live Input (para OBS) — solo fase 2 | Cerrada |
| Realtime (chat/pins/viewers) | Durable Objects + WebSocket Hibernation | Cerrada |
| API | Cloudflare Workers + Hono | Cerrada |
| DB | D1 (SQLite) | Cerrada |
| Assets | R2 (imágenes de producto) | Cerrada |
| Frontend | Nuxt 3 (SSR off para MVP → SPA) desplegado con Workers Assets | Cerrada |
| Auth | Clerk (streamer y comprador) | Cerrada |
| Pagos | Fase 1: checkout mock. Fase 2: MercadoPago Checkout Pro | Cerrada |
| Notificaciones | Fase 2: Telegram Bot API | Cerrada |
| PENDIENTE | Grabación/replay: [Probable] recording desde ingest WHIP tiene fallas reportadas (community CF nov-2025/mar-2026). Validar en spike antes de prometer replay | Abierta |
| PENDIENTE | Multi-tenant (varios streamers) vs single-tenant. MVP asume multi-streamer con 1 stream activo por streamer | Abierta |

---

## 1. Arquitectura general

```
┌──────────────┐   WHIP (WebRTC)    ┌──────────────────────┐
│  Streamer    │ ─────────────────▶ │  Cloudflare Stream    │
│  (browser,   │                    │  Live Input           │
│  getUserMedia)│                   └──────────┬───────────┘
└──────┬───────┘                               │ WHEP (WebRTC, <1s)
       │ WS                                    ▼
       │            ┌──────────────┐    ┌──────────────┐
       └──────────▶ │ Durable      │◀───│  Viewers     │
                    │ Object       │ WS │  (Nuxt SPA)  │
   admin: pin/chat  │ "StreamRoom" │    └──────┬───────┘
                    └──────┬───────┘           │ HTTPS
                           │ RPC/fetch          ▼
                    ┌──────┴───────────────────────────┐
                    │  Worker API (Hono)                │
                    │  /api/streams /api/products       │
                    │  /api/checkout /api/orders        │
                    └───┬─────────┬─────────┬──────────┘
                        │         │         │
                       D1        R2      Clerk (JWT verify)
                                          MercadoPago (fase 2)
```

Principios:
1. **Un solo proveedor de video.** No mezclar LiveKit/IVS. Si la beta WHIP de Cloudflare falla en el spike (sección 3), se reemplaza Stream completo por LiveKit Cloud — no se suman.
2. **El pin de producto viaja por WebSocket, no por el video.** La sincronización percibida depende del WS (instantáneo), el video puede tener su propia latencia.
3. **Modelo de datos agnóstico al protocolo de ingest** (`ingest_type: 'whip' | 'rtmp'`) para no refactorizar cuando entre OBS.

---

## 2. Estructura del monorepo

```
live-commerce/
├── apps/
│   ├── web/                  # Nuxt 3 SPA
│   │   ├── pages/
│   │   │   ├── index.vue             # lobby: streams en vivo
│   │   │   ├── watch/[streamId].vue  # viewer: player WHEP + chat + product rail + checkout
│   │   │   └── studio/
│   │   │       ├── index.vue         # dashboard streamer
│   │   │       └── live/[streamId].vue # broadcast: preview cámara + control de pins + chat
│   │   ├── composables/
│   │   │   ├── useWhipBroadcast.ts   # WHIPClient
│   │   │   ├── useWhepPlayer.ts      # WHEPClient
│   │   │   ├── useStreamRoom.ts      # WS al DO: chat, pins, viewers
│   │   │   └── useCheckout.ts
│   │   └── nuxt.config.ts            # ssr: false
│   └── api/                  # Worker
│       ├── src/
│       │   ├── index.ts              # Hono router + export DO
│       │   ├── routes/{streams,products,checkout,orders}.ts
│       │   ├── durable/StreamRoom.ts
│       │   ├── lib/{cloudflareStream.ts, clerk.ts, db.ts}
│       │   └── types/messages.ts     # protocolo WS compartido
│       ├── migrations/               # D1
│       └── wrangler.jsonc
└── packages/shared/                  # tipos compartidos web/api
```

---

## 3. Fase 0 — Spike de validación (medio día, OBLIGATORIO antes de todo)

Objetivo: confirmar que la beta WHIP/WHEP sostiene el MVP. Si falla cualquiera de los 3 checks, cambiar a LiveKit Cloud y ajustar sección 5.

1. Crear Live Input vía API y transmitir desde Chrome con el WHIPClient de ejemplo de Cloudflare.
2. Reproducir vía WHEP en otro navegador/red móvil. Medir latencia real (target: <2s) y estabilidad 15 min.
3. Verificar comportamiento de grabación (`recording.mode = "automatic"`) sobre ingest WHIP. [Probable] fallará o quedará incompleta — documentar resultado y decidir replay.

[Seguro] Crear Live Input (verificado en docs CF y tutorial Atyantik):

```
POST https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/stream/live_inputs
Authorization: Bearer {CF_STREAM_API_TOKEN}
{ "meta": { "name": "stream-{uuid}" }, "recording": { "mode": "automatic" } }
```

[Seguro] La respuesta incluye `result.webRTC.url` (WHIP, para transmitir) y `result.webRTCPlayback.url` (WHEP, para reproducir). Guardar ambos + `result.uid`.

[Seguro] Codec para WHIP: H.264 Constrained Baseline 3.1 (`42e01f`). No forzar VP8/VP9 desde clientes no-browser.

---

## 4. Modelo de datos (D1)

```sql
-- migrations/0001_init.sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,              -- clerk user id
  role TEXT NOT NULL DEFAULT 'buyer' CHECK (role IN ('buyer','streamer','admin')),
  display_name TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE streams (
  id TEXT PRIMARY KEY,              -- uuid propio
  streamer_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled'
    CHECK (status IN ('scheduled','live','ended')),
  ingest_type TEXT NOT NULL DEFAULT 'whip' CHECK (ingest_type IN ('whip','rtmp')),
  cf_live_input_uid TEXT NOT NULL,  -- uid de Cloudflare
  whip_url TEXT NOT NULL,
  whep_url TEXT NOT NULL,
  scheduled_at INTEGER,
  started_at INTEGER,
  ended_at INTEGER
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  streamer_id TEXT NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  price_clp INTEGER NOT NULL,       -- CLP sin decimales
  stock INTEGER NOT NULL DEFAULT 0,
  image_key TEXT                    -- key en R2
);

CREATE TABLE stream_products (      -- catálogo asignado a un stream
  stream_id TEXT NOT NULL REFERENCES streams(id),
  product_id TEXT NOT NULL REFERENCES products(id),
  PRIMARY KEY (stream_id, product_id)
);

CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  stream_id TEXT NOT NULL REFERENCES streams(id),
  product_id TEXT NOT NULL REFERENCES products(id),
  buyer_id TEXT NOT NULL REFERENCES users(id),
  qty INTEGER NOT NULL DEFAULT 1,
  amount_clp INTEGER NOT NULL,
  payment_status TEXT NOT NULL DEFAULT 'mock_paid'
    CHECK (payment_status IN ('pending','mock_paid','paid','failed')),
  mp_preference_id TEXT,            -- fase 2 MercadoPago
  created_at INTEGER NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX idx_orders_stream ON orders(stream_id);
```

Regla de stock: decrementar con `UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?` y verificar `meta.changes` — no leer-luego-escribir. [Probable] D1 serializa escrituras por DB, suficiente para MVP; a escala real el contador de stock "caliente" debería vivir en el DO de la sala.

---

## 5. Durable Object `StreamRoom`

Un DO por stream (`idFromName(streamId)`). Responsabilidades: WebSockets de la sala, chat efímero, pin de producto activo, contador de viewers.

Usar **WebSocket Hibernation API** (`state.acceptWebSocket(ws)` + handlers `webSocketMessage/webSocketClose`) — [Seguro] existe y reduce costo en idle a casi cero. [Suposición] verificar firmas exactas en docs de DO al implementar; no usar `addEventListener` clásico porque impide hibernar.

Estado interno (en `state.storage` para sobrevivir hibernación):
- `pinnedProductId: string | null`
- `viewerCount` se deriva de `state.getWebSockets().length`, no se persiste

### Protocolo WS (types/messages.ts — fuente de verdad compartida)

```ts
// Cliente → DO
type ClientMsg =
  | { t: 'chat'; text: string }                       // max 280 chars, sanitizar
  | { t: 'pin'; productId: string }                   // solo streamer (validar rol vía JWT en upgrade)
  | { t: 'unpin' }
  | { t: 'end_stream' };                              // solo streamer

// DO → Clientes (broadcast)
type ServerMsg =
  | { t: 'chat'; userId: string; name: string; text: string; ts: number }
  | { t: 'pinned'; product: { id: string; name: string; priceClp: number; imageUrl: string; stock: number } | null }
  | { t: 'viewers'; count: number }
  | { t: 'stock'; productId: string; stock: number }  // tras cada orden
  | { t: 'stream_ended' };
```

Reglas:
- Autenticación del WS: el upgrade llega con `?token={clerk_session_jwt}`; el Worker valida el JWT **antes** de rutear al DO y pasa `{userId, role}` en headers internos. [Suposición] Verificar el método actual de verificación de JWT de Clerk en Workers (`@clerk/backend` `verifyToken`) contra docs de Clerk.
- Rate limit de chat: 1 msg/seg por conexión, en memoria del DO.
- `viewers` se emite con debounce de 2s, no en cada join/leave.
- El evento `pinned` incluye el producto completo (denormalizado) para que el viewer no haga fetch adicional — el momento del pin es el pico de tráfico.

---

## 6. API Worker (Hono)

Middleware global: CORS restringido al dominio del front + verificación Clerk JWT (excepto rutas públicas marcadas).

```
POST   /api/streams                 (streamer) crea stream → llama CF API live_inputs, inserta en D1
GET    /api/streams?status=live     (público) lobby
GET    /api/streams/:id             (público) detalle + productos asignados
POST   /api/streams/:id/start       (streamer) status→live, notifica DO
POST   /api/streams/:id/end         (streamer) status→ended, DO broadcast stream_ended, CF: opcionalmente borrar live input
GET    /api/streams/:id/ws          upgrade WebSocket → DO idFromName(:id)

POST   /api/products                (streamer) multipart: datos + imagen → R2.put(), D1 insert
GET    /api/products?mine=1         (streamer)
POST   /api/streams/:id/products    (streamer) asigna catálogo al stream

POST   /api/checkout                (buyer) { streamId, productId, qty }
                                    Fase 1: valida stock, decrementa, crea order mock_paid,
                                            avisa al DO → broadcast {t:'stock'}
                                    Fase 2: crea preference MercadoPago, retorna init_point
POST   /api/webhooks/mercadopago    Fase 2: confirma pago → order.paid
GET    /api/orders?streamId=        (streamer) ventas del stream en vivo
```

Comunicación Worker → DO para eventos (stock, end): `env.STREAM_ROOM.get(id).fetch('https://do/internal/event', {...})` con un secreto interno en header. [Suposición] Si la versión de runtime lo permite, preferir RPC de DO (métodos públicos sobre `DurableObject`); verificar disponibilidad en la versión actual de wrangler.

### wrangler.jsonc (api)

```jsonc
{
  "name": "live-commerce-api",
  "main": "src/index.ts",
  "compatibility_date": "2026-06-01",
  "durable_objects": { "bindings": [{ "name": "STREAM_ROOM", "class_name": "StreamRoom" }] },
  "migrations": [{ "tag": "v1", "new_sqlite_classes": ["StreamRoom"] }],
  "d1_databases": [{ "binding": "DB", "database_name": "livecommerce", "database_id": "<crear con wrangler d1 create>" }],
  "r2_buckets": [{ "binding": "ASSETS", "bucket_name": "livecommerce-assets" }]
}
```

Secrets (via `wrangler secret put`): `CF_ACCOUNT_ID`, `CF_STREAM_API_TOKEN` (token con permiso Stream:Edit), `CLERK_SECRET_KEY`, `INTERNAL_DO_SECRET`, fase 2: `MP_ACCESS_TOKEN`.

---

## 7. Frontend Nuxt 3

- `ssr: false`. [Probable] SSR sobre Workers con Nitro preset `cloudflare_module` funciona, pero para MVP la SPA elimina una clase entera de bugs de hidratación con WebRTC. No gastar tiempo ahí.
- **useWhipBroadcast**: basarse en el `WHIPClient.js` oficial de Cloudflare (~100 líneas): `getUserMedia` 720p/30fps → `RTCPeerConnection` (`bundlePolicy: 'max-bundle'`, sin iceServers propios: [Seguro] Cloudflare maneja ICE) → POST del offer SDP a `whip_url`. Guardar la resource URL de la respuesta para DELETE al cortar.
- **useWhepPlayer**: mismo patrón inverso contra `whep_url`, `<video autoplay playsinline muted>` (autoplay policies exigen muted inicial + botón de unmute).
- **useStreamRoom**: WS con reconexión exponencial (1s→30s) y re-suscripción; al reconectar, pedir estado actual (`{t:'sync'}` — agregarlo al protocolo).
- Vista viewer: video full-bleed, chat overlay, y la card del producto pineado con CTA "Comprar" → bottom sheet de checkout. La card debe renderizar desde el payload del WS sin fetch (ver sección 5).
- Vista streamer: preview local, lista de productos del stream con botón "Pin", contador de viewers, feed de ventas en vivo (polling 5s a /api/orders o push por WS).

---

## 8. Fases de ejecución

**Fase 0 — Spike WHIP/WHEP** (0.5 día): sección 3. Gate: si falla → LiveKit.

**Fase 1 — Núcleo transmisión + sala** (2-3 días)
1. Scaffold monorepo, wrangler, D1 migrations, Clerk en Nuxt y Worker.
2. CRUD streams + integración CF live_inputs.
3. DO StreamRoom con hibernación: chat + viewers.
4. Broadcast (studio) y playback (watch) funcionando entre dos dispositivos.
✅ Criterio: streamear desde un notebook, ver desde un celular en 4G con chat en vivo, latencia <2s.

**Fase 2 — Commerce** (2 días)
1. CRUD productos + upload a R2.
2. Pin/unpin desde studio → card en viewer.
3. Checkout mock con decremento de stock atómico + broadcast de stock.
4. Feed de ventas en studio.
✅ Criterio: comprar (mock) durante el stream y ver el stock bajar en todos los viewers en <1s.

**Fase 3 — Pagos reales + pulido** (2-3 días)
1. MercadoPago Checkout Pro: crear preference en /api/checkout, webhook de confirmación, estados pending→paid. [Suposición] Verificar payload actual del webhook MP y firma; no confiar en memoria.
2. Notificación Telegram "stream en vivo" a seguidores (tabla followers, opcional).
3. Manejo de fin de stream: broadcast, cierre de sala, resumen de ventas.

**Fuera de alcance del MVP** (anotar como backlog, no construir): replay shoppable, simulcast a redes, multi-cámara/OBS, cupones, subastas, moderación con ML, panel admin.

---

## 9. Riesgos técnicos y mitigaciones

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Beta WHIP inestable / grabación rota | Media-alta | Gate en Fase 0; plan B LiveKit documentado; `ingest_type` en schema desacopla |
| WHEP sin fallback HLS → viewers en redes hostiles a WebRTC (corporativas) | Media | Aceptado para MVP; anotar métricas de fallo de conexión desde el día 1 |
| Stock race en flash sale | Media | UPDATE condicional en D1 (sección 4); mover a DO si hay contención real |
| Costos DO por WS abiertos | Baja | Hibernation API obligatoria; sin timers activos en idle |
| Clerk JWT en upgrade WS | Baja | Validar en Worker antes del DO; nunca dentro del DO |

---

## 10. Variables de entorno consolidadas

```
# Worker (secrets)
CF_ACCOUNT_ID=
CF_STREAM_API_TOKEN=          # scope: Stream:Edit
CLERK_SECRET_KEY=
INTERNAL_DO_SECRET=
MP_ACCESS_TOKEN=              # fase 2

# Nuxt (públicas)
NUXT_PUBLIC_API_BASE=https://live-commerce-api.<subdominio>.workers.dev
NUXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
```
