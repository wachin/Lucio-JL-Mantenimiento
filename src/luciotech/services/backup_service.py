"""Servicio de copias de seguridad."""

from __future__ import annotations

import json
import logging
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget, QInputDialog

from luciotech.config import get_data_dir

logger = logging.getLogger(__name__)


class BackupService:
    """Crear y restaurar copias de seguridad."""

    BACKUP_EXTENSION = ".jlmb"  # JL Mantenimiento Backup

    @classmethod
    def create_backup(cls, parent: QWidget | None = None) -> str | None:
        """Crear copia de seguridad completa.

        Incluye: base de datos, fotografías, configuración.
        Retorna la ruta del archivo creado.
        """
        # Seleccionar destino
        dest_dir = QFileDialog.getExistingDirectory(
            parent or QWidget(),
            "Seleccionar carpeta para la copia de seguridad",
        )
        if not dest_dir:
            return None

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"JL_Mantenimiento_Backup_{timestamp}{cls.BACKUP_EXTENSION}"
        backup_path = Path(dest_dir) / backup_name

        data_dir = get_data_dir()
        db_path = data_dir / "database.sqlite3"
        attachments_dir = data_dir / "attachments"

        try:
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Base de datos
                if db_path.exists():
                    # Verificar integridad antes de incluir
                    if not cls._verify_db_integrity(str(db_path)):
                        reply = QMessageBox.question(
                            parent, "Advertencia",
                            "La base de datos podría estar corrupta. ¿Desea continuar con la copia?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return None

                    zf.write(db_path, "database.sqlite3")

                # Fotografías
                if attachments_dir.exists():
                    for photo_file in attachments_dir.rglob("*"):
                        if photo_file.is_file():
                            arc_name = str(photo_file.relative_to(data_dir))
                            zf.write(photo_file, arc_name)

                # Metadatos de la copia
                metadata = {
                    "created_at": datetime.now().isoformat(),
                    "version": "0.1.0",
                    "db_path": str(db_path),
                    "photo_count": len(list(attachments_dir.rglob("*"))) if attachments_dir.exists() else 0,
                }
                zf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))

            logger.info("Copia de seguridad creada: %s (%.1f MB)", backup_path, backup_path.stat().st_size / 1024 / 1024)
            return str(backup_path)

        except Exception as e:
            logger.exception("Error creando copia de seguridad")
            QMessageBox.critical(parent or QWidget(), "Error", f"No se pudo crear la copia: {e}")
            return None

    @classmethod
    def restore_backup(cls, parent: QWidget | None = None) -> bool:
        """Restaurar desde una copia de seguridad.

        Crea automáticamente una copia del estado actual antes de restaurar.
        Retorna True si la restauración fue exitosa.
        """
        # Seleccionar archivo
        backup_path, _ = QFileDialog.getOpenFileName(
            parent or QWidget(),
            "Seleccionar copia de seguridad",
            "",
            f"Backup files (*{cls.BACKUP_EXTENSION});;ZIP files (*.zip);;All files (*)",
        )
        if not backup_path:
            return False

        # Advertencia
        reply = QMessageBox.warning(
            parent or QWidget(),
            "Restaurar copia de seguridad",
            "Esta operación REEMPLAZARÁ todos los datos actuales.\n"
            "Se creará automáticamente una copia del estado actual antes de continuar.\n\n"
            "¿Desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False

        data_dir = get_data_dir()

        # Crear copia del estado actual
        pre_restore_backup = cls.create_backup(parent)
        if pre_restore_backup:
            logger.info("Copia pre-restauración creada: %s", pre_restore_backup)

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                # Verificar contenido
                namelist = zf.namelist()
                if "database.sqlite3" not in namelist:
                    QMessageBox.critical(parent or QWidget(), "Error", "La copia de seguridad no contiene una base de datos válida.")
                    return False

                # Extraer
                zf.extractall(data_dir)

            # Verificar la base de datos restaurada
            restored_db = data_dir / "database.sqlite3"
            if not cls._verify_db_integrity(str(restored_db)):
                QMessageBox.warning(
                    parent or QWidget(), "Advertencia",
                    "La base de datos restaurada podría tener problemas.\n"
                    "Se recomienda crear una nueva copia de seguridad.",
                )

            logger.info("Copia de seguridad restaurada desde: %s", backup_path)
            QMessageBox.information(
                parent or QWidget(),
                "Restauración completada",
                f"Copia restaurada exitosamente desde:\n{backup_path}\n\n"
                f"Se recomienda reiniciar la aplicación.",
            )
            return True

        except zipfile.BadZipFile:
            QMessageBox.critical(parent or QWidget(), "Error", "El archivo no es una copia de seguridad válida.")
            return False
        except Exception as e:
            logger.exception("Error restaurando copia de seguridad")
            QMessageBox.critical(parent or QWidget(), "Error", f"No se pudo restaurar la copia: {e}")
            return False

    @classmethod
    def list_backups(cls, backup_dir: Path | None = None) -> list[dict]:
        """Listar copias de seguridad disponibles."""
        if backup_dir is None:
            backup_dir = get_data_dir() / "backups"

        if not backup_dir.exists():
            return []

        backups = []
        for f in sorted(backup_dir.glob(f"*{cls.BACKUP_EXTENSION}"), reverse=True):
            try:
                with zipfile.ZipFile(f, "r") as zf:
                    metadata = json.loads(zf.read("backup_metadata.json")) if "backup_metadata.json" in zf.namelist() else {}
                backups.append({
                    "path": str(f),
                    "name": f.name,
                    "size_mb": f.stat().st_size / 1024 / 1024,
                    "created_at": metadata.get("created_at", "Desconocido"),
                    "photo_count": metadata.get("photo_count", 0),
                })
            except Exception:
                backups.append({
                    "path": str(f),
                    "name": f.name,
                    "size_mb": f.stat().st_size / 1024 / 1024,
                    "created_at": "Error al leer",
                    "photo_count": 0,
                })
        return backups

    @staticmethod
    def _verify_db_integrity(db_path: str) -> bool:
        """Verificar integridad de la base de datos SQLite."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result and result[0] == "ok"
        except Exception:
            return False
