import uuid
from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from .config import settings


@dataclass
class LiveInput:
    uid: str
    whip_url: str
    whep_url: str


async def create_live_input(name: str) -> LiveInput:
    if settings.cf_mock:
        uid = f"mock-{uuid.uuid4().hex[:12]}"
        return LiveInput(
            uid=uid,
            whip_url=f"mock://whip/{uid}",
            whep_url=f"mock://whep/{uid}",
        )

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{settings.cf_account_id}/stream/live_inputs"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {settings.cf_stream_api_token}"},
            json={
                "meta": {"name": name},
                "recording": {"mode": "automatic"},
            },
            timeout=15,
        )
    if resp.status_code != 200:
        raise HTTPException(502, f"Cloudflare Stream error: {resp.text[:300]}")
    result = resp.json()["result"]
    return LiveInput(
        uid=result["uid"],
        whip_url=result["webRTC"]["url"],
        whep_url=result["webRTCPlayback"]["url"],
    )


async def delete_live_input(uid: str) -> None:
    if settings.cf_mock:
        return
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{settings.cf_account_id}/stream/live_inputs/{uid}"
    )
    async with httpx.AsyncClient() as client:
        await client.delete(
            url,
            headers={"Authorization": f"Bearer {settings.cf_stream_api_token}"},
            timeout=15,
        )
