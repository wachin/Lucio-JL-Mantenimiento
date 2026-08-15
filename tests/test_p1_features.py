"""Pruebas para prioridades P1: validaciones, auditoría de campos, papelera y configuración."""

from __future__ import annotations

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
                            yield Path(tmpdir)
                        finally:
                            reset_connection()


# ── Helpers ──────────────────────────────────────────────────────────


def _make_order(order_svc, customer_svc, equip_svc, **kwargs):
    """Crear cliente + equipo + orden de servicio rápidamente."""
    customer, _ = customer_svc.create_customer("Test User", "0999999999")
    equipment, _ = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
    defaults = dict(customer=customer, equipment=equipment, intake_date=datetime.now())
    defaults.update(kwargs)
    return order_svc.create_order(**defaults)


# ── Validación de teléfonos ──────────────────────────────────────────


class TestPhoneValidation:
    """Validación de formatos de teléfono."""

    def test_valid_phone_10_digits(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        customer, warnings = svc.create_customer("Phone OK", "0987654321")
        assert customer.id is not None

    def test_valid_phone_with_country_code(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        customer, _ = svc.create_customer("Phone Intl", "+593987654321")
        assert customer.id is not None

    def test_invalid_phone_too_short(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        with pytest.raises(ValueError, match="al menos 7 dígitos"):
            svc.create_customer("Bad Phone", "123")

    def test_invalid_phone_letters_only(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        with pytest.raises(ValueError, match="al menos 7 dígitos"):
            svc.create_customer("Bad Phone", "abcdefgh")

    def test_phone_with_dashes_and_spaces(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        customer, _ = svc.create_customer("Formatted Phone", "099-999-999")
        assert customer.id is not None

    def test_empty_phone_rejected(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        with pytest.raises(ValueError, match="obligatorio"):
            svc.create_customer("No Phone", "")


# ── Validación de correo ─────────────────────────────────────────────


class TestEmailValidation:
    """Validación de formato de correo electrónico."""

    def test_valid_email(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        customer, _ = svc.create_customer("Email OK", "0999999999", email="test@example.com")
        assert customer.email == "test@example.com"

    def test_invalid_email_no_at(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        with pytest.raises(ValueError, match="correo electrónico"):
            svc.create_customer("Bad Email", "0999999999", email="invalidemail")

    def test_invalid_email_no_domain(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        with pytest.raises(ValueError, match="correo electrónico"):
            svc.create_customer("Bad Email2", "0999999999", email="user@")

    def test_invalid_email_spaces(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        with pytest.raises(ValueError, match="correo electrónico"):
            svc.create_customer("Bad Email3", "0999999999", email="user @example.com")

    def test_empty_email_allowed(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        customer, _ = svc.create_customer("No Email", "0999999999")
        assert customer.email is None


# ── Detección de teléfonos duplicados ────────────────────────────────


class TestDuplicatePhoneDetection:
    """Detección de teléfonos duplicados entre clientes."""

    def test_duplicate_phone_returns_warning(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        svc.create_customer("Client A", "0999999999")
        _, warnings = svc.create_customer("Client B", "0999999999")
        assert len(warnings) == 1
        assert "ya está registrado" in warnings[0]

    def test_same_phone_update_no_warning(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        customer, _ = svc.create_customer("Client A", "0999999999")
        _, warnings = svc.update_customer(customer, full_name="Client A Updated")
        assert len(warnings) == 0

    def test_different_phone_no_warning(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        svc.create_customer("Client A", "0999999999")
        _, warnings = svc.create_customer("Client B", "0988888888")
        assert len(warnings) == 0

    def test_duplicate_secondary_phone_detected(self, setup_test_db):
        from luciotech.services.order_service import CustomerService
        svc = CustomerService()
        svc.create_customer("Client A", "0911111111")
        dup_warning = svc.check_duplicate_phone("0911111111")
        assert dup_warning is not None
        assert "ya está registrado" in dup_warning


# ── Validación de sobrepago ──────────────────────────────────────────


class TestOverpaymentValidation:
    """Validación de pagos que exceden el saldo."""

    def test_abono_exceeds_balance(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc, diagnostic_cost=100.0)
        order_svc.add_payment(order, "Anticipo", "Efectivo", 50.0)

        with pytest.raises(ValueError, match="no puede exceder"):
            order_svc.add_payment(order, "Abono", "Efectivo", 60.0)

    def test_anticipo_exceeds_total(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc, diagnostic_cost=100.0)
        with pytest.raises(ValueError, match="no puede exceder"):
            order_svc.add_payment(order, "Anticipo", "Efectivo", 150.0)

    def test_negative_amount_rejected(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc, diagnostic_cost=100.0)
        with pytest.raises(ValueError, match="mayor que cero"):
            order_svc.add_payment(order, "Abono", "Efectivo", -10.0)

    def test_zero_amount_rejected(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc, diagnostic_cost=100.0)
        with pytest.raises(ValueError, match="mayor que cero"):
            order_svc.add_payment(order, "Abono", "Efectivo", 0.0)

    def test_exact_balance_payment_ok(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc, diagnostic_cost=100.0)
        payment = order_svc.add_payment(order, "Abono", "Efectivo", 100.0)
        assert payment.amount == 100.0
        order = order_svc.get_by_id(order.id)
        assert order.balance == 0.0


# ── Reemplazo de conceptos de presupuesto ────────────────────────────


class TestBudgetConceptReplace:
    """Verificar que reemplazar conceptos elimina los anteriores."""

    def test_replace_deletes_old_concepts(self, setup_test_db):
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
            order_number="ORD-REPL-001",
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=datetime.now(),
        )
        session.add(order)
        session.commit()

        repo = BudgetConceptRepo(session)

        # Crear 3 conceptos
        initial = [
            BudgetConcept(order_id=order.id, concept_type="Diagnóstico",
                          description="A", quantity=1, unit_price=10.0, subtotal=10.0),
            BudgetConcept(order_id=order.id, concept_type="Mano de obra",
                          description="B", quantity=1, unit_price=20.0, subtotal=20.0),
            BudgetConcept(order_id=order.id, concept_type="Repuesto",
                          description="C", quantity=1, unit_price=30.0, subtotal=30.0),
        ]
        repo.replace_for_order(order.id, initial)
        assert len(repo.get_by_order(order.id)) == 3

        # Reemplazar con 1 solo concepto
        replacement = [
            BudgetConcept(order_id=order.id, concept_type="Servicio",
                          description="D", quantity=1, unit_price=50.0, subtotal=50.0),
        ]
        repo.replace_for_order(order.id, replacement)

        concepts = repo.get_by_order(order.id)
        assert len(concepts) == 1
        assert concepts[0].description == "D"
        assert concepts[0].concept_type == "Servicio"

    def test_replace_with_empty_list(self, setup_test_db):
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
            order_number="ORD-REPL-002",
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

        # Reemplazar con lista vacía
        repo.replace_for_order(order.id, [])
        assert len(repo.get_by_order(order.id)) == 0


# ── Borrado permanente de la papelera ────────────────────────────────


class TestTrashPermanentDelete:
    """Eliminar permanentemente una orden borra registros relacionados."""

    def test_permanent_delete_removes_related_records(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.connection import get_session
        from luciotech.database.models import Photo, Payment, HistoryEvent, StatusHistory, BudgetConcept, ServiceOrder

        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer, _ = customer_svc.create_customer("Perm Delete", "0977777777")
        equipment, _ = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now(), diagnostic_cost=200.0)

        # Agregar datos relacionados
        order_svc.change_status(order, "En reparación")
        order_svc.add_payment(order, "Anticipo", "Efectivo", 50.0)
        order_svc.add_event(order, "Nota interna", "Test note")

        # Agregar un concepto de presupuesto
        session = get_session()
        concept = BudgetConcept(
            order_id=order.id, concept_type="Mano de obra",
            description="Test", quantity=1, unit_price=100.0, subtotal=100.0,
        )
        session.add(concept)
        session.commit()

        # Soft-delete primero
        order_svc.order_repo.soft_delete(order)

        # Verificar que existen registros relacionados
        assert len(session.query(Payment).filter(Payment.order_id == order.id).all()) >= 1
        assert len(session.query(HistoryEvent).filter(HistoryEvent.order_id == order.id).all()) >= 1
        assert len(session.query(StatusHistory).filter(StatusHistory.order_id == order.id).all()) >= 1
        assert len(session.query(BudgetConcept).filter(BudgetConcept.order_id == order.id).all()) >= 1

        # Borrado permanente
        order_svc.order_repo.permanent_delete(order)

        # Verificar que todo fue eliminado
        assert len(session.query(Payment).filter(Payment.order_id == order.id).all()) == 0
        assert len(session.query(HistoryEvent).filter(HistoryEvent.order_id == order.id).all()) == 0
        assert len(session.query(StatusHistory).filter(StatusHistory.order_id == order.id).all()) == 0
        assert len(session.query(BudgetConcept).filter(BudgetConcept.order_id == order.id).all()) == 0
        assert session.get(ServiceOrder, order.id) is None

    def test_permanent_delete_nonexistent_order_no_error(self, setup_test_db):
        """Eliminar una orden inexistente no debe lanzar error."""
        from luciotech.database.connection import get_session
        from luciotech.database.models import ServiceOrder
        from luciotech.database.repositories import OrderRepo

        session = get_session()
        repo = OrderRepo(session)
        # Crear y eliminar para obtener un ID que ya no existe
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        customer_svc = CustomerService()
        equip_svc = EquipmentService()
        order_svc = OrderService()

        customer, _ = customer_svc.create_customer("Ghost", "0966666666")
        equipment, _ = equip_svc.create_equipment(customer_id=customer.id, equipment_type="Laptop")
        order = order_svc.create_order(customer, equipment, datetime.now())
        order_id = order.id
        order_svc.order_repo.soft_delete(order)
        order_svc.order_repo.permanent_delete(order)

        # La orden ya no existe
        assert session.get(ServiceOrder, order_id) is None


# ── Settings service ─────────────────────────────────────────────────


class TestSettingsService:
    """Servicio de configuración."""

    def test_get_equipment_types_defaults(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        types = svc.get_equipment_types()
        assert "Laptop" in types
        assert "Impresora" in types
        assert len(types) > 5

    def test_get_int_returns_default_when_missing(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        result = svc.get_int("nonexistent_key", 42)
        assert result == 42

    def test_get_int_returns_stored_value(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        from luciotech.database.connection import get_session
        from luciotech.database.models import Settings

        session = get_session()
        session.add(Settings(key="test_int", value="99"))
        session.commit()

        svc = SettingsService()
        assert svc.get_int("test_int", 0) == 99

    def test_get_int_returns_default_on_invalid(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        from luciotech.database.connection import get_session
        from luciotech.database.models import Settings

        session = get_session()
        session.add(Settings(key="bad_int", value="not_a_number"))
        session.commit()

        svc = SettingsService()
        assert svc.get_int("bad_int", 7) == 7

    def test_format_order_number_default(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        when = datetime(2025, 3, 15)
        result = svc.format_order_number("ORD-{year}{month:02d}{day:02d}-{sequence:04d}", when, 1)
        assert result == "ORD-20250315-0001"

    def test_format_order_number_custom_template(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        when = datetime(2025, 6, 1)
        result = svc.format_order_number("TICKET-{year}-{sequence:03d}", when, 5)
        assert result == "TICKET-2025-005"

    def test_format_order_number_missing_sequence_raises(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        with pytest.raises(ValueError, match="{sequence"):
            svc.format_order_number("ORD-{year}", datetime.now(), 1)

    def test_format_order_number_too_long_raises(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        long_template = "X" * 30 + "-{sequence:04d}"
        with pytest.raises(ValueError, match="30 caracteres"):
            svc.format_order_number(long_template, datetime.now(), 1)

    def test_get_order_format_returns_valid_default(self, setup_test_db):
        from luciotech.services.settings_service import SettingsService
        svc = SettingsService()
        fmt = svc.get_order_format()
        assert "{sequence" in fmt


# ── Auditoría de cambios de campo ────────────────────────────────────


class TestFieldChangeAudit:
    """Auditoría detallada de cambios en campos de órdenes."""

    def test_change_status_records_field_change(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import FieldChangeRepo
        from luciotech.database.connection import get_session

        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc)
        order_svc.change_status(order, "En reparación", user="admin")

        repo = FieldChangeRepo(get_session())
        changes = repo.get_by_order(order.id)
        status_changes = [c for c in changes if c.field_name == "status"]
        assert len(status_changes) >= 1
        assert status_changes[0].old_value == "Recibido"
        assert status_changes[0].new_value == "En reparación"
        assert status_changes[0].user == "admin"

    def test_update_order_fields_records_changes(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import FieldChangeRepo
        from luciotech.database.connection import get_session

        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc)
        order_svc.update_order_fields(order, user="tech1", priority="Urgente", technician="Ing. López")

        repo = FieldChangeRepo(get_session())
        changes = repo.get_by_order(order.id)
        priority_changes = [c for c in changes if c.field_name == "priority"]
        tech_changes = [c for c in changes if c.field_name == "technician"]
        assert len(priority_changes) == 1
        assert priority_changes[0].old_value == "Normal"
        assert priority_changes[0].new_value == "Urgente"
        assert len(tech_changes) == 1
        assert tech_changes[0].new_value == "Ing. López"

    def test_update_same_value_no_audit(self, setup_test_db):
        from luciotech.services.order_service import CustomerService, EquipmentService, OrderService
        from luciotech.database.repositories import FieldChangeRepo
        from luciotech.database.connection import get_session

        order_svc = OrderService()
        customer_svc = CustomerService()
        equip_svc = EquipmentService()

        order = _make_order(order_svc, customer_svc, equip_svc)
        # priority is already "Normal"
        order_svc.update_order_fields(order, priority="Normal")

        repo = FieldChangeRepo(get_session())
        changes = repo.get_by_order(order.id)
        priority_changes = [c for c in changes if c.field_name == "priority"]
        assert len(priority_changes) == 0

    def test_field_change_repo_get_by_order(self, setup_test_db):
        from luciotech.database.connection import get_session
        from luciotech.database.models import FieldChange, Customer, Equipment, ServiceOrder
        from luciotech.database.repositories import FieldChangeRepo

        session = get_session()
        customer = Customer(full_name="Audit", phone_primary="099")
        session.add(customer)
        session.commit()

        equipment = Equipment(customer_id=customer.id, equipment_type="Laptop")
        session.add(equipment)
        session.commit()

        order = ServiceOrder(
            order_number="ORD-AUDIT-001",
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=datetime.now(),
        )
        session.add(order)
        session.commit()

        repo = FieldChangeRepo(session)
        repo.create(FieldChange(order_id=order.id, field_name="status", old_value="A", new_value="B"))
        repo.create(FieldChange(order_id=order.id, field_name="priority", old_value="Normal", new_value="Alta"))

        changes = repo.get_by_order(order.id)
        assert len(changes) == 2
