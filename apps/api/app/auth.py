import base64
import json
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException

from .config import settings
from .db import get_db

_jwks_client: jwt.PyJWKClient | None = None


@dataclass
class User:
    id: str
    name: str
    role: str  # buyer | streamer | admin


async def verify_token(token: str) -> User:
    """Valida token (mock dev o JWT Clerk) y hace upsert del usuario en DB."""
    if settings.auth_mock:
        user = _parse_dev_token(token)
    else:
        user = await _verify_clerk_jwt(token)
    await _upsert_user(user)
    return user


def _parse_dev_token(token: str) -> User:
    # Formato: "dev." + base64url(JSON {id, name, role})
    if not token.startswith("dev."):
        raise HTTPException(401, "Token dev inválido")
    try:
        payload = token[4:]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        role = data.get("role", "buyer")
        if role not in ("buyer", "streamer", "admin"):
            raise ValueError(f"rol inválido: {role}")
        return User(id=data["id"], name=data.get("name", "anon"), role=role)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Token dev malformado")


async def _verify_clerk_jwt(token: str) -> User:
    global _jwks_client
    if not settings.clerk_jwks_url:
        raise HTTPException(500, "CLERK_JWKS_URL no configurada")
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(settings.clerk_jwks_url)
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer or None,
            options={"verify_aud": False},
        )
    except Exception:
        raise HTTPException(401, "JWT inválido")
    user_id = claims["sub"]
    name = claims.get("name") or claims.get("first_name") or "usuario"
    # Rol vive en nuestra DB, no en el JWT
    db = get_db()
    cur = await db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = await cur.fetchone()
    role = row["role"] if row else "buyer"
    return User(id=user_id, name=name, role=role)


async def _upsert_user(user: User) -> None:
    db = get_db()
    if settings.auth_mock:
        # En mock el rol viene en el token: mantenerlo sincronizado
        await db.execute(
            """INSERT INTO users (id, role, display_name) VALUES (?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET role = excluded.role,
                                             display_name = excluded.display_name""",
            (user.id, user.role, user.name),
        )
    else:
        await db.execute(
            """INSERT INTO users (id, display_name) VALUES (?, ?)
               ON CONFLICT(id) DO UPDATE SET display_name = excluded.display_name""",
            (user.id, user.name),
        )
    await db.commit()


async def get_current_user(authorization: str = Header(default="")) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Falta Authorization: Bearer")
    return await verify_token(authorization[7:])


async def get_optional_user(
    authorization: str = Header(default=""),
) -> User | None:
    if not authorization.startswith("Bearer "):
        return None
    try:
        return await verify_token(authorization[7:])
    except HTTPException:
        return None


async def require_streamer(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("streamer", "admin"):
        raise HTTPException(403, "Requiere rol streamer")
    return user
