from __future__ import annotations

from typing import Optional

from ser_pleno.features.relatorio.repo import RelatorioRepository


class ServicoRelatorio:
    def __init__(self, auth_service=None):
        self.repo = RelatorioRepository()
    
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1, search=None, data_fim=None):
        """Lista relatórios com filtros opcionais."""
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
        """Lista relatórios filtrados sem paginação (para previews/templates)."""
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
        """Obtém detalhes de um relatório."""
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": row}
        return {"success": False, "message": "Relatório não encontrado"}

    def obter_estatisticas(self, periodo='month'):
        """Obtém estatísticas básicas do sistema."""
        stats = self.repo.obter_estatisticas()
        return {"success": True, "data": stats}

    def obter_comparacao_estatisticas(self, periodo_inicio, periodo_fim):
        """Obtém comparação de estatísticas entre dois períodos."""
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
        """Gera um novo relatório."""
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
        """Obtém o caminho de um relatório para download."""
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row['file_path']}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_pdf(self, id_relatorio):
        """Download do relatório em PDF."""
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "pdf"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_excel(self, id_relatorio):
        """Download do relatório em Excel."""
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "excel"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_csv(self, id_relatorio):
        """Download do relatório em CSV."""
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "csv"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def baixar_json(self, id_relatorio):
        """Download do relatório em JSON."""
        row = self.repo.obter_relatorio_por_id(id_relatorio)
        if row:
            return {"success": True, "data": {"file_path": row.get('file_path'), "format": "json"}}
        return {"success": False, "message": "Relatório não encontrado"}

    def deletar_relatorio(self, id_relatorio):
        """Deleta um relatório."""
        self.repo.deletar_relatorio(id_relatorio)
        return {"success": True, "message": "Relatório deletado com sucesso"}

    def deletar_lote(self, ids_relatorios):
        """Deleta múltiplos relatórios."""
        for id_relatorio in ids_relatorios:
            self.repo.deletar_relatorio(id_relatorio)
        return {"success": True, "message": f"{len(ids_relatorios)} relatório(s) deletado(s)"}

    def baixar_lote(self, ids_relatorios):
        """Download de múltiplos relatórios."""
        file_paths = []
        for id_relatorio in ids_relatorios:
            row = self.repo.obter_relatorio_por_id(id_relatorio)
            if row and row.get('file_path'):
                file_paths.append(row['file_path'])
        return {"success": True, "data": {"file_paths": file_paths}}

    def exportar_estudantes(self):
        """Exporta todos os estudantes."""
        rows = self.repo.exportar_estudantes()
        return {"success": True, "data": list(rows)}

    def exportar_agendamentos(self):
        """Exporta todos os agendamentos."""
        rows = self.repo.exportar_agendamentos()
        return {"success": True, "data": list(rows)}

    def exportar_triagens(self):
        """Exporta todas as triagens."""
        rows = self.repo.exportar_triagens()
        return {"success": True, "data": list(rows)}

    def exportar_intervencoes(self):
        """Exporta todas as intervenções."""
        rows = self.repo.exportar_intervencoes() if hasattr(self.repo, 'exportar_intervencoes') else []
        return {"success": True, "data": list(rows)}

    def gerar_relatorio_por_template(self, id_template: int, parametros: Optional[dict] = None) -> dict:
        """Gera relatório baseado em um template pré-definido."""
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
        """Gera dados brutos para um tipo de relatório."""
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
