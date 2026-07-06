"""Sala en memoria por stream — reemplaza el Durable Object StreamRoom del plan.

Válido para una sola instancia del API (MVP). Escalar horizontal => Redis pub/sub.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from .auth import User

CHAT_MAX_LEN = 280
CHAT_MIN_INTERVAL = 1.0  # seg entre mensajes por conexión
VIEWERS_DEBOUNCE = 2.0  # seg


@dataclass
class _Conn:
    ws: WebSocket
    user: User
    last_chat_ts: float = 0.0


@dataclass
class Room:
    stream_id: str
    conns: dict[WebSocket, _Conn] = field(default_factory=dict)
    pinned_product: dict[str, Any] | None = None
    _viewers_task: asyncio.Task | None = None


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def _room(self, stream_id: str) -> Room:
        if stream_id not in self.rooms:
            self.rooms[stream_id] = Room(stream_id=stream_id)
        return self.rooms[stream_id]

    # --- ciclo de vida de conexiones ---

    async def connect(self, stream_id: str, ws: WebSocket, user: User) -> None:
        await ws.accept()
        room = self._room(stream_id)
        room.conns[ws] = _Conn(ws=ws, user=user)
        # Estado actual solo al que entra
        await self._send(ws, {"t": "pinned", "product": room.pinned_product})
        self._schedule_viewers(room)

    def disconnect(self, stream_id: str, ws: WebSocket) -> None:
        room = self.rooms.get(stream_id)
        if room is None:
            return
        room.conns.pop(ws, None)
        if room.conns:
            self._schedule_viewers(room)
        else:
            if room._viewers_task:
                room._viewers_task.cancel()
            self.rooms.pop(stream_id, None)

    # --- mensajes cliente -> sala ---

    async def handle_message(
        self, stream_id: str, ws: WebSocket, user: User, msg: dict[str, Any]
    ) -> None:
        room = self._room(stream_id)
        t = msg.get("t")

        if t == "chat":
            conn = room.conns.get(ws)
            if conn is None:
                return
            now = time.monotonic()
            if now - conn.last_chat_ts < CHAT_MIN_INTERVAL:
                return  # rate limit: descartar
            text = str(msg.get("text", "")).strip()[:CHAT_MAX_LEN]
            if not text:
                return
            conn.last_chat_ts = now
            await self.broadcast(
                stream_id,
                {
                    "t": "chat",
                    "userId": user.id,
                    "name": user.name,
                    "text": text,
                    "ts": int(time.time() * 1000),
                },
            )

        elif t == "sync":
            await self._send(ws, {"t": "pinned", "product": room.pinned_product})
            await self._send(ws, {"t": "viewers", "count": len(room.conns)})

        # pin / unpin / end_stream llegan por HTTP (routers) — el router valida
        # rol y datos contra DB y luego llama a pin()/end(). No se aceptan por WS.

    # --- eventos servidor -> sala (llamados desde routers) ---

    async def pin(self, stream_id: str, product: dict[str, Any] | None) -> None:
        room = self._room(stream_id)
        room.pinned_product = product
        await self.broadcast(stream_id, {"t": "pinned", "product": product})

    async def stock_update(self, stream_id: str, product_id: str, stock: int) -> None:
        room = self._room(stream_id)
        if room.pinned_product and room.pinned_product.get("id") == product_id:
            room.pinned_product["stock"] = stock
        await self.broadcast(
            stream_id, {"t": "stock", "productId": product_id, "stock": stock}
        )

    async def end(self, stream_id: str) -> None:
        await self.broadcast(stream_id, {"t": "stream_ended"})
        room = self.rooms.pop(stream_id, None)
        if room is None:
            return
        if room._viewers_task:
            room._viewers_task.cancel()
        for conn in list(room.conns.values()):
            try:
                await conn.ws.close(code=1000)
            except Exception:
                pass

    # --- internos ---

    async def broadcast(self, stream_id: str, msg: dict[str, Any]) -> None:
        room = self.rooms.get(stream_id)
        if room is None:
            return
        dead: list[WebSocket] = []
        for ws in list(room.conns):
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            room.conns.pop(ws, None)

    def _schedule_viewers(self, room: Room) -> None:
        # Debounce: un solo broadcast de viewers cada VIEWERS_DEBOUNCE seg
        if room._viewers_task and not room._viewers_task.done():
            return
        room._viewers_task = asyncio.create_task(self._emit_viewers(room))

    async def _emit_viewers(self, room: Room) -> None:
        await asyncio.sleep(VIEWERS_DEBOUNCE)
        await self.broadcast(room.stream_id, {"t": "viewers", "count": len(room.conns)})

    async def _send(self, ws: WebSocket, msg: dict[str, Any]) -> None:
        try:
            await ws.send_json(msg)
        except Exception:
            pass


room_manager = RoomManager()
