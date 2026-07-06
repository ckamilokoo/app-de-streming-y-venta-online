import time
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from ..auth import User, get_optional_user, require_streamer, verify_token
from ..cf_stream import create_live_input
from ..db import get_db
from ..room import room_manager
from ..serializers import product_row, stream_row
from ..storage import image_url

router = APIRouter(prefix="/api/streams", tags=["streams"])


class CreateStream(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    scheduled_at: int | None = None


class PinBody(BaseModel):
    product_id: str | None = None  # None => unpin


@router.post("")
async def create_stream(body: CreateStream, user: User = Depends(require_streamer)):
    stream_id = uuid.uuid4().hex
    live_input = await create_live_input(f"stream-{stream_id}")
    db = get_db()
    await db.execute(
        """INSERT INTO streams
           (id, streamer_id, title, cf_live_input_uid, whip_url, whep_url, scheduled_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            stream_id,
            user.id,
            body.title,
            live_input.uid,
            live_input.whip_url,
            live_input.whep_url,
            body.scheduled_at,
        ),
    )
    await db.commit()
    cur = await db.execute("SELECT * FROM streams WHERE id = ?", (stream_id,))
    row = await cur.fetchone()
    return stream_row(row, include_whip=True)


@router.get("")
async def list_streams(status: str | None = None, mine: int = 0,
                       user: User | None = Depends(get_optional_user)):
    db = get_db()
    query = """SELECT s.*, u.display_name AS streamer_name,
               (SELECT COUNT(*) FROM stream_products sp WHERE sp.stream_id = s.id) AS products_count
               FROM streams s JOIN users u ON u.id = s.streamer_id"""
    conds, params = [], []
    if status:
        conds.append("s.status = ?")
        params.append(status)
    if mine:
        if user is None:
            raise HTTPException(401, "Requiere auth para mine=1")
        conds.append("s.streamer_id = ?")
        params.append(user.id)
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY s.started_at DESC NULLS LAST, s.scheduled_at DESC NULLS LAST"
    cur = await db.execute(query, params)
    rows = await cur.fetchall()
    result = []
    for r in rows:
        include_whip = user is not None and r["streamer_id"] == user.id
        data = stream_row(r, include_whip=include_whip)
        data["streamerName"] = r["streamer_name"]
        data["productsCount"] = r["products_count"]
        if r["status"] == "live":
            data["viewers"] = room_manager.viewer_count(r["id"])
        result.append(data)
    return result


@router.get("/{stream_id}")
async def get_stream(stream_id: str, user: User | None = Depends(get_optional_user)):
    db = get_db()
    cur = await db.execute(
        """SELECT s.*, u.display_name AS streamer_name
           FROM streams s JOIN users u ON u.id = s.streamer_id WHERE s.id = ?""",
        (stream_id,),
    )
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Stream no existe")
    is_owner = user is not None and row["streamer_id"] == user.id
    data = stream_row(row, include_whip=is_owner)
    data["streamerName"] = row["streamer_name"]
    cur = await db.execute(
        """SELECT p.* FROM products p
           JOIN stream_products sp ON sp.product_id = p.id
           WHERE sp.stream_id = ?""",
        (stream_id,),
    )
    data["products"] = [product_row(r) for r in await cur.fetchall()]
    return data


async def _owned_stream(stream_id: str, user: User):
    db = get_db()
    cur = await db.execute("SELECT * FROM streams WHERE id = ?", (stream_id,))
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Stream no existe")
    if row["streamer_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "No es tu stream")
    return row


@router.post("/{stream_id}/start")
async def start_stream(stream_id: str, user: User = Depends(require_streamer)):
    row = await _owned_stream(stream_id, user)
    if row["status"] == "ended":
        raise HTTPException(409, "Stream ya terminó")
    db = get_db()
    await db.execute(
        "UPDATE streams SET status = 'live', started_at = ? WHERE id = ?",
        (int(time.time()), stream_id),
    )
    await db.commit()
    return {"ok": True, "status": "live"}


@router.post("/{stream_id}/end")
async def end_stream(stream_id: str, user: User = Depends(require_streamer)):
    await _owned_stream(stream_id, user)
    # Leer peak ANTES de cerrar la sala (end() destruye el room)
    peak = room_manager.peak_viewers(stream_id)
    db = get_db()
    await db.execute(
        "UPDATE streams SET status = 'ended', ended_at = ?, peak_viewers = ? WHERE id = ?",
        (int(time.time()), peak, stream_id),
    )
    await db.commit()
    await room_manager.end(stream_id)
    return {"ok": True, "status": "ended"}


@router.get("/{stream_id}/summary")
async def stream_summary(stream_id: str, user: User = Depends(require_streamer)):
    row = await _owned_stream(stream_id, user)
    db = get_db()
    cur = await db.execute(
        """SELECT COUNT(*) AS n, COALESCE(SUM(amount_clp), 0) AS total,
                  COALESCE(SUM(qty), 0) AS units
           FROM orders WHERE stream_id = ?""",
        (stream_id,),
    )
    agg = await cur.fetchone()
    cur = await db.execute(
        """SELECT p.id, p.name, SUM(o.qty) AS units, SUM(o.amount_clp) AS total
           FROM orders o JOIN products p ON p.id = o.product_id
           WHERE o.stream_id = ?
           GROUP BY p.id ORDER BY total DESC""",
        (stream_id,),
    )
    by_product = [
        {"productId": r["id"], "name": r["name"], "units": r["units"], "totalClp": r["total"]}
        for r in await cur.fetchall()
    ]
    started, ended = row["started_at"], row["ended_at"]
    duration = (ended - started) if started and ended else None
    # Stream aún en vivo: peak actual de la sala supera lo persistido
    peak = max(row["peak_viewers"], room_manager.peak_viewers(stream_id))
    return {
        "streamId": stream_id,
        "title": row["title"],
        "status": row["status"],
        "startedAt": started,
        "endedAt": ended,
        "durationSec": duration,
        "peakViewers": peak,
        "totalClp": agg["total"],
        "ordersCount": agg["n"],
        "units": agg["units"],
        "byProduct": by_product,
    }


@router.post("/{stream_id}/pin")
async def pin_product(
    stream_id: str, body: PinBody, user: User = Depends(require_streamer)
):
    await _owned_stream(stream_id, user)
    if body.product_id is None:
        await room_manager.pin(stream_id, None)
        return {"ok": True, "pinned": None}
    db = get_db()
    cur = await db.execute(
        """SELECT p.* FROM products p
           JOIN stream_products sp ON sp.product_id = p.id
           WHERE p.id = ? AND sp.stream_id = ?""",
        (body.product_id, stream_id),
    )
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Producto no asignado a este stream")
    # Payload denormalizado: el viewer renderiza la card sin fetch adicional
    product = {
        "id": row["id"],
        "name": row["name"],
        "priceClp": row["price_clp"],
        "imageUrl": image_url(row["image_key"]),
        "stock": row["stock"],
    }
    await room_manager.pin(stream_id, product)
    return {"ok": True, "pinned": product}


@router.websocket("/{stream_id}/ws")
async def stream_ws(ws: WebSocket, stream_id: str, token: str = ""):
    # Validar JWT ANTES de aceptar la conexión (regla del plan)
    try:
        user = await verify_token(token)
    except HTTPException:
        await ws.close(code=4401)
        return
    db = get_db()
    cur = await db.execute("SELECT id FROM streams WHERE id = ?", (stream_id,))
    if await cur.fetchone() is None:
        await ws.close(code=4404)
        return

    await room_manager.connect(stream_id, ws, user)
    try:
        while True:
            msg = await ws.receive_json()
            await room_manager.handle_message(stream_id, ws, user, msg)
    except WebSocketDisconnect:
        pass
    finally:
        room_manager.disconnect(stream_id, ws)
