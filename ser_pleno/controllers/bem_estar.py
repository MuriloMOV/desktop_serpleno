# -*- coding: utf-8 -*-
"""Controller de Bem-Estar — mediação entre View e Services."""

from services.bem_estar import ServicoBemEstar


class BemEstarController:
    """Coordena as requisições da View de Bem-Estar."""

    def __init__(self, servico=None):
        self.servico = servico or ServicoBemEstar()

    def obter_dashboard(self):
        return self.servico.obter_dashboard()

    def listar_entradas_humor(self):
        return self.servico.listar_entradas_humor()

    def obter_medias_humor(self):
        return self.servico.obter_medias_humor()

    def obter_humor_estudante(self, id_estudante):
        return self.servico.obter_humor_estudante(id_estudante)

    def listar_checkins(self):
        return self.servico.listar_checkins()

    def listar_estudantes_risco(self):
        return self.servico.listar_estudantes_risco()
