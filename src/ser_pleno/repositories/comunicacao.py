# -*- coding: utf-8 -*-
"""Repositorio de comunicacao."""

from datetime import datetime

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)
from ser_pleno.infrastructure.api.sync_service import queue_sync


class ComunicacaoRepository:
    @with_local_fallback("_local_listar_alertas")
    def listar_alertas(self):
        return fetch_all("SELECT * FROM desktop_alert ORDER BY created_at DESC")

    def _local_listar_alertas(self):
        return local_cache.list_alerts()

    @with_local_fallback("_local_marcar_alerta_lido")
    def marcar_alerta_lido(self, id_alerta):
        def _mysql():
            execute_non_query(
                "UPDATE desktop_alert SET is_read = 1 WHERE id = %s",
                (id_alerta,),
            )
            return 1

        def _local(mysql_result):
            local_cache.update("alerts", {"is_read": 1}, "id", id_alerta)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="alerts", entity_id=id_alerta,
            queue_data_fn=lambda r, eid: {"id": id_alerta, "is_read": 1},
        )

    @with_local_fallback("_local_marcar_todos_lidos")
    def marcar_todos_lidos(self):
        def _mysql():
            count = execute_non_query("UPDATE desktop_alert SET is_read = 1 WHERE is_read = 0")
            return count if count else 1

        def _local(mysql_result):
            alerts = local_cache.list_all("alerts", where_clause="is_read=0")
            for alert in alerts:
                local_cache.update("alerts", {"is_read": 1}, "id", alert.get("id"))
            return len(alerts)

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="alerts", entity_id="bulk",
            queue_data_fn=lambda r, eid: None,
        )

    @with_local_fallback("_local_listar_pedidos_ajuda")
    def listar_pedidos_ajuda(self):
        return fetch_all("SELECT * FROM help_requests ORDER BY created_at DESC")

    def _local_listar_pedidos_ajuda(self):
        # Help requests nao sao sincronizados no cache local
        return []

    @with_local_fallback("_local_listar_contatos")
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

    def _local_listar_contatos(self, id_usuario_logado=None):
        # Contatos nao sao sincronizados no cache local
        return []

    @with_local_fallback("_local_obter_mensagens")
    def obter_mensagens(self, usuario_id: int, conversa_id: int):
        query = """
            SELECT * FROM desktop_message
            WHERE sender_id = %s AND recipient_id = %s
               OR sender_id = %s AND recipient_id = %s
            ORDER BY timestamp ASC
        """
        return fetch_all(query, (usuario_id, conversa_id, conversa_id, usuario_id))

    def _local_obter_mensagens(self, usuario_id: int, conversa_id: int):
        return local_cache.list_messages(sender_id=usuario_id, recipient_id=conversa_id)

    def enviar_mensagem(self, usuario_id: int, destinatario_id: int, texto: str):
        query = """
            INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo)
            VALUES (%s, %s, %s, NOW(), 0, NULL, NULL)
        """
        params = (usuario_id, destinatario_id, texto)
        message_data = {
            "sender_id": usuario_id,
            "recipient_id": destinatario_id,
            "text": texto,
            "timestamp": datetime.now().isoformat(),
            "read": 0,
            "caminho_arquivo": None,
            "tipo_arquivo": None,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            local_cache.upsert_message(message_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            return message_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="messages", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def enviar_mensagem_arquivo(self, usuario_id: int, destinatario_id: int, nome_arquivo: str, caminho: str, categoria: str):
        query = """
            INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo)
            VALUES (%s, %s, %s, NOW(), 0, %s, %s)
        """
        params = (usuario_id, destinatario_id, nome_arquivo, caminho, categoria)
        message_data = {
            "sender_id": usuario_id,
            "recipient_id": destinatario_id,
            "text": nome_arquivo,
            "timestamp": datetime.now().isoformat(),
            "read": 0,
            "caminho_arquivo": caminho,
            "tipo_arquivo": categoria,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            local_cache.upsert_message(message_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            return message_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="messages", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    @with_local_fallback("_local_obter_mensagens_grupo")
    def obter_mensagens_grupo(self):
        query = "SELECT * FROM desktop_message WHERE recipient_id IS NULL ORDER BY timestamp ASC"
        return fetch_all(query)

    def _local_obter_mensagens_grupo(self):
        return local_cache.list_group_messages()

    def enviar_mensagem_grupo_texto(self, usuario_id: int, texto: str):
        query = """
            INSERT INTO desktop_message (sender_id, text, timestamp, `read`, recipient_id)
            VALUES (%s, %s, NOW(), 0, NULL)
        """
        params = (usuario_id, texto)
        message_data = {
            "sender_id": usuario_id,
            "recipient_id": None,
            "text": texto,
            "timestamp": datetime.now().isoformat(),
            "read": 0,
            "caminho_arquivo": None,
            "tipo_arquivo": None,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            local_cache.upsert_message(message_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            return message_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="messages", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def enviar_mensagem_grupo_arquivo(self, usuario_id: int, nome_arquivo: str, caminho: str, categoria: str):
        query = """
            INSERT INTO desktop_message (sender_id, text, timestamp, `read`, recipient_id, caminho_arquivo, tipo_arquivo)
            VALUES (%s, %s, NOW(), 0, NULL, %s, %s)
        """
        params = (usuario_id, nome_arquivo, caminho, categoria)
        message_data = {
            "sender_id": usuario_id,
            "recipient_id": None,
            "text": nome_arquivo,
            "timestamp": datetime.now().isoformat(),
            "read": 0,
            "caminho_arquivo": caminho,
            "tipo_arquivo": categoria,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            local_cache.upsert_message(message_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            message_data["id"] = last_id
            return message_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="messages", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    @with_local_fallback("_local_marcar_mensagem_lida")
    def marcar_mensagem_lida(self, mensagem_id: int):
        def _mysql():
            execute_non_query("UPDATE desktop_message SET `read` = 1 WHERE id = %s", (mensagem_id,))
            return 1

        def _local(mysql_result):
            local_cache.update("messages", {"read": 1}, "id", mensagem_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="messages", entity_id=mensagem_id,
            queue_data_fn=lambda r, eid: {"id": mensagem_id, "read": 1},
        )

    @with_local_fallback("_local_contar_mensagens_nao_lidas")
    def contar_mensagens_nao_lidas(self, usuario_id: int) -> int:
        query = "SELECT COUNT(*) as total FROM desktop_message WHERE recipient_id = %s AND `read` = 0"
        row = fetch_one(query, (usuario_id,))
        return row.get("total", 0) if row else 0

    def _local_contar_mensagens_nao_lidas(self, usuario_id: int) -> int:
        rows = local_cache.list_all("messages", where_clause="recipient_id=? AND read=0", params=(usuario_id,))
        return len(rows)

    @with_local_fallback("_local_marcar_todas_mensagens_lidas")
    def marcar_todas_mensagens_lidas(self, usuario_id: int):
        def _mysql():
            return execute_non_query(
                "UPDATE desktop_message SET `read` = 1 WHERE recipient_id = %s AND `read` = 0",
                (usuario_id,),
            )

        def _local(mysql_result):
            messages = local_cache.list_all(
                "messages", where_clause="recipient_id=? AND read=0", params=(usuario_id,)
            )
            for msg in messages:
                local_cache.update("messages", {"read": 1}, "id", msg.get("id"))
            return len(messages)

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="messages", entity_id="bulk",
            queue_data_fn=lambda r, eid: None,
        )

    def excluir_mensagem(self, mensagem_id: int):
        def _mysql():
            return execute_non_query("DELETE FROM desktop_message WHERE id = %s", (mensagem_id,))

        def _local(mysql_result):
            local_cache.delete("messages", mensagem_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="messages", entity_id=mensagem_id,
            queue_data_fn=lambda r, eid: {"id": mensagem_id},
        )
