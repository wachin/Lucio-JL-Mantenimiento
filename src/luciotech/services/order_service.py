"""Servicios de lógica de negocio."""

from __future__ import annotations

import logging
import re
from datetime import datetime

from luciotech.database.connection import get_session
from luciotech.database.models import Customer, Equipment, ServiceOrder, StatusHistory, HistoryEvent, Payment
from luciotech.database.repositories import (
    CustomerRepo,
    EquipmentRepo,
    OrderRepo,
    StatusHistoryRepo,
    HistoryEventRepo,
    PaymentRepo,
)
from luciotech.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class CustomerService:
    """Servicio para gestión de clientes."""

    def __init__(self) -> None:
        self.repo = CustomerRepo(get_session())

    def search(self, query: str):
        """Buscar clientes por texto."""
        return self.repo.search(query)

    def get_all(self):
        """Obtener todos los clientes activos."""
        return self.repo.get_all()

    def get_by_id(self, customer_id: int):
        """Obtener cliente por ID."""
        return self.repo.get_by_id(customer_id)

    def find_by_id_number(self, id_number: str):
        """Buscar cliente por número de identificación."""
        if not id_number:
            return None
        return self.repo.get_by_id_number(id_number)

    def find_by_phone(self, phone: str):
        """Buscar cliente por teléfono."""
        if not phone:
            return None
        return self.repo.get_by_phone(phone)

    def get_deleted(self):
        """Obtener clientes eliminados (soft-deleted)."""
        return self.repo.get_deleted()

    def search_deleted(self, query: str):
        """Buscar clientes eliminados por texto."""
        return self.repo.search_deleted(query)

    def restore_customer(self, customer: Customer) -> Customer:
        """Restaurar un cliente eliminado."""
        return self.repo.undelete(customer)

    @staticmethod
    def _validate_phone(phone: str, field_label: str) -> None:
        """Validar que el teléfono tenga al menos 7 dígitos."""
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 7:
            raise ValueError(
                f"{field_label} debe tener al menos 7 dígitos (actualmente {len(digits)})"
            )

    @staticmethod
    def _validate_email(email: str) -> None:
        """Validar formato básico de correo electrónico."""
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(pattern, email):
            raise ValueError("El formato del correo electrónico no es válido")

    def _validate_contact_fields(
        self,
        phone_primary: str,
        phone_secondary: str = "",
        email: str = "",
    ) -> None:
        """Validar campos de contacto (teléfono y correo)."""
        self._validate_phone(phone_primary, "El teléfono principal")
        if phone_secondary:
            self._validate_phone(phone_secondary, "El teléfono secundario")
        if email:
            self._validate_email(email)

    def create_customer(
        self,
        full_name: str,
        phone_primary: str,
        id_number: str = "",
        phone_secondary: str = "",
        email: str = "",
        address: str = "",
        notes: str = "",
    ) -> Customer:
        """Crear un nuevo cliente."""
        if not full_name.strip():
            raise ValueError("El nombre del cliente es obligatorio")
        if not phone_primary.strip():
            raise ValueError("El teléfono principal es obligatorio")
        if id_number.strip() and self.find_by_id_number(id_number.strip()):
            raise ValueError("Ya existe un cliente con esa identificación")

        self._validate_contact_fields(
            phone_primary=phone_primary.strip(),
            phone_secondary=phone_secondary.strip(),
            email=email.strip(),
        )

        customer = Customer(
            full_name=full_name.strip(),
            id_number=id_number.strip() or None,
            phone_primary=phone_primary.strip(),
            phone_secondary=phone_secondary.strip() or None,
            email=email.strip() or None,
            address=address.strip() or None,
            notes=notes.strip() or None,
        )
        return self.repo.create(customer)

    def update_customer(self, customer: Customer, **kwargs) -> Customer:
        """Actualizar datos de un cliente."""
        full_name = str(kwargs.get("full_name", customer.full_name)).strip()
        phone_primary = str(kwargs.get("phone_primary", customer.phone_primary)).strip()
        if not full_name:
            raise ValueError("El nombre del cliente es obligatorio")
        if not phone_primary:
            raise ValueError("El teléfono principal es obligatorio")

        id_number = str(kwargs.get("id_number", customer.id_number) or "").strip()
        duplicate = self.find_by_id_number(id_number) if id_number else None
        if duplicate is not None and duplicate.id != customer.id:
            raise ValueError("Ya existe un cliente con esa identificación")

        phone_secondary = str(kwargs.get("phone_secondary", customer.phone_secondary) or "").strip()
        email = str(kwargs.get("email", customer.email) or "").strip()

        self._validate_contact_fields(
            phone_primary=phone_primary,
            phone_secondary=phone_secondary,
            email=email,
        )

        customer.full_name = full_name
        customer.phone_primary = phone_primary
        customer.id_number = id_number or None
        for key in ("phone_secondary", "email", "address", "notes"):
            if key in kwargs:
                value = str(kwargs[key] or "").strip()
                setattr(customer, key, value or None)
        return self.repo.update(customer)


