"""Pruebas básicas del sistema."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def setup_test_db():
    """Configurar base de datos temporal para pruebas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_database.sqlite3"
        with patch("luciotech.config.get_db_path", return_value=db_path):
            with patch("luciotech.database.connection.get_db_path", return_value=db_path):
                with patch("luciotech.config.get_data_dir", return_value=Path(tmpdir)):
                    with patch("luciotech.config.get_log_dir", return_value=Path(tmpdir) / "logs"):
                        from luciotech.database.connection import init_db, reset_connection
                        reset_connection()
                        init_db()
                        try:
                            yield db_path
                        finally:
                            reset_connection()


def test_create_customer(setup_test_db):
    """Prueba: creación de cliente."""
    from luciotech.services.order_service import CustomerService
    service = CustomerService()
    customer = service.create_customer(
        full_name="Juan Pérez",
        phone_primary="0999999999",
        id_number="1234567890",
        email="juan@test.com",
    )
    assert customer.id is not None
    assert customer.full_name == "Juan Pérez"
    assert customer.id_number == "1234567890"


def test_search_customer(setup_test_db):
    """Prueba: búsqueda de clientes."""
    from luciotech.services.order_service import CustomerService
    service = CustomerService()
    service.create_customer("Juan Pérez", "0999999999", "1234567890")
    service.create_customer("María López", "0988888888", "0987654321")

    results = service.search("Juan")
    assert len(results) == 1
    assert results[0].full_name == "Juan Pérez"

    results = service.search("Pérez")
    assert len(results) == 1


def test_duplicate_customer(setup_test_db):
    """Prueba: detección de duplicados por ID."""
    from luciotech.services.order_service import CustomerService
    service = CustomerService()
    service.create_customer("Juan Pérez", "0999999999", "1234567890")

    found = service.find_by_id_number("1234567890")
    assert found is not None
    assert found.full_name == "Juan Pérez"


def test_create_equipment(setup_test_db):
    """Prueba: creación de equipo."""
    from luciotech.services.order_service import CustomerService, EquipmentService
    customer_svc = CustomerService()
    equip_svc = EquipmentService()

    customer = customer_svc.create_customer("Test", "0999999999")
    equipment = equip_svc.create_equipment(
        customer_id=customer.id,
        equipment_type="Laptop",
        brand="Dell",
        model="Latitude 5520",
        serial_number="SN123456",
    )
    assert equipment.id is not None
    assert equipment.equipment_type == "Laptop"
    assert equipment.brand == "Dell"


def test_create_order(setup_test_db):
    """Prueba: creación de orden de servicio."""
    from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
    from luciotech.database.models import Customer, Equipment

    customer_svc = CustomerService()
    equip_svc = EquipmentService()
    order_svc = OrderService()

    customer = customer_svc.create_customer("Ana García", "0977777777")
    equipment = equip_svc.create_equipment(
        customer_id=customer.id,
        equipment_type="Laptop",
        brand="HP",
        reported_problem="No enciende",
    )

    order = order_svc.create_order(
        customer=customer,
        equipment=equipment,
        intake_date=datetime.now(),
        priority="Normal",
        technician="Ing. Joseph Lucio",
        reported_problem="No enciende",
    )

    assert order.id is not None
    assert order.order_number.startswith("ORD-")
    assert order.status == "Recibido"
    assert order.balance == 0.0


def test_order_number_generation(setup_test_db):
    """Prueba: generación de número de orden."""
    from luciotech.services.order_service import OrderService
    service = OrderService()
    num = service.generate_order_number()
    assert num.startswith("ORD-")
    # Formato: ORD-YYYYMMDD-NNNN
    parts = num.split("-")
    assert len(parts) == 3
    assert len(parts[2]) == 4  # Secuencia


def test_change_status(setup_test_db):
    """Prueba: cambio de estado y registro en historial."""
    from luciotech.services.order_service import CustomerService, EquipmentService, OrderService

    customer_svc = CustomerService()
    equip_svc = EquipmentService()
    order_svc = OrderService()

    customer = customer_svc.create_customer("Test", "0999999999")
    equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
    order = order_svc.create_order(customer, equipment, datetime.now())

    old_status = order.status
    order = order_svc.change_status(order, "En reparación", "Diagnóstico completado")

    assert order.status == "En reparación"
    assert old_status == "Recibido"

    # Verificar historial
    from luciotech.database.repositories import StatusHistoryRepo
    from luciotech.database.connection import get_session
    repo = StatusHistoryRepo(get_session())
    history = repo.get_by_order(order.id)
    assert len(history) >= 2  # Creación + cambio


def test_payment_and_balance(setup_test_db):
    """Prueba: registro de pagos y cálculo de saldo."""
    from luciotech.services.order_service import CustomerService, EquipmentService, OrderService

    customer_svc = CustomerService()
    equip_svc = EquipmentService()
    order_svc = OrderService()

    customer = customer_svc.create_customer("Test", "0999999999")
    equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
    order = order_svc.create_order(
        customer, equipment, datetime.now(),
        diagnostic_cost=100.0,
    )

    assert order.total == 100.0
    assert order.balance == 100.0

    # Registrar anticipo
    order_svc.add_payment(order, "Anticipo", "Efectivo", 50.0)

    # Recargar orden
    order = order_svc.get_by_id(order.id)
    assert order.balance == 50.0


def test_database_persistence(setup_test_db):
    """Prueba: datos persisten tras cerrar y reabrir conexión."""
    from luciotech.services.order_service import CustomerService

    service = CustomerService()
    service.create_customer("Persistente", "0999999999", "ID123")

    # Nueva sesión (simula cierre y reapertura)
    from luciotech.database.connection import get_session
    from luciotech.database.repositories import CustomerRepo
    repo = CustomerRepo(get_session())
    results = repo.search("Persistente")
    assert len(results) == 1
    assert results[0].full_name == "Persistente"
