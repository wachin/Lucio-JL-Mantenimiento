"""Servicio de generación de documentos PDF."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from luciotech.database.models import ServiceOrder, Photo
from luciotech.config import get_data_dir

logger = logging.getLogger(__name__)

# Tamaño de celda para miniaturas en PDF
THUMB_SIZE_PDF = 45 * mm


class PDFBuilder:
    """Constructor base de documentos PDF."""

    def __init__(
        self,
        title: str = "",
        page_size=A4,
        orientation: str = "portrait",
        margins: tuple[float, float, float, float] = (2 * cm, 2 * cm, 2 * cm, 2 * cm),
    ) -> None:
        self.title = title
        self.page_size = page_size
        if orientation == "landscape":
            self.page_size = (page_size[1], page_size[0])
        self.margins = margins
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.page_size,
            leftMargin=margins[0],
            rightMargin=margins[1],
            topMargin=margins[2],
            bottomMargin=margins[3],
            title=title,
            author="JL Mantenimiento",
        )
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.story: list = []

    def _setup_styles(self) -> None:
        """Configurar estilos personalizados."""
        self.styles.add(ParagraphStyle(
            name="DocTitle",
            parent=self.styles["Title"],
            fontSize=20,
            spaceAfter=6 * mm,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1a1a2e"),
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=13,
            spaceBefore=8 * mm,
            spaceAfter=4 * mm,
            textColor=colors.HexColor("#16213e"),
            borderWidth=1,
            borderColor=colors.HexColor("#0f3460"),
            borderPadding=4,
        ))
        self.styles.add(ParagraphStyle(
            name="LabelStyle",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555"),
            fontName="Helvetica-Bold",
        ))
        self.styles.add(ParagraphStyle(
            name="ValueStyle",
            parent=self.styles["Normal"],
            fontSize=10,
            spaceAfter=2 * mm,
        ))
        self.styles.add(ParagraphStyle(
            name="FooterStyle",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#888"),
            alignment=TA_CENTER,
        ))

    def _add_field(self, label: str, value: str, bold_label: bool = True) -> None:
        """Añadir par etiqueta-valor."""
        if bold_label:
            self.story.append(Paragraph(f"<b>{label}:</b>", self.styles["LabelStyle"]))
        else:
            self.story.append(Paragraph(f"{label}:", self.styles["LabelStyle"]))
        self.story.append(Paragraph(value or "—", self.styles["ValueStyle"]))

    def _add_separator(self) -> None:
        self.story.append(Spacer(1, 3 * mm))
        self.story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ccc")))
        self.story.append(Spacer(1, 3 * mm))

    def _add_section(self, title: str) -> None:
        self.story.append(Paragraph(title, self.styles["SectionHeader"]))

    def _build_table(self, headers: list[str], data: list[list[str]], col_widths: list[float] | None = None) -> Table:
        """Crear tabla con encabezado estilizado."""
        header_style = ParagraphStyle("HeaderCell", fontSize=9, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)
        cell_style = ParagraphStyle("CellData", fontSize=9, fontName="Helvetica", alignment=TA_LEFT)

        header_cells = [Paragraph(h, header_style) for h in headers]
        rows = [header_cells]

        for row in data:
            row_cells = [Paragraph(str(c), cell_style) for c in row]
            rows.append(row_cells)

        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f8f8")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f8f8"), colors.white]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def add_header(self, workshop_name: str, technician: str = "", address: str = "", phone: str = "", email: str = "") -> None:
        """Encabezado con datos del taller."""
        self.story.append(Paragraph(workshop_name, self.styles["DocTitle"]))
        if technician:
            self.story.append(Paragraph(f"Técnico: {technician}", ParagraphStyle("SubHeader", parent=self.styles["Normal"], fontSize=11, alignment=TA_CENTER)))
        details = []
        if address:
            details.append(address)
        if phone:
            details.append(f"Tel: {phone}")
        if email:
            details.append(email)
        if details:
            self.story.append(Paragraph(" | ".join(details), self.styles["FooterStyle"]))
        self.story.append(Spacer(1, 5 * mm))
        self._add_separator()

    def add_photos(self, photos: Sequence[Photo], max_per_row: int = 4) -> None:
        """Añadir miniaturas de fotografías."""
        if not photos:
            return
        self._add_section("Fotografías")
        rows_data = []
        current_row = []
        for photo in photos:
            try:
                if Path(photo.file_path).exists():
                    img = Image(photo.file_path, width=THUMB_SIZE_PDF, height=THUMB_SIZE_PDF)
                    img.hAlign = "CENTER"
                    current_row.append(img)
            except Exception as e:
                logger.error("Error cargando foto en PDF: %s", e)
            if len(current_row) >= max_per_row:
                rows_data.append(current_row)
                current_row = []
        if current_row:
            rows_data.append(current_row)

        for row in rows_data:
            t = Table([row], colWidths=[THUMB_SIZE_PDF] * len(row))
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            self.story.append(t)
            self.story.append(Spacer(1, 2 * mm))

    def add_signature_lines(self, labels: list[tuple[str, str]] = None) -> None:
        """Añadir líneas para firmas."""
        if labels is None:
            labels = [("Firma del Cliente", "Firma del Técnico")]
        self.story.append(Spacer(1, 15 * mm))
        sig_data = []
        for l1, l2 in labels:
            sig_data.append([
                Paragraph("_" * 30, ParagraphStyle("SigLine", fontSize=10, alignment=TA_CENTER)),
                Paragraph("_" * 30, ParagraphStyle("SigLine2", fontSize=10, alignment=TA_CENTER)),
            ])
            sig_data.append([
                Paragraph(l1, ParagraphStyle("SigLabel", fontSize=8, alignment=TA_CENTER)),
                Paragraph(l2, ParagraphStyle("SigLabel2", fontSize=8, alignment=TA_CENTER)),
            ])
        for row in sig_data:
            t = Table([row], colWidths=[7 * cm, 7 * cm])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            self.story.append(t)

    def build(self) -> bytes:
        """Generar el PDF y retornar bytes."""
        self.doc.build(self.story)
        return self.buffer.getvalue()

    def save_to_file(self, file_path: str) -> str:
        """Generar y guardar PDF. Retorna la ruta."""
        data = self.build()
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.info("PDF guardado: %s (%.1f KB)", file_path, len(data) / 1024)
        return file_path


class ReceiptPDFService:
    """Generar comprobante de recepción."""

    @staticmethod
    def generate(order: ServiceOrder, output_path: str | None = None) -> str:
        customer = order.customer
        equipment = order.equipment
        photos = order.photos[:6]  # Max 6 en comprobante

        builder = PDFBuilder(title=f"Comprobante de Recepción - {order.order_number}")

        # Encabezado
        builder.add_header("JL Mantenimiento", order.technician or "Ing. Joseph Lucio")

        # Título del documento
        builder.story.append(Paragraph("COMPROBANTE DE RECEPCIÓN", builder.styles["DocTitle"]))
        builder.story.append(Spacer(1, 5 * mm))

        # Datos de la orden
        builder._add_section("Datos de la Orden")
        builder._add_field("Nº Orden", order.order_number)
        builder._add_field("Fecha de ingreso", order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else "")
        builder._add_field("Fecha estimada de entrega", order.estimated_delivery_date.strftime("%Y-%m-%d") if order.estimated_delivery_date else "No definida")
        builder._add_field("Estado", order.status)
        builder._add_field("Prioridad", order.priority)

        # Datos del cliente
        builder._add_section("Datos del Cliente")
        if customer:
            builder._add_field("Nombre", customer.full_name)
            builder._add_field("Identificación", customer.id_number or "No registrada")
            builder._add_field("Teléfono", customer.phone_primary)
            if customer.phone_secondary:
                builder._add_field("Teléfono alternativo", customer.phone_secondary)
            if customer.email:
                builder._add_field("Correo", customer.email)
            if customer.address:
                builder._add_field("Dirección", customer.address)

        # Datos del equipo
        builder._add_section("Datos del Equipo")
        if equipment:
            builder._add_field("Tipo", equipment.equipment_type)
            builder._add_field("Marca", equipment.brand or "No especificada")
            builder._add_field("Modelo", equipment.model or "No especificado")
            builder._add_field("Nº Serie", equipment.serial_number or "No registrado")
            builder._add_field("Color", equipment.color or "No especificado")
            builder._add_field("Estado físico", equipment.physical_state or "No registrada")
            builder._add_field("Problema reportado", equipment.reported_problem or "No especificado")
            if equipment.accessories:
                builder._add_field("Accesorios recibidos", equipment.accessories)

        # Costos
        builder._add_section("Costos iniciales")
        builder._add_field("Costo de diagnóstico", f"${order.diagnostic_cost:,.2f}")
        builder._add_field("Anticipo recibido", f"${order.advance_payment:,.2f}")
        builder._add_field("Saldo pendiente", f"${order.balance:,.2f}")

        # Fotos
        if photos:
            builder.add_photos(photos)

        # Firmas
        builder.add_signature_lines()

        # Pie
        builder.story.append(Spacer(1, 10 * mm))
        builder.story.append(Paragraph("Conserve este comprobante para la entrega de su equipo.", builder.styles["FooterStyle"]))
        builder.story.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", builder.styles["FooterStyle"]))

        # Guardar
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            name_slug = (customer.full_name if customer else "Cliente").replace(" ", "-")[:30]
            output_path = str(Path(get_data_dir()) / "reports" / f"{ts}_{name_slug}_Comprobante-Recepcion.pdf")

        return builder.save_to_file(output_path)


class TechnicalReportPDFService:
    """Generar informe técnico."""

    @staticmethod
    def generate(order: ServiceOrder, output_path: str | None = None) -> str:
        customer = order.customer
        equipment = order.equipment
        photos = order.photos

        builder = PDFBuilder(title=f"Informe Técnico - {order.order_number}")
        builder.add_header("JL Mantenimiento", order.technician or "Ing. Joseph Lucio")

        builder.story.append(Paragraph("INFORME TÉCNICO", builder.styles["DocTitle"]))
        builder.story.append(Spacer(1, 5 * mm))

        # Orden
        builder._add_section("Orden de Servicio")
        builder._add_field("Nº Orden", order.order_number)
        builder._add_field("Fecha de ingreso", order.intake_date.strftime("%Y-%m-%d %H:%M") if order.intake_date else "")
        builder._add_field("Estado", order.status)
        builder._add_field("Técnico", order.technician or "No asignado")

        # Cliente y equipo
        builder._add_section("Cliente")
        if customer:
            builder._add_field("Nombre", customer.full_name)
            builder._add_field("Teléfono", customer.phone_primary)

        builder._add_section("Equipo")
        if equipment:
            builder._add_field("Tipo", equipment.equipment_type)
            builder._add_field("Marca/Modelo", f"{equipment.brand or ''} {equipment.model or ''}".strip())
            builder._add_field("Nº Serie", equipment.serial_number or "No registrado")
            builder._add_field("Problema reportado", equipment.reported_problem or "")

        # Diagnóstico
        builder._add_section("Diagnóstico Técnico")
        if order.diagnosis_html:
            from reportlab.lib.utils import simpleSplit
            # Strip HTML for plain text in PDF
            import re
            text = re.sub(r'<[^>]+>', '', order.diagnosis_html)
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
            builder.story.append(Paragraph(text, builder.styles["ValueStyle"]))
        else:
            builder.story.append(Paragraph("Sin diagnóstico registrado.", builder.styles["ValueStyle"]))

        # Trabajo realizado
        builder._add_section("Trabajo Realizado")
        if order.work_done_html:
            text = re.sub(r'<[^>]+>', '', order.work_done_html)
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
            builder.story.append(Paragraph(text, builder.styles["ValueStyle"]))
        else:
            builder.story.append(Paragraph("Sin trabajo registrado.", builder.styles["ValueStyle"]))

        # Recomendaciones
        builder._add_section("Recomendaciones")
        if order.recommendations_html:
            text = re.sub(r'<[^>]+>', '', order.recommendations_html)
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
            builder.story.append(Paragraph(text, builder.styles["ValueStyle"]))
        else:
            builder.story.append(Paragraph("Sin recomendaciones.", builder.styles["ValueStyle"]))

        # Repuestos
        if order.parts_used:
            builder._add_section("Repuestos Utilizados")
            builder.story.append(Paragraph(order.parts_used, builder.styles["ValueStyle"]))

        # Costos
        builder._add_section("Costos")
        cost_data = [
            ["Concepto", "Monto"],
            ["Diagnóstico", f"${order.diagnostic_cost:,.2f}"],
            ["Repuestos", f"${order.parts_cost:,.2f}"],
            ["Mano de obra", f"${order.labor_cost:,.2f}"],
            ["Subtotal", f"${order.total:,.2f}"],
            ["Descuento", f"-${order.discount:,.2f}"],
            ["Impuestos", f"${order.tax:,.2f}"],
            ["TOTAL", f"${order.total:,.2f}"],
            ["Anticipo", f"-${order.advance_payment:,.2f}"],
            ["SALDO PENDIENTE", f"${order.balance:,.2f}"],
        ]
        builder.story.append(builder._build_table(
            ["Concepto", "Monto"],
            [[r[0], r[1]] for r in cost_data[1:]],
        ))

        # Garantía
        builder._add_section("Garantía")
        builder._add_field("Días de garantía", f"{order.warranty_days} días")

        # Fotos
        if photos:
            builder.add_photos(photos)

        # Firmas
        builder.add_signature_lines()

        if not output_path:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            name_slug = (customer.full_name if customer else "Cliente").replace(" ", "-")[:30]
            output_path = str(Path(get_data_dir()) / "reports" / f"{ts}_{name_slug}_Informe-Tecnico.pdf")

        return builder.save_to_file(output_path)
