
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.db.base import Base
import app.models


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# SQLALCHEMY MODEL METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# EXTERNAL TABLES
# Tables managed outside application SQLAlchemy metadata.
# Alembic must not propose dropping these tables.
# ============================================================

EXTERNAL_TABLES = {
    "checkpoints",
    "checkpoint_writes",
    "checkpoint_blobs",
    "checkpoint_migrations",
    "policy_vector_chunks",
}


def include_object(
    object,
    name,
    type_,
    reflected,
    compare_to
):
    """
    Exclude externally managed tables from Alembic
    autogenerate comparison.

    This protects LangGraph checkpoint tables and
    the policy vector table.
    """

    if (
        type_ == "table"
        and reflected
        and name in EXTERNAL_TABLES
    ):
        return False

    return True


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# MIGRATION ENTRY POINT
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
