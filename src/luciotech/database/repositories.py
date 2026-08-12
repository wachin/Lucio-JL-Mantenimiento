"""Repositorios de acceso a datos."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from luciotech.database.models import Customer, Equipment, ServiceOrder, Photo, StatusHistory, HistoryEvent, Payment


class CustomerRepo:
    """Repositorio para operaciones con clientes."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, customer_id: int) -> Customer | None:
        return self.session.get(Customer, customer_id)

    def get_by_id_number(self, id_number: str) -> Customer | None:
        stmt = select(Customer).where(
            Customer.id_number == id_number, Customer.is_deleted == False  # noqa: E712
        )
        return self.session.scalars(stmt).first()

    def get_by_phone(self, phone: str) -> Customer | None:
        stmt = select(Customer).where(
            or_(Customer.phone_primary == phone, Customer.phone_secondary == phone),
            Customer.is_deleted == False,  # noqa: E712
        )
        return self.session.scalars(stmt).first()

    def search(self, query: str) -> Sequence[Customer]:
        """Buscar clientes por nombre, identificación o teléfono."""
        pattern = f"%{query}%"
        stmt = (
            select(Customer)
            .where(Customer.is_deleted == False)  # noqa: E712
            .where(
                or_(
                    Customer.full_name.ilike(pattern),
                    Customer.id_number.ilike(pattern),
                    Customer.phone_primary.ilike(pattern),
                    Customer.phone_secondary.ilike(pattern),
                    Customer.email.ilike(pattern),
                )
            )
            .order_by(Customer.full_name)
            .limit(50)
        )
        return self.session.scalars(stmt).all()

    def get_all(self, active_only: bool = True) -> Sequence[Customer]:
        stmt = select(Customer).order_by(Customer.full_name)
        if active_only:
            stmt = stmt.where(Customer.is_deleted == False)  # noqa: E712
        return self.session.scalars(stmt).all()

    def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        self.session.commit()
        self.session.refresh(customer)
        return customer

    def update(self, customer: Customer) -> Customer:
        customer.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(customer)
        return customer

    def soft_delete(self, customer: Customer) -> None:
        customer.is_deleted = True
        customer.deleted_at = datetime.now()
        self.session.commit()