class EquipmentService:
    """Servicio para gestión de equipos."""

    def __init__(self) -> None:
        self.repo = EquipmentRepo(get_session())

    def get_by_id(self, equipment_id: int):
        return self.repo.get_by_id(equipment_id)

    def find_by_serial(self, serial_number: str):
        if not serial_number:
            return None
        return self.repo.get_by_serial(serial_number)

    def get_all(self):
        return self.repo.get_all()

    def search(self, query: str):
        return self.repo.search(query)

    def create_equipment(
        self,
        customer_id: int,
        equipment_type: str,
        brand: str = "",
        model: str = "",
        serial_number: str = "",
        color: str = "",
        os: str = "",
        password: str = "",
        accessories: str = "",
        physical_state: str = "",
        reported_problem: str = "",
        intake_notes: str = "",
    ) -> Equipment:
        """Crear un nuevo equipo."""
        if not equipment_type.strip():
            raise ValueError("El tipo de equipo es obligatorio")
        if serial_number.strip() and self.find_by_serial(serial_number.strip()):
            raise ValueError("Ya existe otro equipo con ese número de serie")
        equipment = Equipment(
            customer_id=customer_id,
            equipment_type=equipment_type,
            brand=brand.strip() or None,
            model=model.strip() or None,
            serial_number=serial_number.strip() or None,
            color=color.strip() or None,
            os=os.strip() or None,
            password=password.strip() or None,
            accessories=accessories.strip() or None,
            physical_state=physical_state.strip() or None,
            reported_problem=reported_problem.strip() or None,
            intake_notes=intake_notes.strip() or None,
        )
        return self.repo.create(equipment)

    def update_equipment(self, equipment: Equipment, **kwargs) -> Equipment:
        """Actualizar los datos editables de un equipo."""
        equipment_type = str(
            kwargs.get("equipment_type", equipment.equipment_type)
        ).strip()
        if not equipment_type:
            raise ValueError("El tipo de equipo es obligatorio")

        serial_number = str(
            kwargs.get("serial_number", equipment.serial_number) or ""
        ).strip()
        duplicate = self.find_by_serial(serial_number) if serial_number else None
        if duplicate is not None and duplicate.id != equipment.id:
            raise ValueError("Ya existe otro equipo con ese número de serie")

        equipment.equipment_type = equipment_type
        equipment.serial_number = serial_number or None
        for key in (
            "brand",
            "model",
            "color",
            "os",
            "password",
            "accessories",
            "physical_state",
            "reported_problem",
            "intake_notes",
        ):
            if key in kwargs:
                value = str(kwargs[key] or "").strip()
                setattr(equipment, key, value or None)
        return self.repo.update(equipment)


