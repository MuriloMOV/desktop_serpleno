from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _build_fpdf_report(report_type: str, report_data: dict[str, Any], report_name: str) -> bytes:
    try:
        from fpdf import FPDF  # type: ignore

        class RelatorioPDF(FPDF):
            def header(self) -> None:
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(80, 80, 80)
                self.cell(0, 8, "SerPleno Desktop", border=0, align="L")
                self.cell(0, 8, report_type.upper(), border=0, align="R")
                self.ln(6)
                self.set_draw_color(200, 200, 200)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(4)

            def footer(self) -> None:
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f"Página {self.page_no()}", align="C")

        pdf = RelatorioPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 10, report_name, ln=True, align="C")
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"Tipo: {report_type}", ln=True)
        pdf.ln(4)
        summary = report_data.get("summary") if isinstance(report_data, dict) else None
        if isinstance(summary, dict):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "Resumo", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for key, value in summary.items():
                pdf.cell(0, 7, f"{key}: {value}", ln=True)
            pdf.ln(4)
        for key, value in (report_data or {}).items():
            if key == "summary":
                continue
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, str(key).replace("_", " ").title(), ln=True)
            pdf.set_font("Helvetica", "", 10)
            if isinstance(value, list):
                for item in value[:50]:
                    pdf.multi_cell(0, 6, str(item))
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    pdf.cell(0, 6, f"{sub_key}: {sub_value}", ln=True)
            else:
                pdf.multi_cell(0, 6, str(value))
            pdf.ln(2)
        return pdf.output(dest="S").encode("latin-1", errors="replace")
    except ImportError:
        return b""


def _render_markdown_html(text: str) -> str:
    sanitized = text.replace("&", "&").replace("<", "<").replace(">", ">")
    return f"<para>{sanitized}</para>"


def _build_reportlab_report(report_type: str, report_data: dict[str, Any], report_name: str) -> bytes:
    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
        from reportlab.platypus import (  # type: ignore
            Paragraph,
            SimpleDocTemplate,
            Table,
            TableStyle,
            Spacer,
        )

        buffer = __import__("io").BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story: list[Any] = []
        story.append(Paragraph(f"<b>{report_name}</b>", styles["Title"]))
        story.append(Paragraph(f"Tipo: {report_type}", styles["Normal"]))
        story.append(Spacer(1, 12))
        summary = report_data.get("summary") if isinstance(report_data, dict) else None
        if isinstance(summary, dict):
            table_data = [[str(k), str(v)] for k, v in summary.items()]
            story.append(Table(table_data, colWidths=[200, 300], style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])))
            story.append(Spacer(1, 12))
        for key, value in (report_data or {}).items():
            if key == "summary":
                continue
            story.append(Paragraph(f"<b>{str(key).replace('_', ' ').title()}</b>", styles["Heading2"]))
            if isinstance(value, list):
                for item in value[:50]:
                    story.append(Paragraph(_render_markdown_html(str(item)), styles["Normal"]))
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    story.append(Paragraph(f"{sub_key}: {sub_value}", styles["Normal"]))
            else:
                story.append(Paragraph(_render_markdown_html(str(value)), styles["Normal"]))
            story.append(Spacer(1, 6))
        try:
            from reportlab.graphics.barcode import qr  # type: ignore
            from reportlab.graphics.shapes import Drawing  # type: ignore
            qr_code = qr.QrCodeWidget(report_name)
            bounds = qr_code.getBounds()
            d = Drawing(54, 54)
            d.add(qr_code)
            story.append(Spacer(1, 12))
            story.append(d)
        except Exception:
            pass
        doc.build(story)
        return buffer.getvalue()
    except ImportError as exc:
        raise ImportError(
            "Nenhuma biblioteca de PDF disponível. Instale 'fpdf2' ou 'reportlab'."
        ) from exc


def gerar_pdf_relatorio(
    report_type: str,
    report_data: dict[str, Any],
    report_name: str,
) -> bytes:
    pdf_bytes = _build_fpdf_report(report_type, report_data, report_name)
    if pdf_bytes:
        return pdf_bytes
    return _build_reportlab_report(report_type, report_data, report_name)
