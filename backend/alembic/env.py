"""
backend/alembic/env.py
======================
Alembic migration environment for Razorpay AI Risk Manager.
Supports both SQLite (dev) and PostgreSQL (production via Render).

Usage:
  # Apply all pending migrations:
  cd backend && alembic upgrade head

  # Create a new migration after model changes:
  cd backend && alembic revision --autogenerate -m "describe_change"

  # Downgrade one step:
  cd backend && alembic downgrade -1
"""
from logging.config import fileConfig
import os
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend/ to sys.path so app imports resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the SQLAlchemy metadata for all models
from app.core.database import Base  # noqa: E402
from app.models import entities  # noqa: E402, F401 — imports all entity classes for metadata

# Alembic Config object (accesses the .ini file)
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use our app's Base metadata so alembic can auto-generate migrations
target_metadata = Base.metadata

# Override sqlalchemy.url from the environment DATABASE_URL
# This allows render.yaml to inject the PostgreSQL connection string at runtime.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./risk_manager.db")

# Render PostgreSQL URLs use postgres:// prefix — SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL scripts without a live DB connection)."""
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
    """Run migrations in 'online' mode (direct DB connection, applies changes immediately)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare column types for more accurate autogenerate
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
