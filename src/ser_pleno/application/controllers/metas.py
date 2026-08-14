# -*- coding: utf-8 -*-
"""Controller de Metas — mediacao entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.metas import ServicoMetas


class MetasController(BaseController):
    """Coordena as requisicoes da View de Metas."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoMetas, auth_service=auth_service)
        self.app = app
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

    def get_service(self):
        return self._service

    def listar_metas(self, student_id=None, status=None, category=None, priority=None, pagina=1):
        """Lista metas com filtros opcionais."""
        return self._service.listar_metas(student_id, status, category, priority, pagina)

    def obter_meta(self, id_meta):
        """Obtém detalhes de uma meta específica."""
        return self._service.obter_meta(id_meta)

    def criar_meta(self, dados):
        """Cria uma nova meta."""
        return self._service.criar_meta(dados)

    def atualizar_meta(self, id_meta, dados):
        """Atualiza uma meta existente."""
        return self._service.atualizar_meta(id_meta, dados)

    def deletar_meta(self, id_meta):
        """Deleta uma meta."""
        return self._service.deletar_meta(id_meta)

    def registrar_progresso(self, id_meta, percentage, notes, recorded_by_id=None):
        """Registra progresso em uma meta."""
        if recorded_by_id is None:
            recorded_by_id = self.usuario_logado_id
        return self._service.registrar_progresso(id_meta, percentage, notes, recorded_by_id)

    def listar_progresso(self, id_meta):
        """Lista historico de progresso de uma meta."""
        return self._service.listar_progresso(id_meta)

    def listar_metas_atrasadas(self):
        """Lista metas atrasadas."""
        return self._service.listar_metas_atrasadas()

    def obter_estatisticas(self):
        """Obtém estatísticas das metas."""
        return self._service.obter_estatisticas()

    def listar_estudantes(self):
        """Lista estudantes para selecao."""
        return self._service.listar_estudantes()
