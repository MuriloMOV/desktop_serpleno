# -*- coding: utf-8 -*-
"""Repositório de comunicação."""

from ser_pleno.repositories.base import fetch_all, fetch_one, execute_non_query


class ComunicacaoRepository:
    def listar_alertas(self):
        return fetch_all("SELECT * FROM desktop_alert ORDER BY created_at DESC")

    def marcar_alerta_lido(self, id_alerta):
        return execute_non_query("UPDATE desktop_alert SET is_read = 1 WHERE id = %s", (id_alerta,))

    def marcar_todos_lidos(self):
        return execute_non_query("UPDATE desktop_alert SET is_read = 1 WHERE is_read = 0")

    def listar_pedidos_ajuda(self):
        return fetch_all("SELECT * FROM help_requests ORDER BY created_at DESC")

    def listar_contatos(self, id_usuario_logado=None):
        query = """
            SELECT u.id, u.first_name, u.last_name, u.username, u.email, a.nome AS student_name,
                   u.is_superuser, u.is_staff,
                   CASE
                       WHEN u.is_superuser THEN 'admin'
                       WHEN EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name = 'Gestores') THEN 'coordenador'
                       WHEN EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name = 'Profissionais') THEN 'analista'
                       WHEN EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name = 'Suporte') THEN 'suporte'
                       WHEN u.is_staff THEN 'analista'
                       ELSE 'aluno'
                   END AS role
            FROM auth_user u
            LEFT JOIN aluno a ON u.id = a.user_id
            WHERE
                u.is_superuser = 1 OR
                EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name IN ('Gestores', 'Profissionais', 'Suporte')) OR
                u.is_staff = 1
            ORDER BY u.first_name ASC
        """
        return fetch_all(query)

    def obter_mensagens(self, usuario_id: int, conversa_id: int):
        query = """
            SELECT * FROM desktop_message
            WHERE sender_id = %s AND recipient_id = %s
               OR sender_id = %s AND recipient_id = %s
            ORDER BY timestamp ASC
        """
        return fetch_all(query, (usuario_id, conversa_id, conversa_id, usuario_id))

    def enviar_mensagem(self, usuario_id: int, destinatario_id: int, texto: str):
        query = """
            INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`)
            VALUES (%s, %s, %s, NOW(), 0)
        """
        return execute_non_query(query, (usuario_id, destinatario_id, texto))

    def obter_mensagens_grupo(self):
        query = "SELECT * FROM desktop_message WHERE recipient_id IS NULL ORDER BY timestamp ASC"
        return fetch_all(query)

    def enviar_mensagem_grupo_texto(self, usuario_id: int, texto: str):
        query = """
            INSERT INTO desktop_message (sender_id, text, timestamp, `read`, recipient_id)
            VALUES (%s, %s, NOW(), 0, NULL)
        """
        return execute_non_query(query, (usuario_id, texto))

    def enviar_mensagem_grupo_arquivo(self, usuario_id: int, nome_arquivo: str, caminho: str, categoria: str):
        query = """
            INSERT INTO desktop_message (sender_id, text, timestamp, `read`, recipient_id, caminho_arquivo, tipo_arquivo)
            VALUES (%s, %s, NOW(), 0, NULL, %s, %s)
        """
        return execute_non_query(query, (usuario_id, nome_arquivo, caminho, categoria))

    def marcar_mensagem_lida(self, mensagem_id: int):
        query = "UPDATE desktop_message SET `read` = 1 WHERE id = %s"
        return execute_non_query(query, (mensagem_id,))

    def contar_mensagens_nao_lidas(self, usuario_id: int) -> int:
        query = "SELECT COUNT(*) as total FROM desktop_message WHERE recipient_id = %s AND `read` = 0"
        row = fetch_one(query, (usuario_id,))
        return row.get("total", 0) if row else 0

