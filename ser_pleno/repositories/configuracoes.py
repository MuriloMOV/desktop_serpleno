# -*- coding: utf-8 -*-
"""Repositório de configurações."""

from repositories.base import fetch_all, execute_non_query


class ConfiguracoesRepository:
    def obter_configuracoes(self):
        return fetch_all("SELECT * FROM user_preferences")

    def atualizar_configuracoes(self, dados):
        query = "UPDATE user_preferences SET theme = %s, notifications = %s WHERE user_id = %s"
        return execute_non_query(query, (dados['theme'], dados['notifications'], dados['user_id']))
