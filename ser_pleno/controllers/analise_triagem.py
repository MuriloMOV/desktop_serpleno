# -*- coding: utf-8 -*-
"""Controller de Análise de Triagem — mediação entre View e Services."""

from services.triagem import ServicoTriagem


class AnaliseTriagemController:
    """Coordena as requisições da View de Análise de Triagem."""

    def __init__(self, servico=None):
        self.servico = servico or ServicoTriagem()

    def listar_triagens(self):
        return self.servico.listar_triagens()

    def criar_triagem(self, dados):
        return self.servico.criar_triagem(dados)

    def atualizar_triagem(self, id_triagem, dados):
        return self.servico.atualizar_triagem(id_triagem, dados)

    def deletar_triagem(self, id_triagem):
        return self.servico.deletar_triagem(id_triagem)

    def obter_metricas(self):
        return self.servico.obter_metricas()

    def aplicar_filtros(self, status=None, prioridade=None):
        return self.servico.aplicar_filtros(status, prioridade)

    def limpar_filtros(self):
        return self.servico.limpar_filtros()
