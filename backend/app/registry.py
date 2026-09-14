"""
Single import point for every model, so Alembic sees the full metadata.

Every new model module must be imported here, otherwise `alembic revision
--autogenerate` will not see its table and will silently produce an empty
migration.
"""

from app.core.database import Base

__all__ = ["Base"]
