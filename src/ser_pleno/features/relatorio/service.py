from __future__ import annotations

import csv
import io
import json
import logging
import os
import zipfile
from typing import Any, Dict, List, Optional

from ser_pleno.features.relatorio.repo import RelatorioRepository
from ser_pleno.infrastructure.api.api import ClienteAPI

logger = logging.getLogger(__name__)


class ServicoRelatorio:
    def __init__(self, auth_service=None):
        self.repo = RelatorioRepository()
        self._auth_service = auth_service
        self._api = ClienteAPI(auth_service=auth_service)
        self._operation_config = None

    def _get_operation_config(self):
        if self._operation_config is None:
            try:
                from ser_pleno.config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config

    def _should_use_api(self) -> bool:
        config = self._get_operation_config()
        if config is None:
            return True
        return config.should_use_api()

    def _get_session(self):
        auth = self._auth_service
        if auth and hasattr(auth, "get_session"):
            return auth.get_session()
        try:
            import requests
            return requests
        except Exception:
            return None

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        auth = self._auth_service
        if auth:
            if hasattr(auth, "get_headers"):
                return auth.get_headers()
            if hasattr(auth, "csrf_token") and auth.csrf_token:
                headers["X-CSRFToken"] = auth.csrf_token
        return headers

    def _obter_dados_api(self, endpoint: str, filtros: Optional[dict] = None):
        if not self._should_use_api():
            return None
        try:
            params: Dict[str, Any] = {}
            if filtros:
                for k, v in filtros.items():
                    if v is not None and v != "":
                        params[k] = v

            session = self._get_session()
            if not session:
                return None
            url = f"{self._api.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = session.get(url, params=params, headers=self._get_headers(), timeout=10)
            if response.ok:
                data = response.json()
                if data.get("success") is not False:
                    return data.get("data")
        except Exception:
            pass
        return None

    def _aplicar_filtros(self, rows: list, filtros: Optional[dict], campo_data: str, campo_tipo: str) -> list:
        filtros = filtros or {}
        resultado = []
        for r in rows:
            data_val = r.get(campo_data) or ""
            tipo_val = r.get(campo_tipo) or ""
            if filtros.get("date_from") and data_val < filtros["date_from"]:
                continue
            if filtros.get("date_to") and data_val > filtros["date_to"]:
                continue
            if filtros.get("tipo") and tipo_val != filtros["tipo"]:
                continue
            resultado.append(r)
        return resultado

    def _formatar_csv(self, dados: list, campos: list) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        for linha in dados:
            linha_fmt = {c: linha.get(c, "") for c in campos}
            for k, v in linha_fmt.items():
                if isinstance(v, (dict, list)):
                    linha_fmt[k] = json.dumps(v, ensure_ascii=False)
            writer.writerow(linha_fmt)
        return output.getvalue()

    def _formatar_json(self, dados: list) -> str:
        return json.dumps(dados, ensure_ascii=False, indent=2)

    def _coluna(self, indice: int) -> str:
        resultado = ""
        while indice > 0:
            indice, resto = divmod(indice - 1, 26)
            resultado = chr(65 + resto) + resultado
        return resultado

    def _formatar_excel(self, dados: list, campos: list, nome_planilha: str = "Planilha") -> bytes:
        def xml_escape(s):
            return str(s).replace("&", "&").replace("<", "<").replace(">", ">")

        strings = []
        string_index = {}

        def get_string_index(s):
            s = str(s) if s is not None else ""
            if s not in string_index:
                string_index[s] = len(strings)
                strings.append(s)
            return string_index[s]

        ss_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        ss_parts.append('<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{}" uniqueCount="{}">'.format(len(strings), len(strings)))
        for s in strings:
            ss_parts.append('<si><t>{}</t></si>'.format(xml_escape(s)))
        ss_parts.append('</sst>')
        ss_xml = "\n".join(ss_parts)

        sheet_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        sheet_parts.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
        sheet_parts.append('<sheetData>')

        sheet_parts.append('<row r="1">')
        for i, campo in enumerate(campos, 1):
            idx = get_string_index(campo)
            sheet_parts.append('<c r="{}" t="s"><v>{}</v></c>'.format(self._coluna(i) + "1", idx))
        sheet_parts.append('</row>')

        for row_idx, linha in enumerate(dados, 2):
            sheet_parts.append('<row r="{}">'.format(row_idx))
            for i, campo in enumerate(campos, 1):
                valor = linha.get(campo, "")
                if isinstance(valor, (dict, list)):
                    valor = json.dumps(valor, ensure_ascii=False)
                idx = get_string_index(valor)
                sheet_parts.append('<c r="{}" t="s"><v>{}</v></c>'.format(self._coluna(i) + str(row_idx), idx))
            sheet_parts.append('</row>')

        sheet_parts.append('</sheetData>')
        sheet_parts.append('</worksheet>')
        sheet_xml = "\n".join(sheet_parts)

        workbook_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        workbook_parts.append('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')
        workbook_parts.append('<sheets>')
        workbook_parts.append('<sheet name="{}" sheetId="1" r:id="rId1"/>'.format(xml_escape(nome_planilha)))
        workbook_parts.append('</sheets>')
        workbook_parts.append('</workbook>')
        workbook_xml = "\n".join(workbook_parts)

        rels_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        rels_parts.append('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">')
        rels_parts.append('<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>')
        rels_parts.append('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>')
        rels_parts.append('</Relationships>')
        rels_xml = "\n".join(rels_parts)

        root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n</Relationships>'

        content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n<Default Extension="xml" ContentType="application/xml"/>\n<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>\n<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>\n<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>\n</Types>'

        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", root_rels)
            zf.writestr("xl/workbook.xml", workbook_xml)
            zf.writestr("xl/_rels/workbook.xml.rels", rels_xml)
            zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
            zf.writestr("xl/sharedStrings.xml", ss_xml)

        return output.getvalue()

    def _processar_exportacao(self, dados: list, formato: str, entidade: str, campos: list, nome_arquivo: str) -> dict:
        ext_map = {"csv": ".csv", "excel": ".xlsx", "json": ".json"}
        if not dados:
            vazio = "" if formato != "excel" else b""
            return {"success": True, "data": {"content": vazio, "format": formato, "filename": nome_arquivo, "mime_type": self._mime_type(formato)}}

        if formato == "csv":
            content = self._formatar_csv(dados, campos)
        elif formato == "json":
            content = self._formatar_json(dados)
        elif formato == "excel":
            content = self._formatar_excel(dados, campos, entidade.capitalize())
        else:
            content = self._formatar_csv(dados, campos)

        return {
            "success": True,
            "data": {
                "content": content,
                "format": formato,
                "filename": nome_arquivo,
                "mime_type": self._mime_type(formato),
            }
        }

    def _mime_type(self, formato: str) -> str:
        return {"csv": "text/csv", "json": "application/json", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}.get(formato, "application/octet-stream")

    def exportar_estudantes(self, filtros=None, formato="csv"):
        api_data = self._obter_dados_api("export/students/", filtros)
        if api_data is not None:
            campos = ["id", "nome", "email", "curso", "age", "phone", "professor_responsavel", "status", "priority_level", "updated_at"]
            nome_arquivo = "estudantes_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
            return self._processar_exportacao(api_data, formato, "estudantes", campos, nome_arquivo)

        rows = self.repo.exportar_estudantes()
        data = self._aplicar_filtros(rows, filtros, "updated_at", "status")
        campos = ["id", "nome", "email", "curso", "age", "phone", "professor_responsavel", "status", "priority_level", "updated_at"]
        nome_arquivo = "estudantes_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
        return self._processar_exportacao(data, formato, "estudantes", campos, nome_arquivo)

    def exportar_agendamentos(self, filtros=None, formato="csv"):
        api_data = self._obter_dados_api("export/appointments/", filtros)
        if api_data is not None:
            campos = ["id", "nome", "id_aluno", "data_hora", "motivo", "status", "local", "profissional", "origem", "updated_at"]
            nome_arquivo = "agendamentos_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
            return self._processar_exportacao(api_data, formato, "agendamentos", campos, nome_arquivo)

        rows = self.repo.exportar_agendamentos()
        data = self._aplicar_filtros(rows, filtros, "data_hora", "status")
        campos = ["id", "nome", "id_aluno", "data_hora", "motivo", "status", "local", "profissional", "origem", "updated_at"]
        nome_arquivo = "agendamentos_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
        return self._processar_exportacao(data, formato, "agendamentos", campos, nome_arquivo)

    def exportar_triagens(self, filtros=None, formato="csv"):
        api_data = self._obter_dados_api("export/screenings/", filtros)
        if api_data is not None:
            campos = ["id", "student_id", "form_id", "status", "priority", "scheduled_date", "observations", "recommendations", "requires_followup", "followup_date", "updated_at"]
            nome_arquivo = "triagens_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
            return self._processar_exportacao(api_data, formato, "triagens", campos, nome_arquivo)

        rows = self.repo.exportar_triagens()
        data = self._aplicar_filtros(rows, filtros, "created_at", "status")
        campos = ["id", "student_id", "form_id", "status", "priority", "scheduled_date", "observations", "recommendations", "requires_followup", "followup_date", "updated_at"]
        nome_arquivo = "triagens_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
        return self._processar_exportacao(data, formato, "triagens", campos, nome_arquivo)

    def exportar_intervencoes(self, filtros=None, formato="csv"):
        api_data = self._obter_dados_api("export/interventions/", filtros)
        if api_data is not None:
            campos = ["id", "student_id", "date", "intervention_type", "duration_minutes", "intervention_notes", "outcome", "follow_up_required", "follow_up_date", "updated_at"]
            nome_arquivo = "intervencoes_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
            return self._processar_exportacao(api_data, formato, "intervencoes", campos, nome_arquivo)

        rows = self.repo.exportar_intervencoes() if hasattr(self.repo, 'exportar_intervencoes') else []
        data = self._aplicar_filtros(rows, filtros, "date", "intervention_type")
        campos = ["id", "student_id", "date", "intervention_type", "duration_minutes", "intervention_notes", "outcome", "follow_up_required", "follow_up_date", "updated_at"]
        nome_arquivo = "intervencoes_{}.{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d"), {"csv": "csv", "excel": "xlsx", "json": "json"}.get(formato, "csv"))
        return self._processar_exportacao(data, formato, "intervencoes", campos, nome_arquivo)

    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1, search=None, data_fim=None):
        rows = self.repo.listar_relatorios(tipo, data_inicio, pagina, search, data_fim)
        relatorios = []
        for r in rows:
            relatorios.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'report_type': r.get('report_type'),
                'format': r.get('format'),
                'generated_at': str(r.get('generated_at')),
                'file_path': r.get('file_path'),
                'file_size': r.get('file_size'),
                'is_public': bool(r.get('is_public')),
                'expires_at': str(r.get('expires_at')) if r.get('expires_at') else None
            })
        return {"success": True, "data": relatorios}

    def listar_relatorios_filtrados(self, tipo=None, data_inicio=None, data_fim=None, search=None, pagina=1):
        rows = self.repo.listar_relatorios_filtrados(tipo, data_inicio, data_fim, search, pagina)
        relatorios = []
        for r in rows:
            relatorios.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'report_type': r.get('report_type'),
                'format': r.get('format'),
                'generated_at': str(r.get('generated_at')),
                'file_path': r.get('file_path'),
                'file_size': r.get('file_size'),
                'is_public': bool(r.get('is_public')),
                'expires_at': str(r.get('expires_at')) if r.get('expires_at') else None
            })
        return {"success": True, "data": relatorios}

    def obter_relatorio(self, id_relatorio):
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": row}
        return {"success": False, "message": "Relatório não encontrado"}

    def obter_estatisticas(self, periodo='month'):
        api_data = self._obter_dados_api("reports/stats/")
        if api_data is not None:
            return {"success": True, "data": api_data}
        stats = self.repo.obter_estatisticas()
        return {"success": True, "data": stats}

    def obter_comparacao_estatisticas(self, periodo_inicio, periodo_fim):
        params = {
            "period_inicio_0": periodo_inicio[0],
            "period_inicio_1": periodo_inicio[1],
            "period_fim_0": periodo_fim[0],
            "period_fim_1": periodo_fim[1],
        }
        api_data = self._obter_dados_api("reports/stats/comparison/", filtros=params)
        if api_data is not None:
            return {"success": True, "data": api_data}
        stats_inicio = self.repo.obter_estatisticas()
        stats_fim = self.repo.obter_estatisticas()
        return {
            "success": True,
            "data": {
                "periodo_inicio": {"periodo": periodo_inicio, "stats": stats_inicio},
                "periodo_fim": {"periodo": periodo_fim, "stats": stats_fim},
            }
        }

    def gerar_relatorio(self, dados):
        relatorio_id = self.repo.criar_relatorio(
            name=dados['name'],
            report_type=dados['report_type'],
            format=dados.get('format', 'pdf'),
            parameters=dados.get('parameters', '{}'),
            data=dados.get('data', '{}'),
            file_path=dados.get('file_path', ''),
            file_size=dados.get('file_size', 0),
            is_public=dados.get('is_public', False),
            expires_at=dados.get('expires_at'),
            generated_by_id=dados.get('generated_by_id')
        )
        return {"success": True, "data": {"id": relatorio_id}}

    def baixar_relatorio(self, id_relatorio):
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row['file_path']}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_pdf(self, id_relatorio):
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "pdf"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_excel(self, id_relatorio):
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "excel"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_csv(self, id_relatorio):
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "csv"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_json(self, id_relatorio):
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "json"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def deletar_relatorio(self, id_relatorio):
        self.repo.deletar_relatorio(id_relatorio)
        return {"success": True, "message": "Relatório deletado com sucesso"}

    def deletar_lote(self, ids_relatorios):
        if self._should_use_api() and ids_relatorios:
            try:
                payload = {"report_ids": ids_relatorios}
                resp = self._api.post("reports/bulk/delete/", json=payload)
                if resp and resp.get("success") is not False:
                    return resp
            except Exception:
                pass
        for id_relatorio in ids_relatorios:
            self.repo.deletar_relatorio(id_relatorio)
        return {"success": True, "message": f"{len(ids_relatorios)} relatório(s) deletado(s)"}

    def baixar_lote(self, ids_relatorios):
        if self._should_use_api() and ids_relatorios:
            try:
                payload = {"report_ids": ids_relatorios}
                resp = self._api.post("reports/bulk/download/", json=payload)
                if resp and resp.get("success") is not False:
                    return resp
            except Exception:
                pass
        file_paths = []
        for id_relatorio in ids_relatorios:
            row = self.repo.obter_relatorio_por_id(id_relatorio)
            if row and row.get('file_path'):
                file_paths.append(row['file_path'])
        return {"success": True, "data": {"file_paths": file_paths}}

    def gerar_relatorio_por_template(self, id_template: int, parametros: Optional[dict] = None) -> dict:
        from ser_pleno.features.report_template.service import ServicoReportTemplate
        template_service = ServicoReportTemplate()
        template_res = template_service.aplicar_template_em_dados(id_template, parametros)
        if not template_res.get("success"):
            return template_res

        template_data = template_res.get("data", {})
        nome = template_data.get("name", "Relatório")
        report_type = template_data.get("report_type", "geral")
        params = template_data.get("parameters", {})

        report_data = self._gerar_dados_relatorio(report_type, params)
        if isinstance(report_data, dict) and "error" in report_data:
            return {"success": False, "message": report_data["error"]}

        file_path = ""
        file_size = 0
        format_type = params.get("format", "pdf")
        try:
            if format_type == "pdf":
                from ser_pleno.application.services.pdf import gerar_pdf_relatorio
                pdf_bytes = gerar_pdf_relatorio(report_type=report_type, report_data=report_data, report_name=nome)
                if pdf_bytes:
                    import os, tempfile
                    file_path = os.path.join(tempfile.gettempdir(), f"{nome.replace(' ', '_')}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(pdf_bytes)
                    file_size = len(pdf_bytes)
        except Exception:
            pass

        relatorio_id = self.repo.criar_relatorio(
            name=nome,
            report_type=report_type,
            format=format_type,
            parameters=str(params),
            data=str(report_data),
            file_path=file_path,
            file_size=file_size,
            is_public=False,
            expires_at=None,
            generated_by_id=1,
        )
        return {
            "success": True,
            "data": {
                "id": relatorio_id,
                "name": nome,
                "type": report_type,
                "format": format_type,
                "generated_at": __import__("datetime").datetime.now().isoformat(),
                "file_path": file_path,
            }
        }

    def _gerar_dados_relatorio(self, report_type: str, parameters: dict) -> dict:
        from datetime import date, timedelta
        today = date.today()

        if report_type == "geral":
            stats = self.repo.obter_estatisticas()
            return {
                "summary": stats,
                "generated_at": today.isoformat(),
            }

        if report_type == "estudante":
            student_id = parameters.get("student_id")
            if not student_id:
                return {"error": "student_id é obrigatório"}
            rows = self.repo.exportar_estudantes()
            student_rows = [r for r in rows if r.get("id") == student_id]
            if not student_rows:
                return {"error": "Estudante não encontrado"}
            student = student_rows[0]
            return {
                "student": student,
                "appointments_count": 0,
                "interventions_count": 0,
                "screenings_count": 0,
                "generated_at": today.isoformat(),
            }

        if report_type == "agendamentos":
            date_from = parameters.get("date_from", (today - timedelta(days=30)).isoformat())
            date_to = parameters.get("date_to", today.isoformat())
            rows = self.repo.exportar_agendamentos()
            filtered = [r for r in rows if date_from <= (r.get("data_hora") or "") <= date_to]
            return {
                "period": {"from": date_from, "to": date_to},
                "total": len(filtered),
                "appointments": filtered[:100],
                "generated_at": today.isoformat(),
            }

        if report_type == "triagens":
            date_from = parameters.get("date_from", (today - timedelta(days=30)).isoformat())
            date_to = parameters.get("date_to", today.isoformat())
            rows = self.repo.exportar_triagens()
            filtered = [r for r in rows if date_from <= (r.get("created_at") or "") <= date_to]
            return {
                "period": {"from": date_from, "to": date_to},
                "total": len(filtered),
                "screenings": filtered[:100],
                "generated_at": today.isoformat(),
            }

        if report_type == "intervencoes":
            date_from = parameters.get("date_from", (today - timedelta(days=30)).isoformat())
            date_to = parameters.get("date_to", today.isoformat())
            rows = self.repo.exportar_intervencoes() if hasattr(self.repo, 'exportar_intervencoes') else []
            filtered = [r for r in rows if date_from <= (r.get("date") or "") <= date_to]
            return {
                "period": {"from": date_from, "to": date_to},
                "total": len(filtered),
                "interventions": filtered[:100],
                "generated_at": today.isoformat(),
            }

        if report_type == "estatisticas":
            stats = self.repo.obter_estatisticas()
            return {
                "summary": stats,
                "generated_at": today.isoformat(),
            }

        return {"error": f"Tipo de relatório não suportado: {report_type}"}
