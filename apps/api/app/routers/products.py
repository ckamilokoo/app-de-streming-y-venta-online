import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..auth import User, require_streamer
from ..db import get_db
from ..room import room_manager
from ..serializers import product_row
from ..storage import save_image

router = APIRouter(prefix="/api", tags=["products"])


async def _owned_product(product_id: str, user: User):
    db = get_db()
    cur = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Producto no existe")
    if row["streamer_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "No es tu producto")
    return row


async def _broadcast_stock_to_live_rooms(product_id: str, stock: int) -> None:
    """Empuja stock nuevo a toda sala en vivo que tenga este producto asignado."""
    db = get_db()
    cur = await db.execute(
        """SELECT s.id FROM streams s
           JOIN stream_products sp ON sp.stream_id = s.id
           WHERE sp.product_id = ? AND s.status = 'live'""",
        (product_id,),
    )
    for r in await cur.fetchall():
        await room_manager.stock_update(r["id"], product_id, stock)


def _unpin_everywhere(product_id: str) -> list[str]:
    return [
        sid
        for sid, room in room_manager.rooms.items()
        if room.pinned_product and room.pinned_product.get("id") == product_id
    ]


@router.post("/products")
async def create_product(
    name: str = Form(min_length=1, max_length=120),
    price_clp: int = Form(gt=0),
    stock: int = Form(ge=0),
    description: str = Form(default=""),
    image: UploadFile | None = None,
    user: User = Depends(require_streamer),
):
    image_key = None
    if image is not None:
        image_key = await save_image(image)
        if image_key is None:
            raise HTTPException(415, "Imagen debe ser jpeg/png/webp")
    product_id = uuid.uuid4().hex
    db = get_db()
    await db.execute(
        """INSERT INTO products (id, streamer_id, name, description, price_clp, stock, image_key)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (product_id, user.id, name, description, price_clp, stock, image_key),
    )
    await db.commit()
    cur = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    return product_row(await cur.fetchone())


@router.get("/products")
async def list_products(mine: int = 1, user: User = Depends(require_streamer)):
    db = get_db()
    cur = await db.execute(
        "SELECT * FROM products WHERE streamer_id = ? ORDER BY rowid DESC", (user.id,)
    )
    return [product_row(r) for r in await cur.fetchall()]


class UpdateProduct(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    price_clp: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)


@router.patch("/products/{product_id}")
async def update_product(
    product_id: str, body: UpdateProduct, user: User = Depends(require_streamer)
):
    await _owned_product(product_id, user)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(422, "Nada que actualizar")
    db = get_db()
    sets = ", ".join(f"{k} = ?" for k in fields)
    await db.execute(
        f"UPDATE products SET {sets} WHERE id = ?", (*fields.values(), product_id)
    )
    await db.commit()
    if "stock" in fields:
        await _broadcast_stock_to_live_rooms(product_id, fields["stock"])
    cur = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    return product_row(await cur.fetchone())


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: User = Depends(require_streamer)):
    await _owned_product(product_id, user)
    db = get_db()
    cur = await db.execute(
        "SELECT COUNT(*) AS n FROM orders WHERE product_id = ?", (product_id,)
    )
    if (await cur.fetchone())["n"] > 0:
        raise HTTPException(409, "Tiene ventas asociadas; no se puede eliminar")
    for sid in _unpin_everywhere(product_id):
        await room_manager.pin(sid, None)
    await db.execute("DELETE FROM stream_products WHERE product_id = ?", (product_id,))
    await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    await db.commit()
    return {"ok": True}


class AssignProducts(BaseModel):
    product_ids: list[str]


@router.post("/streams/{stream_id}/products")
async def assign_products(
    stream_id: str, body: AssignProducts, user: User = Depends(require_streamer)
):
    db = get_db()
    cur = await db.execute("SELECT streamer_id FROM streams WHERE id = ?", (stream_id,))
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Stream no existe")
    if row["streamer_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "No es tu stream")
    for pid in body.product_ids:
        cur = await db.execute(
            "SELECT id FROM products WHERE id = ? AND streamer_id = ?",
            (pid, user.id),
        )
        if await cur.fetchone() is None:
            raise HTTPException(404, f"Producto {pid} no existe o no es tuyo")
        await db.execute(
            "INSERT OR IGNORE INTO stream_products (stream_id, product_id) VALUES (?, ?)",
            (stream_id, pid),
        )
    await db.commit()
    return {"ok": True}


@router.delete("/streams/{stream_id}/products/{product_id}")
async def unassign_product(
    stream_id: str, product_id: str, user: User = Depends(require_streamer)
):
    db = get_db()
    cur = await db.execute("SELECT streamer_id FROM streams WHERE id = ?", (stream_id,))
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "Stream no existe")
    if row["streamer_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "No es tu stream")
    room = room_manager.rooms.get(stream_id)
    if room and room.pinned_product and room.pinned_product.get("id") == product_id:
        await room_manager.pin(stream_id, None)
    await db.execute(
        "DELETE FROM stream_products WHERE stream_id = ? AND product_id = ?",
        (stream_id, product_id),
    )
    await db.commit()
    return {"ok": True}