class OrderService:
    """Servicio para gestión de órdenes de servicio."""

    def __init__(self) -> None:
        self.session = get_session()
        self.order_repo = OrderRepo(self.session)
        self.status_repo = StatusHistoryRepo(self.session)
        self.event_repo = HistoryEventRepo(self.session)
        self.settings = SettingsService()

    def get_by_id(self, order_id: int):
        return self.order_repo.get_by_id(order_id)

    def get_by_number(self, order_number: str):
        return self.order_repo.get_by_number(order_number)

    def get_all(self):
        return self.order_repo.get_all()

    def get_deleted(self):
        return self.order_repo.get_deleted()

    def restore(self, order: ServiceOrder) -> ServiceOrder:
        return self.order_repo.restore(order)

    def get_recent(self, limit: int = 20):
        return self.order_repo.get_recent(limit)

    def search(self, **kwargs):
        return self.order_repo.search(**kwargs)

    def generate_order_number(self) -> str:
        """Generar número de orden automático."""
        now = datetime.now()
        sequence = self._get_next_sequence(now)
        template = self.settings.get_order_format()
        while True:
            number = self.settings.format_order_number(template, now, sequence)
            if self.order_repo.get_by_number(number) is None:
                return number
            sequence += 1

    def _get_next_sequence(self, today: datetime) -> int:
        """Obtener el siguiente número de secuencia para hoy."""
        orders = self.order_repo.get_all(active_only=False)
        today_orders = [
            order
            for order in orders
            if order.created_at and order.created_at.date() == today.date()
        ]
        return len(today_orders) + 1

    def create_order(
        self,
        customer: Customer,
        equipment: Equipment,
        intake_date: datetime,
        estimated_delivery_date: datetime | None = None,
        priority: str = "Normal",
        technician: str = "",
        diagnostic_cost: float = 0.0,
        advance_payment: float = 0.0,
        status: str = "Recibido",
        reported_problem: str = "",
        warranty_days: int | None = None,
    ) -> ServiceOrder:
        """Crear una nueva orden de servicio."""
        order_number = self.generate_order_number()
        total = diagnostic_cost
        balance = total - advance_payment

        order = ServiceOrder(
            order_number=order_number,
            customer_id=customer.id,
            equipment_id=equipment.id,
            intake_date=intake_date,
            estimated_delivery_date=estimated_delivery_date,
            status=status,
            priority=priority,
            technician=technician.strip() or None,
            reported_problem=reported_problem.strip() or None,
            diagnostic_cost=diagnostic_cost,
            total=total,
            advance_payment=advance_payment,
            balance=balance,
            warranty_days=(
                warranty_days
                if warranty_days is not None
                else self.settings.get_int("warranty_days", 30)
            ),
        )
        order = self.order_repo.create(order)

        # Registrar historial de estado
        self._record_status_change(order, "", status, "Orden creada")

        # Registrar anticipo como pago si existe
        if advance_payment > 0:
            payment = Payment(
                order_id=order.id,
                payment_date=intake_date,
                payment_type="Anticipo",
                payment_method="Efectivo",
                amount=advance_payment,
            )
            payment_repo = PaymentRepo(self.session)
            payment_repo.create(payment)
            order.balance = total - advance_payment
            self.order_repo.update(order)

        logger.info("Orden creada: %s para cliente %s", order_number, customer.full_name)
        return order

    def change_status(self, order: ServiceOrder, new_status: str, comment: str = "") -> ServiceOrder:
        """Cambiar el estado de una orden."""
        old_status = order.status
        order.status = new_status
        self.order_repo.update(order)
        self._record_status_change(order, old_status, new_status, comment)
        logger.info("Estado cambiado: %s → %s (%s)", old_status, new_status, order.order_number)
        return order

    def add_event(self, order: ServiceOrder, event_type: str, title: str, description: str = "", user: str = "") -> None:
        """Añadir un evento al historial de la orden."""
        event = HistoryEvent(
            order_id=order.id,
            event_type=event_type,
            title=title.strip(),
            description=description.strip() or None,
            user=user.strip() or None,
        )
        self.event_repo.create(event)

    def add_payment(
        self,
        order: ServiceOrder,
        payment_type: str,
        payment_method: str,
        amount: float,
        reference: str = "",
        notes: str = "",
    ) -> Payment:
        """Registrar un pago para una orden."""
        payment = Payment(
            order_id=order.id,
            payment_type=payment_type,
            payment_method=payment_method,
            amount=amount,
            reference=reference.strip() or None,
            notes=notes.strip() or None,
        )
        payment_repo = PaymentRepo(self.session)
        payment = payment_repo.create(payment)

        # Recalcular saldo
        total_paid = payment_repo.get_total_paid(order.id)
        order.balance = order.total - total_paid
        self.order_repo.update(order)

        self.add_event(order, "Pago recibido", f"Pago de ${amount:.2f}", f"Método: {payment_method}")
        return payment

    def _record_status_change(self, order: ServiceOrder, old_status: str, new_status: str, comment: str) -> None:
        """Registrar cambio de estado en el historial."""
        record = StatusHistory(
            order_id=order.id,
            previous_status=old_status,
            new_status=new_status,
            comment=comment.strip() or None,
        )
        self.status_repo.create(record)
