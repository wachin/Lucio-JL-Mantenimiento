"""Conexión y gestión de la base de datos."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine

from luciotech.config import get_db_path

logger = logging.getLogger(__name__)

_engine = None
_session_factory = None


def get_engine() -> Engine:
    """Obtener el motor de base de datos (singleton)."""
    global _engine
    if _engine is None:
        db_path = get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{db_path}"
        _engine = create_engine(url, echo=False)

        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info("Base de datos conectada: %s", db_path)
    return _engine


def get_session_factory() -> sessionmaker:
    """Obtener la fábrica de sesiones."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def get_session() -> Session:
    """Obtener una nueva sesión."""
    return get_session_factory()()


def init_db() -> None:
    """Inicializar la base de datos y actualizar esquemas anteriores."""
    from luciotech.database.models import Base  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(engine)
    _upgrade_legacy_schema(engine)
    logger.info("Tablas creadas/verificadas")


def _upgrade_legacy_schema(engine: Engine) -> None:
    """Aplicar cambios aditivos necesarios en bases creadas anteriormente.

    ``MetaData.create_all`` crea tablas ausentes, pero no agrega columnas a
    tablas existentes. Estas migraciones son deliberadamente idempotentes para
    que puedan ejecutarse en cada arranque sin alterar datos ya actualizados.
    """
    inspector = inspect(engine)
    if "service_orders" not in inspector.get_table_names():
        return

    order_columns = {
        column["name"] for column in inspector.get_columns("service_orders")
    }
    if "budget_status" not in order_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE service_orders "
                    "ADD COLUMN budget_status VARCHAR(30) DEFAULT 'Pendiente'"
                )
            )
        logger.info(
            "Migración aplicada: service_orders.budget_status agregado"
        )


def reset_connection() -> None:
    """Cerrar y olvidar el motor global.

    Está pensado principalmente para pruebas y para procesos que cambien de
    base de datos explícitamente. Las sesiones existentes no deben reutilizarse
    después de llamar esta función.
    """
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _session_factory = None
    _engine = None
