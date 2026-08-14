# -*- coding: utf-8 -*-
"""Controller de Bem-Estar — mediação explícita entre View e Service."""

from ser_pleno.application.services.bem_estar import ServicoBemEstar
from ser_pleno.application.controllers.base import BaseController


class BemEstarController(BaseController):
    """Controller para a view de Bem-Estar."""

    def __init__(self):
        super().__init__(ServicoBemEstar)

    def obter_dashboard(self):
        return self._service.obter_dashboard()

    def listar_checkins(self):
        return self._service.listar_checkins()

    def listar_estudantes_risco(self):
        return self._service.listar_estudantes_risco()

    def listar_entradas_humor(self, student_id=None, date_from=None, date_to=None, mood_level=None):
        return self._service.listar_entradas_humor()

    def criar_entrada_humor(self, dados):
        return self._service.criar_entrada_humor(dados)

    def obter_medias_humor(self):
        return self._service.obter_medias_humor()

    def obter_humor_estudante(self, id_estudante):
        return self._service.obter_humor_estudante(id_estudante)

    def obter_historico_humor_estudante(self, id_estudante):
        return self._service.obter_historico_humor_estudante(id_estudante)

    def criar_checkin(self, dados):
        return self._service.criar_checkin(dados)

    def obter_checkin(self, checkin_id):
        return self._service.obter_checkin(checkin_id)

    def listar_desafios(self):
        return self._service.listar_desafios()

    def criar_desafio(self, dados):
        return self._service.criar_desafio(dados)

    def atualizar_desafio(self, challenge_id, dados):
        return self._service.atualizar_desafio(challenge_id, dados)

    def deletar_desafio(self, challenge_id):
        return self._service.deletar_desafio(challenge_id)

    def atribuir_desafio(self, dados):
        return self._service.atribuir_desafio(dados)

    def desatribuir_desafio(self, assignment_id):
        return self._service.desatribuir_desafio(assignment_id)

    def completar_desafio(self, assignment_id):
        return self._service.completar_desafio(assignment_id)

    def listar_desafios_estudante(self, student_id):
        return self._service.listar_desafios_estudante(student_id)

    def obter_dashboard_desafios(self):
        return self._service.obter_dashboard_desafios()

    def listar_estudantes(self, busca=None):
        from ser_pleno.application.controllers.estudantes import EstudantesController
        ctrl = EstudantesController()
        return ctrl.listar_estudantes(busca=busca)
