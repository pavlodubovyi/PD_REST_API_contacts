import os
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import context
from app.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = os.getenv("DATABASE_URL")
connectable = create_async_engine(DATABASE_URL, echo=True)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(connection=conn, target_metadata=target_metadata)
        )
        await connection.run_sync(lambda conn: context.run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