class EquipmentRepo:
    """Repositorio para operaciones con equipos."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, equipment_id: int) -> Equipment | None:
        return self.session.get(Equipment, equipment_id)

    def get_by_serial(self, serial_number: str) -> Equipment | None:
        if not serial_number:
            return None
        stmt = select(Equipment).where(Equipment.serial_number == serial_number)
        return self.session.scalars(stmt).first()

    def create(self, equipment: Equipment) -> Equipment:
        self.session.add(equipment)
        self.session.commit()
        self.session.refresh(equipment)
        return equipment

    def update(self, equipment: Equipment) -> Equipment:
        equipment.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(equipment)
        return equipment

    def get_by_customer(self, customer_id: int) -> Sequence[Equipment]:
        stmt = select(Equipment).where(Equipment.customer_id == customer_id).order_by(Equipment.created_at.desc())
        return self.session.scalars(stmt).all()


class OrderRepo:
    """Repositorio para operaciones con órdenes de servicio."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, order_id: int) -> ServiceOrder | None:
        return (
            self.session.query(ServiceOrder)
            .options(
                joinedload(ServiceOrder.customer),
                joinedload(ServiceOrder.equipment),
            )
            .get(order_id)
        )

    def get_by_number(self, order_number: str) -> ServiceOrder | None:
        return (
            self.session.query(ServiceOrder)
            .options(
                joinedload(ServiceOrder.customer),
                joinedload(ServiceOrder.equipment),
            )
            .filter(ServiceOrder.order_number == order_number)
            .first()
        )

    def get_all(self, active_only: bool = True) -> Sequence[ServiceOrder]:
        query = self.session.query(ServiceOrder).options(
            joinedload(ServiceOrder.customer),
            joinedload(ServiceOrder.equipment),
        )
        if active_only:
            query = query.filter(ServiceOrder.is_deleted == False)  # noqa: E712
        return query.order_by(ServiceOrder.created_at.desc()).all()

    def search(
        self,
        query_text: str = "",
        status: str = "",
        priority: str = "",
        customer_name: str = "",
        equipment_type: str = "",
        brand: str = "",
        serial: str = "",
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        has_balance: bool = False,
        is_overdue: bool = False,
    ) -> Sequence[ServiceOrder]:
        """Buscar órdenes con filtros múltiples."""
        q = self.session.query(ServiceOrder).options(
            joinedload(ServiceOrder.customer),
            joinedload(ServiceOrder.equipment),
        )
        q = q.filter(ServiceOrder.is_deleted == False)  # noqa: E712

        if query_text:
            pattern = f"%{query_text}%"
            q = q.filter(
                or_(
                    ServiceOrder.order_number.ilike(pattern),
                    ServiceOrder.reported_problem.ilike(pattern),
                    ServiceOrder.customer.has(Customer.full_name.ilike(pattern)),
                    ServiceOrder.equipment.has(Equipment.brand.ilike(pattern)),
                    ServiceOrder.equipment.has(Equipment.model.ilike(pattern)),
                )
            )

        if status:
            q = q.filter(ServiceOrder.status == status)
        if priority:
            q = q.filter(ServiceOrder.priority == priority)
        if customer_name:
            q = q.join(ServiceOrder.customer).filter(Customer.full_name.ilike(f"%{customer_name}%"))
        if equipment_type:
            q = q.join(ServiceOrder.equipment).filter(Equipment.equipment_type == equipment_type)
        if brand:
            q = q.join(ServiceOrder.equipment).filter(Equipment.brand.ilike(f"%{brand}%"))
        if serial:
            q = q.join(ServiceOrder.equipment).filter(Equipment.serial_number.ilike(f"%{serial}%"))
        if date_from:
            q = q.filter(ServiceOrder.intake_date >= date_from)
        if date_to:
            q = q.filter(ServiceOrder.intake_date <= date_to)
        if has_balance:
            q = q.filter(ServiceOrder.balance > 0)
        if is_overdue:
            now = datetime.now()
            q = q.filter(
                ServiceOrder.estimated_delivery_date != None,  # noqa: E711
                ServiceOrder.estimated_delivery_date < now,
                ServiceOrder.status.notin_(["Entregado", "Cancelado", "No reparable"]),
            )

        return q.order_by(ServiceOrder.created_at.desc()).all()

    def create(self, order: ServiceOrder) -> ServiceOrder:
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order

    def update(self, order: ServiceOrder) -> ServiceOrder:
        order.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(order)
        return order

    def soft_delete(self, order: ServiceOrder) -> None:
        order.is_deleted = True
        order.deleted_at = datetime.now()
        self.session.commit()

    def get_recent(self, limit: int = 20) -> Sequence[ServiceOrder]:
        return (
            self.session.query(ServiceOrder)
            .options(
                joinedload(ServiceOrder.customer),
                joinedload(ServiceOrder.equipment),
            )
            .filter(ServiceOrder.is_deleted == False)  # noqa: E712
            .order_by(ServiceOrder.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_status(self, status: str) -> Sequence[ServiceOrder]:
        return (
            self.session.query(ServiceOrder)
            .options(
                joinedload(ServiceOrder.customer),
                joinedload(ServiceOrder.equipment),
            )
            .filter(ServiceOrder.status == status, ServiceOrder.is_deleted == False)  # noqa: E712
            .order_by(ServiceOrder.created_at.desc())
            .all()
        )


class PhotoRepo:
    """Repositorio para fotografías."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_order(self, order_id: int) -> Sequence[Photo]:
        stmt = select(Photo).where(Photo.order_id == order_id).order_by(Photo.sort_order)
        return self.session.scalars(stmt).all()

    def create(self, photo: Photo) -> Photo:
        self.session.add(photo)
        self.session.commit()
        self.session.refresh(photo)
        return photo

    def delete(self, photo: Photo) -> None:
        self.session.delete(photo)
        self.session.commit()

    def reorder(self, photos: list[tuple[int, int]]) -> None:
        """Reordenar fotos. Lista de (photo_id, sort_order)."""
        for photo_id, sort_order in photos:
            photo = self.session.get(Photo, photo_id)
            if photo:
                photo.sort_order = sort_order
        self.session.commit()


class StatusHistoryRepo:
    """Repositorio para historial de estados."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_order(self, order_id: int) -> Sequence[StatusHistory]:
        stmt = select(StatusHistory).where(StatusHistory.order_id == order_id).order_by(StatusHistory.changed_at.desc())
        return self.session.scalars(stmt).all()

    def create(self, record: StatusHistory) -> StatusHistory:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record


class HistoryEventRepo:
    """Repositorio para eventos del historial."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_order(self, order_id: int) -> Sequence[HistoryEvent]:
        stmt = select(HistoryEvent).where(HistoryEvent.order_id == order_id).order_by(HistoryEvent.created_at.desc())
        return self.session.scalars(stmt).all()

    def create(self, event: HistoryEvent) -> HistoryEvent:
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event


class PaymentRepo:
    """Repositorio para pagos."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_order(self, order_id: int) -> Sequence[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.payment_date.desc())
        return self.session.scalars(stmt).all()

    def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def get_total_paid(self, order_id: int) -> float:
        from sqlalchemy import func

        stmt = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(Payment.order_id == order_id)
        return self.session.scalar(stmt) or 0.0
