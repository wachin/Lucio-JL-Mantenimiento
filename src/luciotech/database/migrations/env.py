"""Alembic configuration para migraciones de base de datos."""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from luciotech.database.models import Base
from luciotech.config import get_db_path

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
