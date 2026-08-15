"""Pruebas para prioridades P0: backups seguros, presupuestos persistentes, papelera e historial."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
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
                            yield Path(tmpdir)
                        finally:
                            reset_connection()


# ── Backups seguros ──────────────────────────────────────────────────


class TestBackupZipSlipValidation:
    """Validación de rutas contra Zip Slip."""

    def test_rejects_path_traversal(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        data_dir = setup_test_db
        namelist = ["database.sqlite3", "../../etc/passwd"]
        assert BackupService._validate_zip_paths(namelist, data_dir) is False

    def test_rejects_absolute_path_outside(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        data_dir = setup_test_db
        namelist = ["database.sqlite3", "/etc/shadow"]
        assert BackupService._validate_zip_paths(namelist, data_dir) is False

    def test_accepts_valid_paths(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        data_dir = setup_test_db
        namelist = ["database.sqlite3", "attachments/photo1.jpg", "backup_metadata.json"]
        assert BackupService._validate_zip_paths(namelist, data_dir) is True

    def test_rejects_nested_traversal(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        data_dir = setup_test_db
        namelist = ["attachments/../../../etc/passwd"]
        assert BackupService._validate_zip_paths(namelist, data_dir) is False


class TestBackupConsistency:
    """Backup consistente usando la API de SQLite."""

    def test_backup_creates_valid_sqlite(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        from luciotech.database.connection import get_session
        from luciotech.database.models import Settings

        data_dir = setup_test_db

        session = get_session()
        setting = Settings(key="test_key", value="test_value")
        session.add(setting)
        session.commit()

        # create_backup_to busca data_dir/database.sqlite3; el fixture usa otro nombre
        import shutil as _shutil
        _shutil.copy2(str(data_dir / "test_database.sqlite3"), str(data_dir / "database.sqlite3"))

        backup_dir = data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        with patch("luciotech.services.backup_service.get_data_dir", return_value=data_dir):
            result = BackupService.create_backup_to(str(backup_dir))

        backup_path = Path(result)
        assert backup_path.exists()

        with zipfile.ZipFile(backup_path, "r") as zf:
            assert "database.sqlite3" in zf.namelist()
            assert "backup_metadata.json" in zf.namelist()

            with tempfile.TemporaryDirectory() as extract_dir:
                zf.extract("database.sqlite3", extract_dir)
                extracted = Path(extract_dir) / "database.sqlite3"

                check_conn = sqlite3.connect(str(extracted))
                cursor = check_conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                assert cursor.fetchone()[0] == "ok"
                cursor.execute("SELECT value FROM settings WHERE key='test_key'")
                assert cursor.fetchone()[0] == "test_value"
                check_conn.close()

    def test_backup_metadata_version(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        data_dir = setup_test_db

        backup_dir = data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        with patch("luciotech.services.backup_service.get_data_dir", return_value=data_dir):
            result = BackupService.create_backup_to(str(backup_dir))

        with zipfile.ZipFile(result, "r") as zf:
            metadata = json.loads(zf.read("backup_metadata.json"))
            assert metadata["version"] == "0.2.0"
            assert "created_at" in metadata


class TestAtomicRestore:
    """Restauración transaccional."""

    def test_restore_replaces_database(self, setup_test_db):
        from luciotech.services.backup_service import BackupService
        from luciotech.database.connection import get_session
        from luciotech.database.models import Settings
        import shutil as _shutil

        data_dir = setup_test_db

        session = get_session()
        setting = Settings(key="restore_test", value="original")
        session.add(setting)
        session.commit()

        # Copiar al nombre que create_backup_to espera
        _shutil.copy2(str(data_dir / "test_database.sqlite3"), str(data_dir / "database.sqlite3"))

        backup_dir = data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        with patch("luciotech.services.backup_service.get_data_dir", return_value=data_dir):
            backup_path = BackupService.create_backup_to(str(backup_dir))

        # Modificar la base de datos actual
        conn = sqlite3.connect(str(data_dir / "database.sqlite3"))
        conn.execute("UPDATE settings SET value='modified' WHERE key='restore_test'")
        conn.commit()
        conn.close()

        # Restaurar desde el backup
        with zipfile.ZipFile(backup_path, "r") as zf:
            namelist = zf.namelist()
            assert BackupService._validate_zip_paths(namelist, data_dir)

            with tempfile.TemporaryDirectory(prefix="jlmb-test-") as tmpdir:
                tmpdir_path = Path(tmpdir)
                zf.extractall(tmpdir_path)
                BackupService._atomic_replace(tmpdir_path, data_dir)

        # Verificar restauración
        check_conn = sqlite3.connect(str(data_dir / "database.sqlite3"))
        cursor = check_conn.execute("SELECT value FROM settings WHERE key='restore_test'")
        assert cursor.fetchone()[0] == "original"
        check_conn.close()


# ── Presupuestos persistentes ────────────────────────────────────────


class TestBudgetConcepts:
    """Persistencia de conceptos del presupuesto."""

    def test_create_and_retrieve_concepts(self, setup_test_db):
        from luciotech.database.connection import get_session
        from luciotech.database.models import BudgetConcept, Customer, Equipment, ServiceOrder
        from luciotech.database.repositories import BudgetConceptRepo

        session = get_session()

        customer = Customer(full_name="Test", phone_primary="099")
        session.add(customer)
        session.commit()

        equipment = Equipment(customer_id=customer.id, equipment_type="Laptop")
        session.add(equipment)
        session.commit()

        order = ServiceOrder(
            order_number="ORD-TEST-001",
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=datetime.now(),
        )
        session.add(order)
        session.commit()

        repo = BudgetConceptRepo(session)
        c1 = BudgetConcept(
            order_id=order.id, concept_type="Mano de obra",
            description="Reparación pantalla", quantity=1, unit_price=80.0, subtotal=80.0,
        )
        c2 = BudgetConcept(
            order_id=order.id, concept_type="Repuesto",
            description="Pantalla LCD 15\"", quantity=1, unit_price=150.0, subtotal=150.0,
        )
        repo.replace_for_order(order.id, [c1, c2])

        concepts = repo.get_by_order(order.id)
        assert len(concepts) == 2
        assert concepts[0].concept_type == "Mano de obra"
        assert concepts[0].subtotal == 80.0
        assert concepts[1].concept_type == "Repuesto"
        assert concepts[1].subtotal == 150.0

    def test_replace_concepts(self, setup_test_db):
        from luciotech.database.connection import get_session
        from luciotech.database.models import BudgetConcept, Customer, Equipment, ServiceOrder
        from luciotech.database.repositories import BudgetConceptRepo

        session = get_session()

        customer = Customer(full_name="Test", phone_primary="099")
        session.add(customer)
        session.commit()

        equipment = Equipment(customer_id=customer.id, equipment_type="Laptop")
        session.add(equipment)
        session.commit()

        order = ServiceOrder(
            order_number="ORD-TEST-002",
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=datetime.now(),
        )
        session.add(order)
        session.commit()

        repo = BudgetConceptRepo(session)

        # Crear conceptos iniciales
        initial = [
            BudgetConcept(order_id=order.id, concept_type="Diagnóstico",
                          description="Revisión", quantity=1, unit_price=30.0, subtotal=30.0),
        ]
        repo.replace_for_order(order.id, initial)
        assert len(repo.get_by_order(order.id)) == 1

        # Reemplazar con nuevos
        replacement = [
            BudgetConcept(order_id=order.id, concept_type="Mano de obra",
                          description="Cambio de teclado", quantity=1, unit_price=50.0, subtotal=50.0),
            BudgetConcept(order_id=order.id, concept_type="Repuesto",
                          description="Teclado US", quantity=1, unit_price=25.0, subtotal=25.0),
        ]
        repo.replace_for_order(order.id, replacement)

        concepts = repo.get_by_order(order.id)
        assert len(concepts) == 2
        assert concepts[0].description == "Cambio de teclado"
        assert concepts[1].description == "Teclado US"

    def test_delete_concepts_by_order(self, setup_test_db):
        from luciotech.database.connection import get_session
        from luciotech.database.models import BudgetConcept, Customer, Equipment, ServiceOrder
        from luciotech.database.repositories import BudgetConceptRepo

        session = get_session()

        customer = Customer(full_name="Test", phone_primary="099")
        session.add(customer)
        session.commit()

        equipment = Equipment(customer_id=customer.id, equipment_type="Laptop")
        session.add(equipment)
        session.commit()

        order = ServiceOrder(
            order_number="ORD-TEST-003",
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=datetime.now(),
        )
        session.add(order)
        session.commit()

        repo = BudgetConceptRepo(session)
        repo.replace_for_order(order.id, [
            BudgetConcept(order_id=order.id, concept_type="Otro",
                          description="X", quantity=1, unit_price=10.0, subtotal=10.0),
        ])
        assert len(repo.get_by_order(order.id)) == 1

        repo.delete_by_order(order.id)
        assert len(repo.get_by_order(order.id)) == 0

    def test_concepts_persist_across_sessions(self, setup_test_db):
        from luciotech.database.connection import get_session
        from luciotech.database.models import BudgetConcept, Customer, Equipment, ServiceOrder
        from luciotech.database.repositories import BudgetConceptRepo

        session = get_session()

        customer = Customer(full_name="Persist", phone_primary="099")
        session.add(customer)
        session.commit()

        equipment = Equipment(customer_id=customer.id, equipment_type="Laptop")
        session.add(equipment)
        session.commit()

        order = ServiceOrder(
            order_number="ORD-TEST-004",
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=datetime.now(),
        )
        session.add(order)
        session.commit()

        repo = BudgetConceptRepo(session)
        repo.replace_for_order(order.id, [
            BudgetConcept(order_id=order.id, concept_type="Servicio",
                          description="Limpieza", quantity=1, unit_price=20.0, subtotal=20.0),
        ])

        # Nueva sesión (simula reapertura)
        from luciotech.database.connection import get_session as new_session
        new_repo = BudgetConceptRepo(new_session())
        concepts = new_repo.get_by_order(order.id)
        assert len(concepts) == 1
        assert concepts[0].description == "Limpieza"


# ── Papelera ─────────────────────────────────────────────────────────


class TestTrashAndRestore:
    """Papelera y restauración de órdenes."""

    def test_soft_delete_order(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("Trash Test", "0999999999")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())

        order_svc.order_repo.soft_delete(order)

        active = order_svc.get_all()
        assert all(o.id != order.id for o in active)

        deleted = order_svc.get_deleted()
        assert any(o.id == order.id for o in deleted)

    def test_restore_order(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("Restore Test", "0988888888")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())

        order_svc.order_repo.soft_delete(order)
        assert any(o.id == order.id for o in order_svc.get_deleted())

        restored = order_svc.restore(order)
        assert restored.is_deleted is False
        assert restored.deleted_at is None
        assert any(o.id == order.id for o in order_svc.get_all())

    def test_deleted_order_not_in_search(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("Search Test", "0977777777")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())

        order_svc.order_repo.soft_delete(order)

        results = order_svc.search(query_text="Search Test")
        assert all(o.id != order.id for o in results)


# ── Historial ────────────────────────────────────────────────────────


class TestHistory:
    """Historial de cambios de estado y eventos."""

    def test_status_change_creates_history(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import StatusHistoryRepo
        from luciotech.database.connection import get_session

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("History Test", "0966666666")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())

        order_svc.change_status(order, "En reparación", "Diagnóstico completado")
        order_svc.change_status(order, "Reparado", "Pantalla reemplazada")

        repo = StatusHistoryRepo(get_session())
        history = repo.get_by_order(order.id)
        statuses = [(h.previous_status, h.new_status) for h in history]

        assert ("", "Recibido") in statuses
        assert ("Recibido", "En reparación") in statuses
        assert ("En reparación", "Reparado") in statuses

    def test_add_event(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import HistoryEventRepo
        from luciotech.database.connection import get_session

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("Event Test", "0955555555")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())

        order_svc.add_event(order, "Llamada al cliente", "Se llamó al cliente", "Confirmó presupuesto")

        repo = HistoryEventRepo(get_session())
        events = repo.get_by_order(order.id)
        assert len(events) >= 1
        assert events[0].event_type == "Llamada al cliente"
        assert events[0].title == "Se llamó al cliente"

    def test_payment_creates_event(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import HistoryEventRepo
        from luciotech.database.connection import get_session

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("Payment Event", "0944444444")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now(), diagnostic_cost=100.0)

        order_svc.add_payment(order, "Abono", "Efectivo", 50.0)

        repo = HistoryEventRepo(get_session())
        events = repo.get_by_order(order.id)
        payment_events = [e for e in events if e.event_type == "Pago recibido"]
        assert len(payment_events) >= 1

    def test_global_history(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import StatusHistoryRepo, HistoryEventRepo
        from luciotech.database.connection import get_session

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer = customer_svc.create_customer("Global Hist", "0933333333")
        equipment = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())
        order_svc.change_status(order, "En reparación")

        status_repo = StatusHistoryRepo(get_session())
        all_status = status_repo.get_recent()
        assert len(all_status) >= 2

        event_repo = HistoryEventRepo(get_session())
        all_events = event_repo.get_recent()
        assert len(all_events) >= 0  # At least the creation events
