from ser_pleno.repositories.relatorios import RelatorioRepository


class ServicoRelatorio:
    def __init__(self, auth_service=None):
        self.repo = RelatorioRepository()
    
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1):
        """Lista relatórios com filtros opcionais."""
        rows = self.repo.listar_relatorios(tipo, data_inicio, pagina)
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

    def obter_estatisticas(self, periodo='month'):
        """Obtém estatísticas básicas do sistema."""
        stats = self.repo.obter_estatisticas()
        return {"success": True, "data": stats}

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

    def deletar_relatorio(self, id_relatorio):
        """Deleta um relatório."""
        self.repo.deletar_relatorio(id_relatorio)
        return {"success": True, "message": "Relatório deletado com sucesso"}

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
