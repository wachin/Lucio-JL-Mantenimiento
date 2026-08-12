"""Servicios de lógica de negocio."""

from __future__ import annotations

import logging
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
        for key, value in kwargs.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
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


class OrderService:
    """Servicio para gestión de órdenes de servicio."""

    def __init__(self) -> None:
        self.session = get_session()
        self.order_repo = OrderRepo(self.session)
        self.status_repo = StatusHistoryRepo(self.session)
        self.event_repo = HistoryEventRepo(self.session)

    def get_by_id(self, order_id: int):
        return self.order_repo.get_by_id(order_id)

    def get_by_number(self, order_number: str):
        return self.order_repo.get_by_number(order_number)

    def get_all(self):
        return self.order_repo.get_all()

    def get_recent(self, limit: int = 20):
        return self.order_repo.get_recent(limit)

    def search(self, **kwargs):
        return self.order_repo.search(**kwargs)

    def generate_order_number(self) -> str:
        """Generar número de orden automático."""
        now = datetime.now()
        # Formato: ORD-YYYYMMDD-NNNN
        sequence = self._get_next_sequence(now)
        return f"ORD-{now.year}{now.month:02d}{now.day:02d}-{sequence:04d}"

    def _get_next_sequence(self, today: datetime) -> int:
        """Obtener el siguiente número de secuencia para hoy."""
        prefix = f"ORD-{today.year}{today.month:02d}{today.day:02d}-"
        orders = self.order_repo.search()
        today_orders = [o for o in orders if o.order_number.startswith(prefix)]
        if not today_orders:
            return 1
        max_seq = max(
            int(o.order_number.split("-")[-1]) for o in today_orders if o.order_number.split("-")[-1].isdigit()
        )
        return max_seq + 1

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
    ) -> ServiceOrder:
        """Crear una nueva orden de servicio."""
        order_number = self.generate_order_number()
        balance = 0.0
        total = diagnostic_cost

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
