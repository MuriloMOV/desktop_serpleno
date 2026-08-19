from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ReportTemplate:
    id: int
    name: str
    template_type: str
    content: str
    sections: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def render_template(self, context: dict[str, Any]) -> str:
        try:
            from string import Template
            return Template(self.content).safe_substitute(context)
        except Exception:
            return self.content

    def export_to_format(self, data: dict[str, Any], format_type: str) -> bytes:
        try:
            from ser_pleno.application.services.pdf import gerar_pdf_relatorio
            if format_type == "pdf":
                return gerar_pdf_relatorio(self.template_type, data, self.name)
        except Exception:
            pass
        try:
            from ser_pleno.application.services._export_helpers import format_date_for_export
            import csv, io
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow([self.name, format_date_for_export(datetime.now())])
            for key, value in (data or {}).items():
                writer.writerow([str(key), str(value)])
            return buffer.getvalue().encode("utf-8")
        except Exception:
            return b""


@dataclass
class Report:
    id: int
    student_id: int
    type: str
    generated_at: datetime = field(default_factory=datetime.now)
    download_path: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    template_id: int | None = None

    def render_template(self) -> str:
        if self.template_id:
            try:
                from ser_pleno.infrastructure.db.query_helpers import fetch_one
                row = fetch_one(
                    "SELECT content, sections, filters FROM report_template WHERE id = %s",
                    (self.template_id,),
                )
                if row:
                    template = ReportTemplate(
                        id=self.template_id,
                        name=self.type,
                        template_type=self.type,
                        content=row.get("content", ""),
                        sections=row.get("sections", []),
                        filters=row.get("filters", {}),
                    )
                    return template.render_template(self.data)
            except Exception:
                pass
        return str(self.data)

    def export_to_format(self, format_type: str) -> bytes:
        try:
            from ser_pleno.application.services.pdf import gerar_pdf_relatorio
            if format_type == "pdf":
                return gerar_pdf_relatorio(self.type, self.data, f"Relatorio_{self.id}")
        except Exception:
            pass
        try:
            import json
            return json.dumps(self.data, ensure_ascii=False, default=str).encode("utf-8")
        except Exception:
            return b""
