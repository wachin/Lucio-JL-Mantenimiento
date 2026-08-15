"""Modelos de base de datos SQLAlchemy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Customer(Base):
    """Cliente del taller."""

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_is_deleted", "is_deleted"),
        Index("ix_customers_full_name", "full_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(200), nullable=False)
    id_number = Column(String(50), unique=True, nullable=True)
    phone_primary = Column(String(20), nullable=False)
    phone_secondary = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)
    address = Column(String(300), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    equipments = relationship("Equipment", back_populates="customer", lazy="select")
    orders = relationship("ServiceOrder", back_populates="customer", lazy="select")

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.full_name}')>"


class Equipment(Base):
    """Equipo registrado en el taller."""

    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    equipment_type = Column(String(50), nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    os = Column(String(100), nullable=True)
    password = Column(String(100), nullable=True)
    accessories = Column(Text, nullable=True)
    physical_state = Column(String(200), nullable=True)
    reported_problem = Column(Text, nullable=True)
    intake_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    customer = relationship("Customer", back_populates="equipments", lazy="select")
    orders = relationship("ServiceOrder", back_populates="equipment", lazy="select")

    def __repr__(self) -> str:
        return f"<Equipment(id={self.id}, type='{self.equipment_type}', brand='{self.brand}')>"


class ServiceOrder(Base):
    """Orden de servicio."""

    __tablename__ = "service_orders"
    __table_args__ = (
        Index("ix_service_orders_status", "status"),
        Index("ix_service_orders_customer_id", "customer_id"),
        Index("ix_service_orders_is_deleted", "is_deleted"),
        Index("ix_service_orders_intake_date", "intake_date"),
        Index("ix_service_orders_order_number", "order_number"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(30), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    intake_date = Column(DateTime, nullable=False)
    estimated_delivery_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    status = Column(String(30), default="Recibido", nullable=False)
    priority = Column(String(10), default="Normal", nullable=False)
    technician = Column(String(100), nullable=True)
    reported_problem = Column(Text, nullable=True)
    diagnosis_html = Column(Text, nullable=True)
    work_done_html = Column(Text, nullable=True)
    recommendations_html = Column(Text, nullable=True)
    parts_used = Column(Text, nullable=True)
    diagnostic_cost = Column(Float, default=0.0, nullable=False)
    parts_cost = Column(Float, default=0.0, nullable=False)
    labor_cost = Column(Float, default=0.0, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    advance_payment = Column(Float, default=0.0, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    warranty_days = Column(Integer, default=30, nullable=False)
    budget_status = Column(String(30), default="Pendiente", nullable=True)
    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="orders", lazy="select")
    equipment = relationship("Equipment", back_populates="orders", lazy="select")
    photos = relationship("Photo", back_populates="order", lazy="select", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="order", lazy="select", cascade="all, delete-orphan")
    events = relationship("HistoryEvent", back_populates="order", lazy="select", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", lazy="select", cascade="all, delete-orphan")
    budget_concepts = relationship("BudgetConcept", back_populates="order", lazy="select", cascade="all, delete-orphan")
    field_changes = relationship("FieldChange", back_populates="order", lazy="select", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ServiceOrder(number='{self.order_number}', status='{self.status}')>"


class Photo(Base):
    """Fotografía adjunta a una orden."""

    __tablename__ = "photos"
    __table_args__ = (
        Index("ix_photos_order_id", "order_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    description = Column(String(300), nullable=True)
    photo_type = Column(String(50), default="Otro", nullable=False)
    capture_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    order = relationship("ServiceOrder", back_populates="photos", lazy="select")

    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, file='{self.file_name}')>"


class StatusHistory(Base):
    """Historial de cambios de estado."""

    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    previous_status = Column(String(30), nullable=False)
    new_status = Column(String(30), nullable=False)
    comment = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.now, nullable=False)
    user = Column(String(100), nullable=True)

    order = relationship("ServiceOrder", back_populates="status_history", lazy="select")

    def __repr__(self) -> str:
        return f"<StatusHistory(order='{self.order_id}', {self.previous_status}→{self.new_status})>"


class HistoryEvent(Base):
    """Eventos o notas del historial de una orden."""

    __tablename__ = "history_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    user = Column(String(100), nullable=True)

    order = relationship("ServiceOrder", back_populates="events", lazy="select")

    def __repr__(self) -> str:
        return f"<HistoryEvent(id={self.id}, type='{self.event_type}')>"


class Payment(Base):
    """Pago registrado para una orden."""

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_payment_date", "payment_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    payment_date = Column(DateTime, default=datetime.now, nullable=False)
    payment_type = Column(String(30), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    is_voided = Column(Boolean, default=False, nullable=False)
    void_reason = Column(Text, nullable=True)

    order = relationship("ServiceOrder", back_populates="payments", lazy="select")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, type='{self.payment_type}', voided={self.is_voided})>"


class BudgetConcept(Base):
    """Concepto individual del presupuesto de una orden."""

    __tablename__ = "budget_concepts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    concept_type = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    order = relationship("ServiceOrder", back_populates="budget_concepts", lazy="select")

    def __repr__(self) -> str:
        return f"<BudgetConcept(id={self.id}, type='{self.concept_type}', subtotal={self.subtotal})>"



class FieldChange(Base):
    """Auditoría de cambios individuales en campos de una orden."""

    __tablename__ = "field_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.now, nullable=False)
    user = Column(String(100), nullable=True)

    order = relationship("ServiceOrder", back_populates="field_changes", lazy="select")

    def __repr__(self) -> str:
        return f"<FieldChange(order={self.order_id}, field='{self.field_name}')>"


class Settings(Base):
    """Configuración de la aplicación."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Settings(key='{self.key}')>"
