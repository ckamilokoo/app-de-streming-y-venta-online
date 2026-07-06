from pathlib import Path

import aiosqlite

from .config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

_conn: aiosqlite.Connection | None = None


async def init_db() -> None:
    global _conn
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _conn = await aiosqlite.connect(db_path)
    _conn.row_factory = aiosqlite.Row
    await _conn.execute("PRAGMA foreign_keys = ON")
    await _conn.execute("PRAGMA journal_mode = WAL")
    await _run_migrations(_conn)


async def close_db() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None


def get_db() -> aiosqlite.Connection:
    assert _conn is not None, "DB no inicializada (init_db)"
    return _conn


async def _run_migrations(conn: aiosqlite.Connection) -> None:
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)"
    )
    cur = await conn.execute("SELECT name FROM schema_migrations")
    applied = {row["name"] for row in await cur.fetchall()}
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if sql_file.name in applied:
            continue
        await conn.executescript(sql_file.read_text(encoding="utf-8"))
        await conn.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)", (sql_file.name,)
        )
        await conn.commit()
