import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.database import Base
from app.models import User, Contact

# Load environment variables
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Connect the models' metadata to Alembic
target_metadata = Base.metadata

# Use the synchronous database URL for Alembic migrations
config.set_main_option("sqlalchemy.url", os.getenv("SYNC_DATABASE_URL"))


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures Alembic to generate SQL statements to a file without
    requiring a live database connection.

    This function retrieves the synchronous database URL and sets up
    the context configuration with literal binds for parameterized queries.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Configures Alembic to apply migrations directly to a live database
    connection.

    This function uses `engine_from_config` to create an engine and establishes
    a connection with the specified database, allowing Alembic to perform migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
