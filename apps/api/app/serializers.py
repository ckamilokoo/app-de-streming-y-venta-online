from typing import Any

import aiosqlite

from .storage import image_url


def stream_row(row: aiosqlite.Row, include_whip: bool = False) -> dict[str, Any]:
    data = {
        "id": row["id"],
        "streamerId": row["streamer_id"],
        "title": row["title"],
        "status": row["status"],
        "ingestType": row["ingest_type"],
        "whepUrl": row["whep_url"],
        "scheduledAt": row["scheduled_at"],
        "startedAt": row["started_at"],
        "endedAt": row["ended_at"],
    }
    if include_whip:
        data["whipUrl"] = row["whip_url"]
    return data


def product_row(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "streamerId": row["streamer_id"],
        "name": row["name"],
        "description": row["description"],
        "priceClp": row["price_clp"],
        "stock": row["stock"],
        "imageUrl": image_url(row["image_key"]),
    }


def order_row(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "streamId": row["stream_id"],
        "productId": row["product_id"],
        "buyerId": row["buyer_id"],
        "qty": row["qty"],
        "amountClp": row["amount_clp"],
        "paymentStatus": row["payment_status"],
        "createdAt": row["created_at"],
    }
