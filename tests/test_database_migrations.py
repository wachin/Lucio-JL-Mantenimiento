"""Pruebas de actualización para bases de datos de versiones anteriores."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch


def test_init_db_adds_budget_status_to_legacy_database(tmp_path: Path) -> None:
    """La inicialización conserva órdenes y agrega ``budget_status`` una vez."""
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE service_orders "
            "(id INTEGER PRIMARY KEY, order_number VARCHAR(30))"
        )
        connection.execute(
            "INSERT INTO service_orders (id, order_number) VALUES (1, 'ORD-1')"
        )

    with patch("luciotech.database.connection.get_db_path", return_value=db_path):
        from luciotech.database.connection import init_db, reset_connection

        reset_connection()
        try:
            init_db()
            init_db()  # La migración también debe ser segura al repetirse.
        finally:
            reset_connection()

    with sqlite3.connect(db_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(service_orders)")
        }
        migrated_row = connection.execute(
            "SELECT order_number, budget_status FROM service_orders WHERE id = 1"
        ).fetchone()

    assert "budget_status" in columns
    assert migrated_row == ("ORD-1", "Pendiente")
