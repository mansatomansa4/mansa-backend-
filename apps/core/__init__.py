"""Core app initialization and utilities (Supabase helper)."""

from __future__ import annotations

import os
from typing import Optional

try:
    from supabase import Client, create_client  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in some envs
    create_client = None  # type: ignore
    Client = object  # type: ignore


def get_supabase_client() -> Optional["Client"]:
    """Return a Supabase client if environment variables are configured.

    Uses service role key if available (server-side secure), else anon key.
    Returns None if supabase lib or env vars are not present.
    """
    if create_client is None:
        return None
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


__all__ = ["get_supabase_client"]
# End of module
