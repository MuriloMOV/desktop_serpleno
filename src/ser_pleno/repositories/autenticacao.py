# -*- coding: utf-8 -*-
"""Repositório de autenticação."""

from ser_pleno.repositories.base import (
    fetch_one,
    fetch_all,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)
from ser_pleno.infrastructure.api.sync_service import queue_sync
import logging

logger = logging.getLogger(__name__)


class AutenticacaoRepository:
    def obter_usuario_por_username(self, username):
        _local_rows = local_cache.list_all("auth_users", where_clause="username=?", params=(username,))
        if _local_rows:
            return _local_rows[0]
        try:
            query = "SELECT * FROM auth_user WHERE username = %s"
            return fetch_one(query, (username,))
        except Exception as exc:
            logger.debug("MySQL indisponivel para obter_usuario_por_username: %s", exc)
            return None

    def _local_obter_usuario_por_username(self, username):
        rows = local_cache.list_all("auth_users", where_clause="username=?", params=(username,))
        return rows[0] if rows else None

    def obter_usuario_por_id(self, user_id):
        _local_rows = local_cache.list_all("auth_users", where_clause="id=?", params=(user_id,))
        if _local_rows:
            return _local_rows[0]
        try:
            query = "SELECT * FROM auth_user WHERE id = %s"
            return fetch_one(query, (user_id,))
        except Exception as exc:
            logger.debug("MySQL indisponivel para obter_usuario_por_id: %s", exc)
            return None

    def _local_obter_usuario_por_id(self, user_id):
        rows = local_cache.list_all("auth_users", where_clause="id=?", params=(user_id,))
        return rows[0] if rows else None

    # AVISO: Este metodo retorna o hash da senha apenas para verificacao.
    # Nunca retorne o hash para a UI ou para qualquer camada externa.
    @with_local_fallback("_local_obter_hash_senha_para_verificacao")
    def obter_hash_senha_para_verificacao(self, user_id):
        _local_rows = local_cache.list_all("auth_users", where_clause="id=?", params=(user_id,))
        if _local_rows:
            return {"password": _local_rows[0].get("password", "")}
        try:
            query = "SELECT password FROM auth_user WHERE id = %s"
            return fetch_one(query, (user_id,))
        except Exception as exc:
            logger.debug("MySQL indisponivel para obter_hash_senha_para_verificacao: %s", exc)
            return None

    def _local_obter_hash_senha_para_verificacao(self, user_id):
        rows = local_cache.list_all("auth_users", where_clause="id=?", params=(user_id,))
        if rows:
            return {"password": rows[0].get("password")}
        return None

    @with_local_fallback("_local_atualizar_senha_usuario")
    def atualizar_senha_usuario(self, user_id, novo_hash):
        def _mysql():
            execute_non_query("UPDATE auth_user SET password = %s WHERE id = %s", (novo_hash, user_id))
            return 1

        def _local(mysql_result):
            user = local_cache.list_all("auth_users", where_clause="id=?", params=(user_id,))
            if user:
                local_cache.update("auth_users", {"password": novo_hash}, "id", user_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="auth_user", entity_id=user_id,
            queue_data_fn=lambda r, eid: {"id": user_id, "password": novo_hash},
        )

    def _local_atualizar_senha_usuario(self, user_id, novo_hash):
        user = local_cache.list_all("auth_users", where_clause="id=?", params=(user_id,))
        if user:
            local_cache.update("auth_users", {"password": novo_hash}, "id", user_id)
        return 1

    @with_local_fallback("_local_listar_usuarios")
    def listar_usuarios(self, busca=None, role=None, pagina=1):
        query = "SELECT * FROM auth_user WHERE 1=1"
        params = []
        if busca:
            query += " AND (username LIKE %s OR email LIKE %s OR first_name LIKE %s OR last_name LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%", f"%{busca}%"])
        if role:
            query += " AND id IN (SELECT user_id FROM user_profile WHERE role = %s)"
            params.append(role)
        offset = (pagina - 1) * 20
        query += " ORDER BY id ASC LIMIT 20 OFFSET %s"
        params.append(offset)
        return fetch_all(query, params)

    def _local_listar_usuarios(self, busca=None, role=None, pagina=1):
        rows = local_cache.list_all("auth_users")
        resultado = []
        for r in rows:
            if busca:
                termo = busca.lower()
                if termo not in (r.get("username") or "").lower() and termo not in (r.get("email") or "").lower():
                    continue
            if role:
                profiles = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(r.get("id"),))
                if not profiles or profiles[0].get("role") != role:
                    continue
            resultado.append(r)
        offset = (pagina - 1) * 20
        return resultado[offset:offset + 20]

    @with_local_fallback("_local_criar_usuario")
    def criar_usuario(self, username, email, password, first_name="", last_name="", role="visitante", is_staff=False):
        query = """
            INSERT INTO auth_user (username, email, password, first_name, last_name, is_staff, is_superuser, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        """
        params = (username, email, password, first_name, last_name, 1 if is_staff else 0, 0)

        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": 1 if is_staff else 0,
            "is_superuser": 0,
            "is_active": 1,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            user_data["id"] = last_id
            local_cache.upsert_auth_user(user_data)
            if role:
                profile_data = {
                    "user_id": last_id,
                    "role": role,
                    "is_active_profile": 1,
                }
                local_cache.upsert_user_profile(profile_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            user_data["id"] = last_id
            return user_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="auth_user", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        if role:
            profile_query = """
                INSERT INTO user_profile (user_id, role, is_active_profile)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE role = VALUES(role)
            """
            execute_non_query(profile_query, (last_id, role))
        queue_sync("create", "auth_user", last_id, {"id": last_id, "username": username, "email": email, "role": role})
        return last_id

    def _local_criar_usuario(self, username, email, password, first_name="", last_name="", role="visitante", is_staff=False):
        rows = local_cache.list_all("auth_users")
        max_id = 0
        for r in rows:
            if r.get("id") and r["id"] > max_id:
                max_id = r["id"]
        last_id = max_id + 1
        user_data = {
            "id": last_id,
            "username": username,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": 1 if is_staff else 0,
            "is_superuser": 0,
            "is_active": 1,
        }
        local_cache.upsert_auth_user(user_data)
        if role:
            profile_data = {
                "user_id": last_id,
                "role": role,
                "is_active_profile": 1,
            }
            local_cache.upsert_user_profile(profile_data)
        return last_id

    @with_local_fallback("_local_atualizar_usuario")
    def atualizar_usuario(self, user_id, email=None, first_name=None, last_name=None, role=None, is_staff=None):
        sets = []
        params = []
        if email is not None:
            sets.append("email = %s")
            params.append(email)
        if first_name is not None:
            sets.append("first_name = %s")
            params.append(first_name)
        if last_name is not None:
            sets.append("last_name = %s")
            params.append(last_name)
        if is_staff is not None:
            sets.append("is_staff = %s")
            params.append(1 if is_staff else 0)
        if not sets:
            return 0
        params.append(user_id)
        query = f"UPDATE auth_user SET {', '.join(sets)} WHERE id = %s"

        user_data = {}
        if email is not None:
            user_data["email"] = email
        if first_name is not None:
            user_data["first_name"] = first_name
        if last_name is not None:
            user_data["last_name"] = last_name
        if is_staff is not None:
            user_data["is_staff"] = 1 if is_staff else 0

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.update("auth_users", user_data, "id", user_id)
            if role is not None:
                profile = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(user_id,))
                if profile:
                    local_cache.update("user_profiles", {"role": role}, "user_id", user_id)
                else:
                    local_cache.upsert_user_profile({"user_id": user_id, "role": role, "is_active_profile": 1})
            return 1

        def _queue_data(mysql_result, entity_id):
            data = {"id": user_id}
            data.update(user_data)
            if role is not None:
                data["role"] = role
            return data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="auth_user", entity_id=user_id,
            queue_data_fn=_queue_data,
        )

    def _local_atualizar_usuario(self, user_id, email=None, first_name=None, last_name=None, role=None, is_staff=None):
        user_data = {}
        if email is not None:
            user_data["email"] = email
        if first_name is not None:
            user_data["first_name"] = first_name
        if last_name is not None:
            user_data["last_name"] = last_name
        if is_staff is not None:
            user_data["is_staff"] = 1 if is_staff else 0
        if user_data:
            local_cache.update("auth_users", user_data, "id", user_id)
        if role is not None:
            profile = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(user_id,))
            if profile:
                local_cache.update("user_profiles", {"role": role}, "user_id", user_id)
            else:
                local_cache.upsert_user_profile({"user_id": user_id, "role": role, "is_active_profile": 1})
        return 1

    @with_local_fallback("_local_deletar_usuario")
    def deletar_usuario(self, user_id):
        def _mysql():
            execute_non_query("DELETE FROM user_profile WHERE user_id = %s", (user_id,))
            execute_non_query("DELETE FROM auth_user WHERE id = %s", (user_id,))
            return 1

        def _local(mysql_result):
            local_cache.delete("user_profiles", "user_id", user_id)
            local_cache.delete("auth_users", "id", user_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="auth_user", entity_id=user_id,
            queue_data_fn=lambda r, eid: {"id": user_id},
        )

    def _local_deletar_usuario(self, user_id):
        local_cache.delete("user_profiles", "user_id", user_id)
        local_cache.delete("auth_users", "id", user_id)
        return 1

    @with_local_fallback("_local_conceder_permissao")
    def conceder_permissao(self, user_id, permissao):
        def _mysql():
            profile = fetch_one("SELECT * FROM user_profile WHERE user_id = %s", (user_id,))
            if not profile:
                raise ValueError("Perfil não encontrado")
            permissions = profile.get("permissions") or "[]"
            import json
            perms = json.loads(permissions) if isinstance(permissions, str) else permissions
            if permissao not in perms:
                perms.append(permissao)
            execute_non_query(
                "UPDATE user_profile SET permissions = %s WHERE user_id = %s",
                (json.dumps(perms), user_id),
            )
            return 1

        def _local(mysql_result):
            profile = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(user_id,))
            if not profile:
                raise ValueError("Perfil não encontrado")
            permissions = profile[0].get("permissions") or "[]"
            import json
            perms = json.loads(permissions) if isinstance(permissions, str) else permissions
            if isinstance(perms, str):
                perms = json.loads(perms)
            if permissao not in perms:
                perms.append(permissao)
            local_cache.update("user_profiles", {"permissions": json.dumps(perms)}, "user_id", user_id)
            return 1

        def _queue_data(mysql_result, entity_id):
            import json
            return {"user_id": user_id, "permissions": json.dumps([permissao])}

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="user_profile", entity_id=user_id,
            queue_data_fn=_queue_data,
        )

    def _local_conceder_permissao(self, user_id, permissao):
        profile = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(user_id,))
        if not profile:
            raise ValueError("Perfil não encontrado")
        permissions = profile[0].get("permissions") or "[]"
        import json
        perms = json.loads(permissions) if isinstance(permissions, str) else permissions
        if isinstance(perms, str):
            perms = json.loads(perms)
        if permissao not in perms:
            perms.append(permissao)
        local_cache.update("user_profiles", {"permissions": json.dumps(perms)}, "user_id", user_id)
        return 1

    @with_local_fallback("_local_revogar_permissao")
    def revogar_permissao(self, user_id, permissao):
        def _mysql():
            profile = fetch_one("SELECT * FROM user_profile WHERE user_id = %s", (user_id,))
            if not profile:
                raise ValueError("Perfil não encontrado")
            permissions = profile.get("permissions") or "[]"
            import json
            perms = json.loads(permissions) if isinstance(permissions, str) else permissions
            if isinstance(perms, str):
                perms = json.loads(perms)
            if permissao in perms:
                perms.remove(permissao)
            execute_non_query(
                "UPDATE user_profile SET permissions = %s WHERE user_id = %s",
                (json.dumps(perms), user_id),
            )
            return 1

        def _local(mysql_result):
            profile = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(user_id,))
            if not profile:
                raise ValueError("Perfil não encontrado")
            permissions = profile[0].get("permissions") or "[]"
            import json
            perms = json.loads(permissions) if isinstance(permissions, str) else permissions
            if isinstance(perms, str):
                perms = json.loads(perms)
            if permissao in perms:
                perms.remove(permissao)
            local_cache.update("user_profiles", {"permissions": json.dumps(perms)}, "user_id", user_id)
            return 1

        def _queue_data(mysql_result, entity_id):
            import json
            return {"user_id": user_id, "permissions": json.dumps([])}

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="user_profile", entity_id=user_id,
            queue_data_fn=_queue_data,
        )

    def _local_revogar_permissao(self, user_id, permissao):
        profile = local_cache.list_all("user_profiles", where_clause="user_id=?", params=(user_id,))
        if not profile:
            raise ValueError("Perfil não encontrado")
        permissions = profile[0].get("permissions") or "[]"
        import json
        perms = json.loads(permissions) if isinstance(permissions, str) else permissions
        if isinstance(perms, str):
            perms = json.loads(perms)
        if permissao in perms:
            perms.remove(permissao)
        local_cache.update("user_profiles", {"permissions": json.dumps(perms)}, "user_id", user_id)
        return 1
