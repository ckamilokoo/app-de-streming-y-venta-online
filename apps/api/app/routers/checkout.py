import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import User, get_current_user
from ..db import get_db
from ..room import room_manager
from ..serializers import order_row

router = APIRouter(prefix="/api", tags=["checkout"])


class CheckoutBody(BaseModel):
    stream_id: str
    product_id: str
    qty: int = Field(default=1, ge=1, le=20)


@router.post("/checkout")
async def checkout(body: CheckoutBody, user: User = Depends(get_current_user)):
    db = get_db()
    cur = await db.execute(
        """SELECT s.status, p.price_clp
           FROM streams s
           JOIN stream_products sp ON sp.stream_id = s.id
           JOIN products p ON p.id = sp.product_id
           WHERE s.id = ? AND p.id = ?""",
        (body.stream_id, body.product_id),
    )
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Producto no disponible en este stream")
    if row["status"] != "live":
        raise HTTPException(409, "El stream no está en vivo")

    # Decremento atómico condicional — nunca leer-luego-escribir (regla del plan)
    cur = await db.execute(
        "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
        (body.qty, body.product_id, body.qty),
    )
    if cur.rowcount == 0:
        await db.commit()
        raise HTTPException(409, "Stock insuficiente")

    order_id = uuid.uuid4().hex
    amount = row["price_clp"] * body.qty
    # Fase 1: mock_paid. Fase 2: crear preference MercadoPago y estado pending.
    await db.execute(
        """INSERT INTO orders (id, stream_id, product_id, buyer_id, qty, amount_clp, payment_status)
           VALUES (?, ?, ?, ?, ?, ?, 'mock_paid')""",
        (order_id, body.stream_id, body.product_id, user.id, body.qty, amount),
    )
    await db.commit()

    cur = await db.execute("SELECT stock FROM products WHERE id = ?", (body.product_id,))
    stock = (await cur.fetchone())["stock"]
    await room_manager.stock_update(body.stream_id, body.product_id, stock)

    cur = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    return order_row(await cur.fetchone())
