"""Dependency helpers that expose read/write DB session generators.

These wrappers provide application-friendly names for injection into FastAPI
endpoints: `get_db_write` (default) and `get_db_read` for read-only routes.
"""

from .database import get_read_session, get_write_session


# Default `get_db` yields a write session (suitable for endpoints that perform writes).
# Use `get_db_read` in read-only endpoints to route reads to read replica when configured.

def get_db_write():
    """Yield a write-capable DB session for FastAPI dependency injection."""
    yield from get_write_session()


def get_db_read():
    """Yield a read-only DB session for FastAPI dependency injection."""
    yield from get_read_session()


# Backwards compat alias
get_db = get_db_write