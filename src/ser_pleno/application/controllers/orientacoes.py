# -*- coding: utf-8 -*-
"""Controller de Orientações — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.orientacoes import ServicoOrientacoes


class OrientacoesController(BaseController):
    """Coordena as requisições da View de Orientações."""

    def __init__(self, auth_service=None):
        super().__init__(ServicoOrientacoes, auth_service=auth_service)

    def get_service(self):
        return self._service

    def listar_orientacoes(self, id_estudante=None, tema=None, pagina=1, date_from=None, date_to=None, search=None):
        """Lista orientações com filtros opcionais."""
        return self._service.listar_orientacoes(id_estudante, tema, pagina, date_from, date_to, search)

    def obter_orientacao(self, id_orientacao):
        """Obtém detalhes de uma orientação específica."""
        return self._service.obter_orientacao(id_orientacao)

    def criar_orientacao(self, dados, arquivos=None):
        """Cria uma nova orientação."""
        return self._service.criar_orientacao(dados, arquivos)

    def atualizar_orientacao(self, id_orientacao, dados, arquivos=None):
        """Atualiza uma orientação existente."""
        return self._service.atualizar_orientacao(id_orientacao, dados, arquivos)

    def deletar_orientacao(self, id_orientacao):
        """Deleta uma orientação."""
        return self._service.deletar_orientacao(id_orientacao)

    def get_preset(self, chave):
        """Retorna um preset específico."""
        return self._service.get_preset(chave)

    def get_presets(self):
        """Retorna todos os presets disponíveis."""
        return self._service.get_presets()

    def duplicar_orientacao(self, id_orientacao, id_estudante=None):
        """Duplica uma orientação existente."""
        return self._service.duplicar_orientacao(id_orientacao, id_estudante)

    def obter_estatisticas(self, id_estudante=None):
        """Obtém estatísticas das orientações."""
        return self._service.obter_estatisticas(id_estudante)

    def listar_estudantes(self):
        """Lista todos os estudantes cadastrados."""
        return self._service.listar_estudantes()

    def listar_anexos(self, orientation_id):
        """Lista anexos de uma orientação."""
        return self._service.listar_anexos(orientation_id)

    def adicionar_anexo(self, orientation_id, arquivo_path, uploaded_by_id):
        """Adiciona um anexo a uma orientação."""
        return self._service.adicionar_anexo(orientation_id, arquivo_path, uploaded_by_id)

    def deletar_anexo(self, attachment_id):
        """Deleta um anexo."""
        return self._service.deletar_anexo(attachment_id)
