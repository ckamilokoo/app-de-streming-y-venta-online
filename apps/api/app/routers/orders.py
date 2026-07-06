from fastapi import APIRouter, Depends, HTTPException

from ..auth import User, get_current_user, require_streamer
from ..db import get_db
from ..serializers import order_row

router = APIRouter(prefix="/api", tags=["orders"])


@router.get("/orders")
async def list_orders(
    stream_id: str | None = None,
    mine: int = 0,
    user: User = Depends(get_current_user),
):
    db = get_db()

    # Historial del comprador (cualquier usuario autenticado)
    if mine:
        cur = await db.execute(
            """SELECT o.*, p.name AS product_name, p.image_key,
                      s.title AS stream_title, u.display_name AS streamer_name
               FROM orders o
               JOIN products p ON p.id = o.product_id
               JOIN streams s ON s.id = o.stream_id
               JOIN users u ON u.id = s.streamer_id
               WHERE o.buyer_id = ? ORDER BY o.created_at DESC""",
            (user.id,),
        )
        result = []
        for r in await cur.fetchall():
            data = order_row(r)
            data["productName"] = r["product_name"]
            data["streamTitle"] = r["stream_title"]
            data["streamerName"] = r["streamer_name"]
            result.append(data)
        return result

    # Ventas de un stream (solo el dueño)
    if not stream_id:
        raise HTTPException(422, "Falta stream_id o mine=1")
    if user.role not in ("streamer", "admin"):
        raise HTTPException(403, "Requiere rol streamer")
    cur = await db.execute("SELECT streamer_id FROM streams WHERE id = ?", (stream_id,))
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Stream no existe")
    if row["streamer_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "No es tu stream")
    cur = await db.execute(
        """SELECT o.*, p.name AS product_name, u.display_name AS buyer_name
           FROM orders o
           JOIN products p ON p.id = o.product_id
           JOIN users u ON u.id = o.buyer_id
           WHERE o.stream_id = ? ORDER BY o.created_at DESC""",
        (stream_id,),
    )
    result = []
    for r in await cur.fetchall():
        data = order_row(r)
        data["productName"] = r["product_name"]
        data["buyerName"] = r["buyer_name"]
        result.append(data)
    return result


@router.get("/studio/stats")
async def studio_stats(user: User = Depends(require_streamer)):
    db = get_db()
    cur = await db.execute(
        """SELECT COUNT(*) AS n, COALESCE(SUM(o.amount_clp), 0) AS total,
                  COALESCE(SUM(o.qty), 0) AS units
           FROM orders o JOIN streams s ON s.id = o.stream_id
           WHERE s.streamer_id = ?""",
        (user.id,),
    )
    sales = await cur.fetchone()
    cur = await db.execute(
        "SELECT COUNT(*) AS n FROM streams WHERE streamer_id = ?", (user.id,)
    )
    streams_count = (await cur.fetchone())["n"]
    cur = await db.execute(
        "SELECT COUNT(*) AS n FROM products WHERE streamer_id = ?", (user.id,)
    )
    products_count = (await cur.fetchone())["n"]
    return {
        "totalClp": sales["total"],
        "ordersCount": sales["n"],
        "unitsSold": sales["units"],
        "streamsCount": streams_count,
        "productsCount": products_count,
    }
