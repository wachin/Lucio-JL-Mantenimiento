"""Servicio para gestión de imágenes y fotografías."""

from __future__ import annotations

import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, ExifTags
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox

from luciotech.config import get_data_dir
from luciotech.database.models import Photo
from luciotech.database.repositories import PhotoRepo
from luciotech.database.connection import get_session

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
THUMBNAIL_SIZE = 200
MAX_IMAGE_SIZE = 1920  # max dimension for storage


class ImageService:
    """Servicio para procesar y almacenar imágenes."""

    @staticmethod
    def get_attachments_dir(order_number: str) -> Path:
        """Obtener directorio de adjuntos para una orden."""
        return get_data_dir() / "attachments" / order_number

    @staticmethod
    def generate_unique_name(original_name: str) -> str:
        """Generar nombre único para la imagen."""
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            ext = ".jpg"
        return f"{uuid.uuid4().hex}{ext}"

    @staticmethod
    def correct_orientation(image: Image.Image) -> Image.Image:
        """Corregir orientación EXIF."""
        try:
            exif = image.getexif()
            orientation = exif.get(0x0112)  # Orientation tag
            if orientation:
                methods = {
                    2: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),
                    3: lambda img: img.rotate(180, expand=True),
                    4: lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),
                    5: lambda img: img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT),
                    6: lambda img: img.rotate(-90, expand=True),
                    7: lambda img: img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT),
                    8: lambda img: img.rotate(90, expand=True),
                }
                if orientation in methods:
                    return methods[orientation](image)
        except (AttributeError, KeyError, IndexError):
            pass
        return image

    @classmethod
    def process_image(cls, source_path: str, order_number: str) -> dict:
        """Procesar y guardar imagen.

        Returns:
            dict con file_path, file_name, thumbnail_path
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Imagen no encontrada: {source_path}")

        # Crear directorio
        attach_dir = cls.get_attachments_dir(order_number)
        attach_dir.mkdir(parents=True, exist_ok=True)

        # Generar nombre único
        unique_name = cls.generate_unique_name(source.name)
        dest_path = attach_dir / unique_name

        # Procesar imagen
        img = Image.open(source)
        img = cls.correct_orientation(img)

        # Redimensionar si es muy grande
        if max(img.size) > MAX_IMAGE_SIZE:
            ratio = MAX_IMAGE_SIZE / max(img.size)
            new_size = tuple(int(d * ratio) for d in img.size)
            img = img.resize(new_size, Image.LANCZOS)

        # Guardar
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGB")
            dest_path = dest_path.with_suffix(".jpg")
            unique_name = dest_path.name
            img.save(dest_path, "JPEG", quality=85)
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(dest_path, "JPEG", quality=85)

        # Crear miniatura
        thumb_path = attach_dir / f"thumb_{unique_name}"
        thumb = img.copy()
        thumb.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        thumb.save(thumb_path, "JPEG", quality=75)

        logger.info("Imagen procesada: %s -> %s", source.name, dest_path.name)
        return {
            "file_path": str(dest_path),
            "file_name": dest_path.name,
            "thumbnail_path": str(thumb_path),
            "original_name": source.name,
        }

    @staticmethod
    def rotate_image(file_path: str, degrees: int = 90) -> None:
        """Rotar imagen."""
        path = Path(file_path)
        if not path.exists():
            return
        img = Image.open(path)
        img = img.rotate(-degrees, expand=True)  # negative for clockwise
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGB")
        img.save(path, "JPEG", quality=85)

        # Also rotate thumbnail
        thumb_path = path.parent / f"thumb_{path.name}"
        if thumb_path.exists():
            thumb = Image.open(thumb_path)
            thumb = thumb.rotate(-degrees, expand=True)
            if thumb.mode in ("RGBA", "LA"):
                thumb = thumb.convert("RGB")
            thumb.save(thumb_path, "JPEG", quality=75)

    @staticmethod
    def get_thumbnail_path(file_path: str) -> str | None:
        """Obtener ruta de miniatura."""
        path = Path(file_path)
        thumb = path.parent / f"thumb_{path.name}"
        if thumb.exists():
            return str(thumb)
        # Generate on the fly
        try:
            img = Image.open(path)
            img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
            thumb_path = path.parent / f"thumb_{path.name}"
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(thumb_path, "JPEG", quality=75)
            return str(thumb_path)
        except Exception as e:
            logger.error("Error generando miniatura: %s", e)
            return None


class PhotoService:
    """Servicio de alto nivel para gestionar fotos de órdenes."""

    def __init__(self) -> None:
        self.session = get_session()
        self.repo = PhotoRepo(self.session)
        self.image_service = ImageService()

    def add_photos(self, order_id: int, order_number: str, file_paths: list[str], photo_type: str = "Otro") -> list[Photo]:
        """Añadir múltiples fotos a una orden."""
        photos = []
        for path in file_paths:
            try:
                result = self.image_service.process_image(path, order_number)
                photo = Photo(
                    order_id=order_id,
                    file_path=result["file_path"],
                    file_name=result["file_name"],
                    description=result["original_name"],
                    photo_type=photo_type,
                    capture_date=datetime.now(),
                    sort_order=0,
                )
                photo = self.repo.create(photo)
                photos.append(photo)
            except Exception as e:
                logger.error("Error al añadir foto %s: %s", path, e)
        return photos

    def get_photos(self, order_id: int) -> list[Photo]:
        return list(self.repo.get_by_order(order_id))

    def delete_photo(self, photo: Photo) -> None:
        """Eliminar foto y su archivo."""
        try:
            Path(photo.file_path).unlink(missing_ok=True)
            thumb = Path(photo.file_path).parent / f"thumb_{Path(photo.file_path).name}"
            thumb.unlink(missing_ok=True)
        except Exception as e:
            logger.error("Error eliminando archivo de foto: %s", e)
        self.repo.delete(photo)

    def rotate_photo(self, photo: Photo, degrees: int = 90) -> None:
        self.image_service.rotate_image(photo.file_path, degrees)

    def reorder_photos(self, photo_orders: list[tuple[int, int]]) -> None:
        self.repo.reorder(photo_orders)
