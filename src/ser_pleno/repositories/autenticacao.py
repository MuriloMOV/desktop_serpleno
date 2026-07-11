# -*- coding: utf-8 -*-
"""Repositório de autenticação."""

from ser_pleno.repositories.base import (
    fetch_one,
    execute_non_query,
)
from ser_pleno.infrastructure.api.sync_service import queue_sync


class AutenticacaoRepository:
    def obter_usuario_por_username(self, username):
        """Obtém um usuário pelo username."""
        query = "SELECT * FROM auth_user WHERE username = %s"
        return fetch_one(query, (username,))

    def obter_usuario_por_id(self, user_id):
        """Obtém um usuário pelo ID."""
        query = "SELECT * FROM auth_user WHERE id = %s"
        return fetch_one(query, (user_id,))

    def obter_senha_usuario(self, user_id):
        """Obtém a senha hash de um usuário pelo ID."""
        query = "SELECT password FROM auth_user WHERE id = %s"
        return fetch_one(query, (user_id,))

    def atualizar_senha_usuario(self, user_id, novo_hash):
        """Atualiza a senha de um usuário."""
        query = "UPDATE auth_user SET password = %s WHERE id = %s"
        execute_non_query(query, (novo_hash, user_id))
        queue_sync("update", "auth_user", user_id, {"id": user_id, "password": novo_hash})
        return 1
