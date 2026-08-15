"""Servicio de copias de seguridad."""

from __future__ import annotations

import json
import logging
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from luciotech.config import get_data_dir
from luciotech.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class BackupService:
    """Crear y restaurar copias de seguridad."""

    BACKUP_EXTENSION = ".jlmb"  # JL Mantenimiento Backup

    @classmethod
    def create_backup(cls, parent=None, dest_dir: str | None = None) -> str | None:
        """Crear copia de seguridad completa (interfaz con diálogos)."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

        if dest_dir is None:
            dest_dir = QFileDialog.getExistingDirectory(
                parent or QWidget(),
                "Seleccionar carpeta para la copia de seguridad",
            )
        if not dest_dir:
            return None

        data_dir = get_data_dir()
        db_path = data_dir / "database.sqlite3"

        if db_path.exists() and not cls._verify_db_integrity(str(db_path)):
            reply = QMessageBox.question(
                parent, "Advertencia",
                "La base de datos podría estar corrupta. ¿Desea continuar con la copia?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return None

        try:
            result = cls.create_backup_to(dest_dir)
            return result
        except Exception as e:
            logger.exception("Error creando copia de seguridad")
            QMessageBox.critical(parent or QWidget(), "Error", f"No se pudo crear la copia: {e}")
            return None

    @classmethod
    def create_backup_to(cls, dest_dir: str) -> str:
        """Crear copia de seguridad en el directorio indicado (sin UI).

        Retorna la ruta del archivo creado. Lanza excepciones si algo falla.
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"JL_Mantenimiento_Backup_{timestamp}{cls.BACKUP_EXTENSION}"
        backup_path = Path(dest_dir) / backup_name

        data_dir = get_data_dir()
        db_path = data_dir / "database.sqlite3"
        attachments_dir = data_dir / "attachments"

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if db_path.exists():
                cls._backup_sqlite(str(db_path), zf)

            photo_count = 0
            if attachments_dir.exists():
                for photo_file in attachments_dir.rglob("*"):
                    if photo_file.is_file():
                        arc_name = str(photo_file.relative_to(data_dir))
                        zf.write(photo_file, arc_name)
                        photo_count += 1

            metadata = {
                "created_at": datetime.now().isoformat(),
                "version": "0.2.0",
                "db_path": str(db_path),
                "photo_count": photo_count,
            }
            zf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))

        logger.info(
            "Copia de seguridad creada: %s (%.1f MB)",
            backup_path,
            backup_path.stat().st_size / 1024 / 1024,
        )
        return str(backup_path)

    @classmethod
    def restore_backup(cls, parent=None) -> bool:
        """Restaurar desde una copia de seguridad.

        Crea automáticamente una copia del estado actual antes de restaurar.
        La restauración es transaccional: extrae a un directorio temporal,
        verifica integridad y solo entonces reemplaza los datos actuales.
        Retorna True si la restauración fue exitosa.
        """
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

        backup_path, _ = QFileDialog.getOpenFileName(
            parent or QWidget(),
            "Seleccionar copia de seguridad",
            "",
            f"Backup files (*{cls.BACKUP_EXTENSION});;ZIP files (*.zip);;All files (*)",
        )
        if not backup_path:
            return False

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

        # Copia pre-restauración automática
        try:
            pre_restore_backup = cls.create_backup(parent, dest_dir=str(data_dir / "backups"))
            if pre_restore_backup:
                logger.info("Copia pre-restauración creada: %s", pre_restore_backup)
        except Exception:
            logger.warning("No se pudo crear copia pre-restauración, continuando de todas formas")

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                namelist = zf.namelist()
                if "database.sqlite3" not in namelist:
                    QMessageBox.critical(
                        parent or QWidget(), "Error",
                        "La copia de seguridad no contiene una base de datos válida.",
                    )
                    return False

                # Validar todas las rutas contra Zip Slip
                if not cls._validate_zip_paths(namelist, data_dir):
                    QMessageBox.critical(
                        parent or QWidget(), "Error de seguridad",
                        "La copia de seguridad contiene rutas inválidas que podrían "
                        "escribir archivos fuera del directorio de datos.",
                    )
                    return False

                # Extraer a directorio temporal
                with tempfile.TemporaryDirectory(prefix="jlmb-restore-") as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    zf.extractall(tmpdir_path)

                    # Verificar integridad de la DB extraída
                    restored_db = tmpdir_path / "database.sqlite3"
                    if not cls._verify_db_integrity(str(restored_db)):
                        QMessageBox.warning(
                            parent or QWidget(), "Advertencia",
                            "La base de datos del backup parece corrupta.\n"
                            "La restauración se ha cancelado.",
                        )
                        return False

                    # Reemplazar datos actuales de forma atómica
                    cls._atomic_replace(tmpdir_path, data_dir)

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

    @classmethod
    def create_auto_backup(cls) -> str:
        """Crear copia de seguridad automática sin interacción UI.

        Guarda el archivo en ``get_data_dir() / "backups"`` y aplica la
        política de retención configurada (clave *auto_backup_retention*,
        valor predeterminado 5).  Retorna la ruta del backup creado.
        """
        backup_dir = get_data_dir() / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = cls.create_backup_to(str(backup_dir))

        # Aplicar retención: borrar los más antiguos si exceden el límite
        settings = SettingsService()
        retention = settings.get_int("auto_backup_retention", 5)
        if retention < 1:
            retention = 1

        backups = sorted(
            backup_dir.glob(f"*{cls.BACKUP_EXTENSION}"),
            key=lambda p: p.stat().st_mtime,
        )
        if len(backups) > retention:
            for old_backup in backups[: len(backups) - retention]:
                try:
                    old_backup.unlink()
                    logger.info("Backup antiguo eliminado (retención): %s", old_backup)
                except OSError as exc:
                    logger.warning("No se pudo eliminar backup antiguo %s: %s", old_backup, exc)

        logger.info("Auto-backup creado: %s", backup_path)
        return backup_path

    @classmethod
    def schedule_auto_backup(cls) -> str | None:
        """Crear un auto-backup si el último tiene más de 24 horas.

        Diseñado para invocarse al arranque de la aplicación.  Retorna la
        ruta del backup creado o ``None`` si no fue necesario.
        """
        backup_dir = get_data_dir() / "backups"
        if not backup_dir.exists():
            return cls.create_auto_backup()

        backups = sorted(
            backup_dir.glob(f"*{cls.BACKUP_EXTENSION}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not backups:
            return cls.create_auto_backup()

        last_backup = backups[0]
        age = datetime.now() - datetime.fromtimestamp(last_backup.stat().st_mtime)
        if age > timedelta(hours=24):
            logger.info("Último backup con antigüedad de %s, creando nuevo", age)
            return cls.create_auto_backup()

        logger.debug("Auto-backup omitido, último backup hace %s", age)
        return None

    @staticmethod
    def _validate_zip_paths(namelist: list[str], data_dir: Path) -> bool:
        """Validar que ninguna ruta del ZIP escape del directorio de destino.

        Previene ataques Zip Slip donde nombres como ``../../etc/passwd``
        escribirían archivos fuera del directorio esperado.
        """
        resolved_data = data_dir.resolve()
        for name in namelist:
            target = (resolved_data / name).resolve()
            if not str(target).startswith(str(resolved_data)):
                logger.error("Ruta inválida detectada en ZIP: %s", name)
                return False
        return True

    @staticmethod
    def _backup_sqlite(db_path: str, zf: zipfile.ZipFile) -> None:
        """Crear copia consistente de SQLite usando la API de backup.

        Usa ``sqlite3.Connection.backup()`` para obtener una instantánea
        consistente aunque la base de datos esté en uso.
        """
        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            source = sqlite3.connect(db_path)
            dest = sqlite3.connect(tmp_path)
            try:
                source.backup(dest)
            finally:
                dest.close()
                source.close()
            zf.write(tmp_path, "database.sqlite3")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @staticmethod
    def _atomic_replace(source_dir: Path, target_dir: Path) -> None:
        """Reemplazar archivos del directorio de datos desde el staging.

        Solo reemplaza archivos conocidos (database.sqlite3 y attachments/).
        No borra otros archivos existentes que no estén en el backup.
        """
        # Reemplazar base de datos
        src_db = source_dir / "database.sqlite3"
        dst_db = target_dir / "database.sqlite3"
        if src_db.exists():
            if dst_db.exists():
                dst_db.unlink()
            shutil.copy2(str(src_db), str(dst_db))

        # Reemplazar attachments
        src_attach = source_dir / "attachments"
        dst_attach = target_dir / "attachments"
        if src_attach.exists():
            if dst_attach.exists():
                shutil.rmtree(str(dst_attach))
            shutil.copytree(str(src_attach), str(dst_attach))

    @staticmethod
    def _verify_db_integrity(db_path: str) -> bool:
        """Verificar integridad de la base de datos SQLite."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0] == "ok"
        except Exception:
            return False
