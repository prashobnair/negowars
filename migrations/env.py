# migrations/env.py (Corrected - you provided this, but this is the confirmed correct version)

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
import asyncio
import sys
from pathlib import Path

# THIS MUST COME BEFORE alembic IMPORT
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import context
from server.config.settings import settings
from server.database import Base

# Your models' MetaData object
target_metadata = Base.metadata

# Important for async
config = context.config
fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Engine) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations(connectable: AsyncEngine) -> None:
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async."""
    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        connectable = create_async_engine(
            config.get_main_option("sqlalchemy.url"),
            poolclass=pool.NullPool,
        )

    if isinstance(connectable, AsyncEngine):
        asyncio.run(run_async_migrations(connectable))
    else:
        # Fallback for sync (shouldn't be needed)
        with connectable.connect() as connection:
            do_run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()