# -*- coding: utf-8 -*-
"""Controller de Agenda — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.agendamentos import ServicoAgendamento


class AgendaController(BaseController):
    """Coordena as requisições da View de Agenda."""

    def __init__(self):
        super().__init__(ServicoAgendamento)

    def get_service(self):
        return self._service

    def listar_agendamentos(self, data=None):
        """Lista agendamentos com filtro opcional por data."""
        return self._service.listar_agendamentos(data)

    def listar_estudantes(self):
        """Lista estudantes para composição dos selects da agenda."""
        return self._service.listar_estudantes()

    def listar_horarios_base(self):
        """Lista horários ativos da grade."""
        return self._service.listar_horarios_base()

    def criar_agendamento(self, dados):
        """Cria um novo agendamento."""
        return self._service.criar_agendamento(dados)

    def atualizar_agendamento(self, id_agendamento, dados):
        """Atualiza um agendamento existente."""
        return self._service.atualizar_agendamento(id_agendamento, dados)

    def deletar_agendamento(self, id_agendamento):
        """Deleta um agendamento."""
        return self._service.deletar_agendamento(id_agendamento)

    def verificar_disponibilidade(self, data, time_str):
        """Verifica se um horário está disponível."""
        return self._service.verificar_disponibilidade(data, time_str)

    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horário de disponibilidade."""
        return self._service.adicionar_horario_disponibilidade(horario)

    def remover_horario_disponibilidade(self, horario):
        """Remove um horário de disponibilidade."""
        return self._service.remover_horario_disponibilidade(horario)
