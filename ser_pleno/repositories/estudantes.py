# -*- coding: utf-8 -*-
"""Repositório de estudantes."""

from repositories.base import fetch_all, fetch_one, execute_non_query


# Whitelist de colunas que podem ser atualizadas via DML.
# Qualquer campo fora desta lista é rejeitado antes de atingir o banco.
_CAMPOS_ATUALIZAVEIS = {
    "nome",
    "email",
    "has_medical_report",
    "requires_attention",
}


class EstudanteRepository:
    def listar(self, busca=None, possui_laudo=None, requer_atencao=None):
        query = (
            "SELECT a.*, u.email AS contact "
            "FROM aluno a "
            "LEFT JOIN auth_user u ON a.user_id = u.id "
            "WHERE 1=1"
        )
        params = []
        if busca:
            query += " AND (a.nome LIKE %s OR u.email LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        if possui_laudo is not None:
            query += " AND a.has_medical_report = %s"
            params.append(possui_laudo)
        if requer_atencao is not None:
            query += " AND a.requires_attention = %s"
            params.append(requer_atencao)
        query += " ORDER BY a.nome ASC"
        return fetch_all(query, params)

    def obter(self, id_estudante):
        query = (
            "SELECT a.*, u.email AS contact "
            "FROM aluno a "
            "LEFT JOIN auth_user u ON a.user_id = u.id "
            "WHERE a.id_aluno = %s"
        )
        return fetch_one(query, (id_estudante,))

    def criar(self, nome, email, has_medical_report=False, requires_attention=False):
        query = (
            "INSERT INTO aluno "
            "(nome, email, has_medical_report, requires_attention) "
            "VALUES (%s, %s, %s, %s)"
        )
        return execute_non_query(
            query,
            (nome, email, has_medical_report, requires_attention),
        )

    def atualizar(self, id_estudante, **dados):
        invalidos = set(dados) - _CAMPOS_ATUALIZAVEIS
        if invalidos:
            raise ValueError(
                f"Campos não permitidos para atualização: {sorted(invalidos)}"
            )

        if not dados:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in dados)
        params = list(dados.values()) + [id_estudante]
        query = f"UPDATE aluno SET {set_clause} WHERE id_aluno = %s"
        return execute_non_query(query, params)

    def deletar(self, id_estudante):
        query = "DELETE FROM aluno WHERE id_aluno = %s"
        return execute_non_query(query, (id_estudante,))
