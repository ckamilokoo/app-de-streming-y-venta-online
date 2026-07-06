import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth import User, require_streamer
from ..db import get_db
from ..serializers import product_row
from ..storage import save_image

router = APIRouter(prefix="/api", tags=["products"])


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
