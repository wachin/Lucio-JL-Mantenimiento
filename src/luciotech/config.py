"""Constantes y configuración global de la aplicación."""

from __future__ import annotations

import sys
from pathlib import Path

from platformdirs import user_data_dir, user_log_dir

APP_NAME = "JL Mantenimiento"
ORG_NAME = "LucioTech"

# Tipos de equipo
EQUIPMENT_TYPES = [
    "Laptop",
    "Computadora de escritorio",
    "Impresora",
    "Cámara de seguridad",
    "DVR",
    "NVR",
    "Monitor",
    "Router",
    "Fuente de alimentación",
    "Otro",
]

# Estados de orden
ORDER_STATUSES = [
    "Recibido",
    "Pendiente de diagnóstico",
    "Diagnosticado",
    "Esperando aprobación",
    "Esperando repuesto",
    "En reparación",
    "Reparado",
    "Listo para entregar",
    "Entregado",
    "No reparable",
    "Cancelado",
]

# Prioridades
PRIORITIES = [
    "Baja",
    "Normal",
    "Alta",
    "Urgente",
]

# Tipos de fotografía
PHOTO_TYPES = [
    "Estado al recibir",
    "Número de serie",
    "Accesorios",
    "Daño físico",
    "Proceso de reparación",
    "Equipo reparado",
    "Otro",
]

# Tipos de pago
PAYMENT_TYPES = [
    "Anticipo",
    "Abono",
    "Pago final",
    "Reembolso",
]

# Métodos de pago
PAYMENT_METHODS = [
    "Efectivo",
    "Transferencia bancaria",
    "Tarjeta",
    "Depósito",
    "Otro",
]

# Tipos de evento
EVENT_TYPES = [
    "Llamada al cliente",
    "Mensaje enviado",
    "Presupuesto aprobado",
    "Presupuesto rechazado",
    "Repuesto solicitado",
    "Repuesto recibido",
    "Diagnóstico actualizado",
    "Pago recibido",
    "Equipo entregado",
    "Nota interna",
]

# Tipos de concepto
CONCEPT_TYPES = [
    "Diagnóstico",
    "Mano de obra",
    "Repuesto",
    "Accesorio",
    "Servicio",
    "Otro",
]

# Accesorios por tipo de equipo
ACCESSORIES_BY_TYPE = {
    "Laptop": [
        "Cargador",
        "Batería",
        "Bolso",
        "Mouse",
        "Adaptador",
        "Memoria USB",
        "Otro",
    ],
    "Computadora de escritorio": [
        "Cable de corriente",
        "Monitor",
        "Teclado",
        "Mouse",
        "Parlantes",
        "Adaptador Wi-Fi",
        "Otro",
    ],
    "Impresora": [
        "Cable de corriente",
        "Cable USB",
        "Cartuchos",
        "Botellas de tinta",
        "Bandejas",
        "Otro",
    ],
    "Cámara de seguridad": [
        "Fuente de alimentación",
        "Adaptador",
        "Cable",
        "Disco duro",
        "Control remoto",
        "Mouse",
        "Antena",
        "Otro",
    ],
    "DVR": [
        "Fuente de alimentación",
        "Adaptador",
        "Cable",
        "Disco duro",
        "Control remoto",
        "Mouse",
        "Otro",
    ],
    "NVR": [
        "Fuente de alimentación",
        "Adaptador",
        "Cable",
        "Disco duro",
        "Control remoto",
        "Mouse",
        "Otro",
    ],
}

# Moneda predeterminada
DEFAULT_CURRENCY = "USD"

# Formato de número de orden
DEFAULT_ORDER_FORMAT = "ORD-{year}{month:02d}{day:02d}-{sequence:04d}"


def get_data_dir() -> Path:
    """Obtener el directorio de datos de la aplicación."""
    return Path(user_data_dir(APP_NAME, ORG_NAME))


def get_log_dir() -> Path:
    """Obtener el directorio de logs de la aplicación."""
    return Path(user_log_dir(APP_NAME, ORG_NAME))


def get_db_path() -> Path:
    """Obtener la ruta de la base de datos."""
    return get_data_dir() / "database.sqlite3"


def get_reports_dir() -> Path:
    """Obtener el directorio de reportes. Lee de settings si existe."""
    from luciotech.database.connection import get_session
    from luciotech.database.models import Settings

    try:
        session = get_session()
        setting = session.query(Settings).filter(Settings.key == "reports_dir").first()
        if setting and setting.value:
            return Path(setting.value)
    except Exception:
        pass
    return get_data_dir() / "reports"


def get_backups_dir() -> Path:
    """Obtener el directorio de backups. Lee de settings si existe."""
    from luciotech.database.connection import get_session
    from luciotech.database.models import Settings

    try:
        session = get_session()
        setting = session.query(Settings).filter(Settings.key == "backups_dir").first()
        if setting and setting.value:
            return Path(setting.value)
    except Exception:
        pass
    return get_data_dir() / "backups"


def get_attachments_dir() -> Path:
    """Obtener el directorio de adjuntos. Lee de settings si existe."""
    from luciotech.database.connection import get_session
    from luciotech.database.models import Settings

    try:
        session = get_session()
        setting = session.query(Settings).filter(Settings.key == "attachments_dir").first()
        if setting and setting.value:
            return Path(setting.value)
    except Exception:
        pass
    return get_data_dir() / "attachments"
