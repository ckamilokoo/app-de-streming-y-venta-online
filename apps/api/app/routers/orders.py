from fastapi import APIRouter, Depends, HTTPException

from ..auth import User, require_streamer
from ..db import get_db
from ..serializers import order_row

router = APIRouter(prefix="/api", tags=["orders"])


@router.get("/orders")
async def list_orders(stream_id: str, user: User = Depends(require_streamer)):
    db = get_db()
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
