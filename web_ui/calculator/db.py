"""
db.py — process-wide IngredientsDatabase singleton.

The engine's IngredientsDatabase loads CSVs and is read-only at runtime, so a
single instance is shared across all requests (loaded lazily on first use).
"""
from alchemy.database import IngredientsDatabase

_DB = None


def get_db():
    """Return the shared IngredientsDatabase, loading it on first call."""
    global _DB
    if _DB is None:
        _DB = IngredientsDatabase()
    return _DB
