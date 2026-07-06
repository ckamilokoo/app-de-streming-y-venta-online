# Live Commerce MVP

Streaming + venta en vivo. Plan completo en `PLAN-live-commerce-mvp.md`.

**Stack**: Nuxt 4 SPA (`apps/web`) + FastAPI/uv (`apps/api`) + SQLite. Video: Cloudflare Stream (WHIP/WHEP). Realtime (chat/pins/stock): WebSockets FastAPI con sala en memoria.

## Modo mock (sin cuentas externas)

`apps/api/.env` con `CF_MOCK=1` y `AUTH_MOCK=1` (default). Todo funciona salvo el video real: el player muestra placeholder y el studio usa preview local de cámara. Login mock: cualquier nombre + rol desde el header de la web.

Cuando existan cuentas: poner `CF_MOCK=0` + credenciales Cloudflare (video real) y `AUTH_MOCK=0` + Clerk (auth real). Los streams creados en mock guardan URLs `mock://` — crear streams nuevos tras el cambio.

## Correr en dev

```bash
# API (puerto 8000)
cd apps/api
cp .env.example .env   # solo la primera vez
uv sync                # solo la primera vez
uv run uvicorn app.main:app --reload --port 8000

# Web (puerto 3000)
pnpm install           # solo la primera vez, desde la raíz
pnpm dev:web
```

Abrir http://localhost:3000 — entrar como `Streamer`, crear producto y stream en Studio, abrir la consola, salir en vivo. En otra ventana (incógnito) entrar como `Comprador` y comprar desde `/watch/...`.

## Estructura

```
apps/
├── api/          # FastAPI — routers/{streams,products,checkout,orders}, room.py (sala WS), cf_stream.py, auth.py
└── web/          # Nuxt 4 — pages/{index,watch,studio}, composables/{useWhipBroadcast,useWhepPlayer,useStreamRoom,...}
```

## Pendiente (según plan)

- Fase 0: spike WHIP/WHEP real (requiere cuenta Cloudflare Stream, ~$5/mes)
- Clerk real (AUTH_MOCK=0)
- Fase 2/3: MercadoPago, Telegram, R2 para imágenes (dev usa disco local)
- Deploy: web → Workers Assets / Pages; api → Fly.io o Railway
