"""
Módulo de exportación a PDF para JMEJCat
Sistema unificado con soporte para notas y tablas
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from PySide6.QtGui import (
    QTextDocument,
    QPageSize,
    QTextCursor,
    QTextBlockFormat,
    QTextCharFormat,
    QFont,
    QColor,
    QPainter,
    QPdfWriter,
)
from PySide6.QtCore import Qt, QThread, Signal, QRectF
from PySide6.QtWidgets import QApplication

from config import APP_AUTHOR, APP_WEBSITE

logger = logging.getLogger(__name__)


class BasePDFExporter(QThread):
    """Clase base para exportación PDF con estilo común"""

    progress = Signal(int)
    finished = Signal(bool, str, str)

    def __init__(self, output_path: Path):
        super().__init__()
        self.output_path = output_path
        self.writer = None
        self.page_rect = None
        self.document = None
        self.painter = None
        self.page_count = 0

    def run(self):
        try:
            self._setup_writer()
            self._write_content()
            self._render_pdf()
            self.finished.emit(
                True,
                f"PDF exportat correctament a:\n{self.output_path}",
                str(self.output_path),
            )
        except Exception as e:
            logger.error(f"Error exportant a PDF: {e}")
            self.finished.emit(False, f"Error exportant a PDF:\n{str(e)}", "")

    def _setup_writer(self):
        """Configura QPdfWriter y documento base"""
        self.writer = QPdfWriter(str(self.output_path))
        self.writer.setPageSize(QPageSize.PageSizeId.A4)
        self.writer.setResolution(72)

        self.page_rect = self.writer.pageLayout().paintRectPixels(72)

        self.document = QTextDocument()
        self.document.setPageSize(self.page_rect.size())
        self.document.setDocumentMargin(10)

    def _write_content(self):
        """Método abstracto - debe implementarse en subclases"""
        raise NotImplementedError("Subclases deben implementar _write_content")

    def _render_pdf(self):
        """Renderiza el documento a PDF con footer"""
        self.page_count = self.document.pageCount()

        self.painter = QPainter(self.writer)

        for page_num in range(self.page_count):
            if page_num > 0:
                self.writer.newPage()

            current_page_rect = self.writer.pageLayout().paintRectPixels(72)

            self.painter.save()
            self.painter.translate(0, -page_num * current_page_rect.height())

            self.document.drawContents(self.painter)

            self.painter.restore()

            self._draw_footer(
                self.painter, current_page_rect, page_num + 1, self.page_count
            )

        self.painter.end()
        logger.info(f"PDF exportat a {self.output_path}")

    def _draw_footer(
        self, painter: QPainter, page_rect: QRectF, current_page: int, total_pages: int
    ):
        """Dibuja footer común"""
        footer_y = page_rect.bottom() - 40

        painter.setPen(QColor("#CCCCCC"))
        painter.drawLine(
            int(page_rect.left() + 20),
            int(footer_y - 5),
            int(page_rect.right() - 20),
            int(footer_y - 5),
        )

        painter.setPen(QColor("#666666"))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        footer_text = f"JMEJCat | {APP_AUTHOR} | {APP_WEBSITE}"
        text_rect = QRectF(page_rect.left() + 20, footer_y, page_rect.width() - 40, 20)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            footer_text,
        )

        page_text = f"Pàgina {current_page} de {total_pages}"
        page_rect_text = QRectF(
            page_rect.left() + 20, footer_y + 15, page_rect.width() - 40, 20
        )
        painter.drawText(page_rect_text, Qt.AlignmentFlag.AlignHCenter, page_text)

    def _insert_page_break(self, cursor: QTextCursor):
        """Inserta salto de página"""
        fmt = QTextBlockFormat()
        fmt.setPageBreakPolicy(QTextBlockFormat.PageBreakFlag.PageBreak_AlwaysBefore)
        cursor.insertBlock(fmt)


class NotesPDFExporter(BasePDFExporter):
    """Exportador de notas con formato elegante (original)"""

    def __init__(self, notes: List[Dict[str, Any]], output_path: Path):
        super().__init__(output_path)
        self.notes = notes

    def _write_content(self):
        """Escribe todas las notas con formato"""
        cursor = QTextCursor(self.document)

        for i, note in enumerate(self.notes):
            if i > 0:
                self._insert_page_break(cursor)

            self._write_note(cursor, note)
            self.progress.emit(int(((i + 1) / len(self.notes)) * 100))
            QApplication.processEvents()

    def _write_note(self, cursor: QTextCursor, note: Dict[str, Any]):
        """Escribe una nota con formato elegante"""
        title = note.get("title", "Sense títit")
        created = note.get("created_at", "")
        request = note.get("request", "")
        solution = note.get("solution", "")
        examples = note.get("examples", "")

        if created:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created)
                created = dt.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                pass

        # Título (header azul)
        title_block = QTextBlockFormat()
        title_block.setBackground(QColor("#2196F3"))
        title_block.setTopMargin(10)
        title_block.setBottomMargin(10)
        title_block.setLeftMargin(10)
        title_block.setRightMargin(10)

        title_char = QTextCharFormat()
        title_char.setFontWeight(QFont.Weight.Bold)
        title_char.setFontPointSize(16)
        title_char.setForeground(QColor("#FFFFFF"))

        cursor.insertBlock(title_block, title_char)
        cursor.insertText(self._escape_text(title))

        # Metadata (subheader azul claro)
        meta_block = QTextBlockFormat()
        meta_block.setBackground(QColor("#2196F3"))
        meta_block.setBottomMargin(10)
        meta_block.setLeftMargin(10)

        meta_char = QTextCharFormat()
        meta_char.setFontPointSize(9)
        meta_char.setForeground(QColor("#E3F2FD"))

        cursor.insertBlock(meta_block, meta_char)
        cursor.insertText(f"Creat: {created} | ID: {note.get('id', 'N/A')}")

        # Secciones
        if request:
            self._write_section(cursor, "Petició", request)
        if solution:
            self._write_section(cursor, "Solució", solution)
        if examples:
            self._write_section(cursor, "Exemples", examples)

    def _write_section(self, cursor: QTextCursor, title: str, content: str):
        """Escribe una sección con título y contenido"""
        section_block = QTextBlockFormat()
        section_block.setTopMargin(15)
        section_block.setBottomMargin(5)

        section_char = QTextCharFormat()
        section_char.setFontWeight(QFont.Weight.Bold)
        section_char.setFontPointSize(12)
        section_char.setForeground(QColor("#1976D2"))
        section_char.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        cursor.insertBlock(section_block, section_char)
        cursor.insertText(title)

        content_block = QTextBlockFormat()
        content_block.setLeftMargin(10)
        content_block.setTopMargin(8)

        content_char = QTextCharFormat()
        content_char.setFontPointSize(10)

        cursor.insertBlock(content_block, content_char)
        cursor.insertHtml(content)

    def _escape_text(self, text: str) -> str:
        """Escapa caracteres HTML"""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class TablePDFExporter(BasePDFExporter):
    """Exportador de tablas con formato elegante (para Tramitación)"""

    def __init__(
        self,
        data: List[List[str]],
        headers: List[str],
        output_path: Path,
        title: str = "Tramitació",
    ):
        super().__init__(output_path)
        self.data = data
        self.headers = headers
        self.title = title

    def _write_content(self):
        """Escribe tabla con formato elegante"""
        cursor = QTextCursor(self.document)

        # Título
        title_block = QTextBlockFormat()
        title_block.setBackground(QColor("#2196F3"))
        title_block.setTopMargin(10)
        title_block.setBottomMargin(10)
        title_block.setLeftMargin(10)
        title_block.setRightMargin(10)

        title_char = QTextCharFormat()
        title_char.setFontWeight(QFont.Weight.Bold)
        title_char.setFontPointSize(16)
        title_char.setForeground(QColor("#FFFFFF"))

        cursor.insertBlock(title_block, title_char)
        cursor.insertText(self.title)

        # Tabla
        self._write_table(cursor)
        self.progress.emit(100)
        QApplication.processEvents()

    def _write_table(self, cursor: QTextCursor):
        """Escribe tabla con formato HTML elegante"""
        # Construir tabla HTML con estilos
        html_table = '<table border="1" cellpadding="8" cellspacing="0" style="width: 100%; border-collapse: collapse; margin: 10px 0;">'

        # Header de tabla
        html_table += '<thead><tr style="background-color: #424242;">'
        for header in self.headers:
            html_table += f'<th style="color: white; padding: 8px; text-align: left; font-weight: bold;">{header}</th>'
        html_table += "</tr></thead>"

        # Datos de la tabla
        html_table += "<tbody>"
        for i, row_data in enumerate(self.data):
            bg_color = "#F5F5F5" if i % 2 == 0 else "#FFFFFF"
            html_table += f'<tr style="background-color: {bg_color};">'
            for cell in row_data:
                html_table += (
                    f'<td style="padding: 8px; border: 1px solid #DDDDDD;">{cell}</td>'
                )
            html_table += "</tr>"
        html_table += "</tbody></table>"

        # Insertar la tabla HTML
        cursor.insertHtml(html_table)


# Funciones de conveniencia para compatibilidad hacia atrás


def export_notes_to_pdf(
    notes: List[Dict[str, Any]], output_path: Path, parent=None, callback=None
) -> NotesPDFExporter:
    """Exporta notas a PDF (API original)"""
    exporter = NotesPDFExporter(notes, output_path)
    if parent and callback:
        exporter.finished.connect(callback)
    exporter.start()
    return exporter


def export_table_to_pdf(
    data: List[List[str]],
    headers: List[str],
    output_path: Path,
    title: str = "Tramitació",
    parent=None,
    callback=None,
) -> TablePDFExporter:
    """Exporta tabla a PDF (nuevo)"""
    exporter = TablePDFExporter(data, headers, output_path, title)
    if parent and callback:
        exporter.finished.connect(callback)
    exporter.start()
    return exporter
