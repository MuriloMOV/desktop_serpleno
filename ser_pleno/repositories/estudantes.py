# -*- coding: utf-8 -*-
"""Repositório de estudantes."""

from repositories.base import fetch_all, fetch_one, execute_non_query


class EstudanteRepository:
    def listar(self, busca=None, possui_laudo=None, requer_atencao=None):
        query = "SELECT a.*, u.email AS contact FROM aluno a LEFT JOIN auth_user u ON a.user_id = u.id WHERE 1=1"
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
        query = "SELECT a.*, u.email AS contact FROM aluno a LEFT JOIN auth_user u ON a.user_id = u.id WHERE a.id_aluno = %s"
        return fetch_one(query, (id_estudante,))

    def criar(self, nome, email, has_medical_report=False, requires_attention=False):
        query = "INSERT INTO aluno (nome, email, has_medical_report, requires_attention) VALUES (%s, %s, %s, %s)"
        return execute_non_query(query, (nome, email, has_medical_report, requires_attention))

    def atualizar(self, id_estudante, nome=None, email=None, has_medical_report=None, requires_attention=None):
        campos = []
        params = []
        if nome is not None:
            campos.append("nome = %s")
            params.append(nome)
        if email is not None:
            campos.append("email = %s")
            params.append(email)
        if has_medical_report is not None:
            campos.append("has_medical_report = %s")
            params.append(has_medical_report)
        if requires_attention is not None:
            campos.append("requires_attention = %s")
            params.append(requires_attention)
        if not campos:
            return 0
        query = f"UPDATE aluno SET {', '.join(campos)} WHERE id_aluno = %s"
        params.append(id_estudante)
        return execute_non_query(query, params)

    def deletar(self, id_estudante):
        query = "DELETE FROM aluno WHERE id_aluno = %s"
        return execute_non_query(query, (id_estudante,))
