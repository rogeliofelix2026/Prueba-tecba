"""
Administra los pools de conexión PostgreSQL usados por la aplicación
y por scripts de ingesta.

FastAPI utiliza el pool asíncrono.
Los scripts e ingestas utilizan el pool síncrono.

Ambos registran pgvector al crear cada conexión.
"""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from pgvector.psycopg import register_vector, register_vector_async
from psycopg import AsyncConnection, Connection
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from app.core.config import settings


_async_pool: AsyncConnectionPool | None = None
_sync_pool: ConnectionPool | None = None


async def configure_async_connection(
    conn: AsyncConnection,
) -> None:
    await register_vector_async(conn)


def configure_sync_connection(conn: Connection) -> None:
    register_vector(conn)


async def open_pool() -> None:
    global _async_pool

    if _async_pool is not None:
        return

    pool = AsyncConnectionPool(
        conninfo=settings.require_database_url(),
        min_size=settings.db_min_size,
        max_size=settings.db_max_size,
        timeout=settings.db_timeout_seconds,
        open=False,
        configure=configure_async_connection,
    )

    try:
        await pool.open(
            wait=True,
            timeout=settings.db_timeout_seconds,
        )
    except Exception:
        await pool.close()
        raise

    _async_pool = pool


async def close_pool() -> None:
    global _async_pool

    pool = _async_pool
    _async_pool = None

    if pool is not None:
        await pool.close()


def async_pool() -> AsyncConnectionPool:
    if _async_pool is None:
        raise RuntimeError(
            "El pool asíncrono no está abierto."
        )

    return _async_pool


def open_sync_pool() -> None:
    global _sync_pool

    if _sync_pool is not None:
        return

    pool = ConnectionPool(
        conninfo=settings.require_database_url(),
        min_size=settings.db_min_size,
        max_size=settings.db_max_size,
        timeout=settings.db_timeout_seconds,
        open=False,
        configure=configure_sync_connection,
    )

    try:
        pool.open(
            wait=True,
            timeout=settings.db_timeout_seconds,
        )
    except Exception:
        pool.close()
        raise

    _sync_pool = pool


def close_sync_pool() -> None:
    global _sync_pool

    pool = _sync_pool
    _sync_pool = None

    if pool is not None:
        pool.close()


@asynccontextmanager
async def connection() -> AsyncGenerator[AsyncConnection, None]:
    pool = async_pool()

    async with pool.connection() as conn:
        yield conn


@contextmanager
def sync_connection() -> Generator[Connection, None, None]:
    pool = _sync_pool

    if pool is None:
        raise RuntimeError(
            "El pool síncrono no está abierto."
        )

    with pool.connection() as conn:
        yield conn