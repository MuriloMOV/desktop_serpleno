"""
Servico de Sincronizacao para o Desktop SerPleno

Fluxo principal:
- Online normal: MySQL é a fonte da verdade; SQLite e apenas cache local.
- MySQL indisponivel: repositories fazem fallback para SQLite e enfileiram operacoes.
- MySQL volta: apply da fila no MySQL (push) + pull de atualizacoes MySQL -> SQLite.
- API serpleno_web: sincronizacao complementar quando houver endpoint configurado.
"""
import logging
import json
import os
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

try:
    import requests
except Exception:
    requests = None  # type: ignore

from ser_pleno.config.db_config import get_db_connection
from ser_pleno.config.operation_mode import (
    OperationConfig, OperationMode, get_operation_config
)
from ser_pleno.infrastructure.local.local_cache import local_cache, _validate_identifier
from ser_pleno.repositories.base import is_local_id, execute_non_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


MYSQL_TABLE_WHITELIST = {
    "aluno",
    "agendamento",
    "desktop_orientation",
    "desktop_screening",
    "desktop_screeningform",
    "desktop_message",
    "desktop_report",
    "desktop_alert",
    "auth_user",
}


_QUEUE_ENTITY_PRIORITY = {
    "auth_user": 1,
    "students": 2,
    "messages": 3,
    "appointments": 4,
    "orientations": 5,
    "screenings": 6,
}


def validate_mysql_table_name(table: str) -> None:
    if table not in MYSQL_TABLE_WHITELIST:
        raise ValueError(
            f"Nome de tabela MySQL invalido: {table!r}. "
            f"Tabelas permitidas: {sorted(MYSQL_TABLE_WHITELIST)}"
        )


def _shorten_avatar(value: Any) -> str:
    if not value:
        return "a"
    text = str(value)
    if "/" in text or "\\" in text:
        text = text.replace("\\", "/").split("/")[-1]
    if not text:
        text = "avatar"
    if "." in text:
        text = text.split(".")[0]
    return text[:1]


class SyncQueue:
    """Fila de operacoes pendentes para sincronizacao — agora usando SQLite."""

    def add(self, operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
        """Adiciona operacao na fila."""
        local_cache.add_sync_queue(operation, entity, entity_id, data)
        logger.debug(f"Operacao adicionada na fila: {operation} {entity}#{entity_id}")

    def get_pending(self) -> List[Dict[str, Any]]:
        """Retorna itens pendentes."""
        return local_cache.list_all("sync_queue")

    def remove(self, item_id: str):
        """Remove item da fila."""
        local_cache.delete("sync_queue", "id", item_id)

    def increment_attempt(self, item_id: str):
        """Incrementa contador de tentativas."""
        items = local_cache.list_all("sync_queue", where_clause="id=?", params=(item_id,))
        if items:
            item = items[0]
            attempts = item.get("attempts", 0) + 1
            last_attempt = datetime.now().isoformat()
            local_cache.update_sync_queue_attempt(item_id, attempts, last_attempt)

    def clear_old(self, max_attempts: int = 5):
        """Remove itens antigos com muitas tentativas."""
        local_cache.clear_old_sync_queue(max_attempts)
        logger.info(f"Fila de sincronizacao limpa (max_attempts={max_attempts})")


class SyncService:
    """Servico de sincronizacao com serpleno_web"""

    SYNC_ENDPOINTS = {
        'students': '/api/v1/desktop/students/',
        'appointments': '/api/v1/desktop/schedule/appointments/',
        'orientations': '/api/v1/desktop/orientations/',
        'screenings': '/api/v1/desktop/screenings/',
        'messages': '/api/v1/desktop/messages/',
    }

    _instance: Optional['SyncService'] = None
    _lock = threading.RLock()
    _running: bool = False
    _thread: Optional[threading.Thread] = None
    _fk_warning_counts: Dict[str, int] = {}
    _fk_warning_reset: float = 0.0

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.config: OperationConfig = get_operation_config()
        self.queue: SyncQueue = SyncQueue()
        self._callbacks: Dict[str, List[Callable]] = {}
        self._session = requests.Session() if requests else None

    def check_api_availability(self) -> bool:
        """Verifica se a API do serpleno_web esta disponivel"""
        if not requests:
            return False

        try:
            url = f"{self.config.api_base_url}/api/v1/desktop/health/"
            response = self._session.get(url, timeout=self.config.api_timeout)
            available = response.status_code == 200
            self.config.set_api_available(available)
            return available
        except Exception as exc:
            logger.debug("API indisponivel: %s", exc)
            self.config.set_api_available(False)
            return False

    def check_mysql_availability(self) -> bool:
        """Verifica se o MySQL local esta disponivel."""
        try:
            conn = get_db_connection()
            conn.close()
            return True
        except Exception as exc:
            logger.debug("MySQL local indisponivel: %s", exc)
            return False

    def start_background_sync(self):
        """Inicia sincronizacao em background"""
        if self._running:
            logger.warning("Sincronizacao ja esta rodando")
            return

        self._running = True
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        logger.info("Sincronizacao em background iniciada")

    def stop_background_sync(self):
        """Para sincronizacao em background"""
        self._running = False
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Sincronizacao em background parada")

    def _sync_loop(self):
        """Loop principal de sincronizacao"""
        mysql_was_down = False
        while self._running:
            try:
                api_available = self.check_api_availability()
                mysql_available = self.check_mysql_availability()

                # Quando o MySQL volta, aplica a fila offline no MySQL local
                # e atualiza o SQLite com os dados mais recentes do MySQL.
                if mysql_available:
                    if mysql_was_down:
                        logger.info("MySQL local voltou; iniciando sync bidirectional")
                        mysql_was_down = False
                    try:
                        self._sync_queue_to_mysql()
                    except Exception as exc:
                        logger.error("Erro ao aplicar fila no MySQL local: %s", exc)
                    try:
                        self._sync_mysql_to_local_cache()
                    except Exception as exc:
                        logger.error("Erro ao sincronizar MySQL -> SQLite: %s", exc)
                else:
                    mysql_was_down = True

                # Fluxo complementar: API serpleno_web.
                if api_available:
                    try:
                        self._process_queue()
                    except Exception as exc:
                        logger.error("Erro ao processar fila na API: %s", exc)

                    if self.config.should_sync():
                        try:
                            self._sync_local_data()
                        except Exception as exc:
                            logger.error("Erro no sync local->API: %s", exc)

                # Aguarda proximo ciclo
                self._stop_event.wait(timeout=self.config.sync_interval)

            except Exception as exc:
                logger.error("Erro no loop de sincronizacao: %s", exc)
                self._stop_event.wait(timeout=60)

    def _process_queue(self):
        """Processa fila de operacoes pendentes"""
        pending = self.queue.get_pending()

        for item in pending:
            try:
                success = self._process_queue_item(item)
                if success:
                    self.queue.remove(item['id'])
                    self._notify_callbacks('sync_success', item)
                else:
                    self.queue.increment_attempt(item['id'])
                    self._notify_callbacks('sync_failed', item)
            except Exception as exc:
                logger.error("Erro ao processar item da fila: %s", exc)
                self.queue.increment_attempt(item['id'])

        # Limpa itens antigos
        self.queue.clear_old()

    def _process_queue_item(self, item: Dict[str, Any]) -> bool:
        """Processa um item da fila"""
        operation = item.get('operation')
        entity = item.get('entity')
        data = item.get('data', {})

        endpoint = self.SYNC_ENDPOINTS.get(entity)
        if not endpoint:
            logger.warning(f"Endpoint desconhecido para entidade: {entity}")
            return True  # Remove da fila

        url = f"{self.config.api_base_url}{endpoint}"

        try:
            payload = dict(data) if isinstance(data, dict) else {}
            if operation == 'create':
                old_id = payload.get("id") or item.get('entity_id')
                if is_local_id(old_id):
                    payload.pop("id", None)
                response = self._session.post(url, json=payload, timeout=self.config.api_timeout)
            if response.status_code in [200, 201]:
                new_id = self._parse_sync_id(response)
                if new_id and is_local_id(old_id):
                    self._reconcile_local_id(entity, old_id, new_id)
            elif operation == 'update':
                response = self._session.put(f"{url}{item.get('entity_id')}/", json=payload, timeout=self.config.api_timeout)
            elif operation == 'delete':
                response = self._session.delete(f"{url}{item.get('entity_id')}/", timeout=self.config.api_timeout)
            else:
                logger.warning(f"Operacao desconhecida: {operation}")
                return True

            return response.status_code in [200, 201, 204]

        except Exception as exc:
            logger.error(f"Erro ao sincronizar {operation} {entity}: {exc}")
            return False

    def _parse_sync_id(self, response) -> Any:
        """Extrai o ID do servidor a partir da resposta de criacao."""
        try:
            body = response.json()
            return body.get("id") or body.get("pk") or body.get("student_id")
        except Exception:
            return None

    def _reconcile_local_id(self, entity: str, old_id: Any, new_id: Any) -> None:
        """Reconcilia ID local com ID do servidor apos sync."""
        table_map = {
            "students": "students",
            "appointments": "appointments",
            "orientations": "orientations",
            "screenings": "screenings",
            "messages": "messages",
            "reports": "reports",
        }
        table = table_map.get(entity)
        if not table:
            return

        try:
            rows = local_cache.list_all(table, where_clause="id=?", params=(old_id,))
            if not rows:
                return
            row = rows[0]
            row["id"] = new_id
            local_cache.upsert(table, row, pk_field="id")
            # Atualiza referencias FK
            self._update_fk_references(entity, old_id, new_id)
            logger.info("ID reconciliado: %s.%s -> %s", entity, old_id, new_id)
        except Exception as exc:
            logger.error("Falha na reconciliacao de ID %s -> %s para %s: %s", old_id, new_id, entity, exc)

    def _update_fk_references(self, entity: str, old_id: Any, new_id: Any) -> None:
        """Atualiza referencias FK locais apos reconciliacao de ID."""
        fk_map = {
            "students": [
                ("appointments", "student_id"),
                ("orientations", "student_id"),
                ("screenings", "student_id"),
                ("wellness_mood", "student_id"),
            ],
        }
        fks = fk_map.get(entity, [])
        for table, fk_column in fks:
            try:
                local_cache.update(table, {fk_column: new_id}, fk_column, old_id)
            except Exception as exc:
                logger.debug("FK update skipped %s.%s -> %s: %s", table, fk_column, old_id, exc)

    def _sync_local_data(self):
        """Sincroniza dados locais com a API"""
        try:
            self._sync_students()
        except Exception as exc:
            logger.error("Erro ao sincronizar estudantes: %s", exc)

        try:
            self._sync_appointments()
        except Exception as exc:
            logger.error("Erro ao sincronizar agendamentos: %s", exc)

        try:
            self.config.update_last_sync()
        except Exception as exc:
            logger.error("Erro ao atualizar last_sync: %s", exc)

        self._notify_callbacks('sync_complete', None)

    def _sync_queue_to_mysql(self) -> None:
        """Aplica operacoes da fila no MySQL local quando a conexao volta."""
        pending = self.queue.get_pending()
        if not pending:
            return

        logger.info("Aplicando %d operacoes offline no MySQL local", len(pending))

        pending_sorted = sorted(
            pending,
            key=lambda item: _QUEUE_ENTITY_PRIORITY.get(item.get("entity", ""), 99),
        )

        id_reconciliation: Dict[int, int] = {}
        applied = 0
        for item in pending_sorted:
            try:
                success = self._apply_queue_item_to_mysql(item, id_reconciliation)
                if success:
                    self.queue.remove(item["id"])
                    applied += 1
                else:
                    self.queue.increment_attempt(item["id"])
            except Exception as exc:
                logger.error("Erro ao aplicar item da fila no MySQL: %s", exc)
                self.queue.increment_attempt(item["id"])

        logger.info("Sync fila->MySQL: %d/%d aplicados", applied, len(pending))

    def _apply_queue_item_to_mysql(self, item: Dict[str, Any], id_reconciliation: Optional[Dict[int, int]] = None) -> bool:
        """Aplica uma operacao da fila no MySQL local."""
        operation = item.get("operation")
        entity = item.get("entity")
        raw_data = item.get("data")

        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except Exception:
                raw_data = {}

        data = raw_data or {}

        if not entity or not operation:
            return False

        if id_reconciliation is not None:
            data = self._reconcile_fk_ids(entity, data, id_reconciliation)

        if entity == "user_preferences":
            logger.debug("Sync removido para entidade sem tabela MySQL: user_preferences")
            return True

        try:
            if operation == "create":
                return self._apply_create_to_mysql(entity, data, id_reconciliation)
            elif operation == "update":
                return self._apply_update_to_mysql(entity, data, item.get("entity_id"))
            elif operation == "delete":
                return self._apply_delete_to_mysql(entity, item.get("entity_id"))
            else:
                logger.warning("Operacao desconhecida na fila: %s", operation)
                return True
        except Exception as exc:
            logger.error("Falha ao aplicar %s %s no MySQL: %s", operation, entity, exc)
            return False

    def _reconcile_fk_ids(self, entity: str, data: Dict[str, Any], id_reconciliation: Dict[int, int]) -> Dict[str, Any]:
        """Substitui IDs locais por IDs MySQL ja reconciliados."""
        if not id_reconciliation:
            return data

        fk_fields = {
            "appointments": ["student_id"],
            "orientations": ["student_id"],
            "screenings": ["student_id", "form_id"],
            "messages": ["sender_id", "recipient_id"],
            "reports": ["generated_by_id"],
            "alerts": [],
        }
        fields = fk_fields.get(entity, [])
        for field in fields:
            value = data.get(field)
            if isinstance(value, int) and value in id_reconciliation:
                data[field] = id_reconciliation[value]
        return data

    def _check_fk_parents_exist(self, entity: str, data: Dict[str, Any]) -> bool:
        """Verifica se os registros pai referenciados existem no MySQL local."""
        checks = {
            "messages": [
                ("auth_user", "id", data.get("sender_id"), "sender_id"),
                ("auth_user", "id", data.get("recipient_id"), "recipient_id"),
            ],
            "appointments": [
                ("aluno", "id_aluno", data.get("student_id"), "student_id"),
            ],
            "orientations": [
                ("aluno", "id_aluno", data.get("student_id"), "student_id"),
            ],
            "screenings": [
                ("aluno", "id_aluno", data.get("student_id"), "student_id"),
                ("desktop_screeningform", "id", data.get("form_id"), "form_id"),
            ],
            "reports": [
                ("auth_user", "id", data.get("generated_by_id"), "generated_by_id"),
            ],
        }
        table_checks = checks.get(entity, [])
        for table, pk_column, fk_value, fk_name in table_checks:
            if fk_value is None:
                continue
            if isinstance(fk_value, int) and fk_value < 0:
                continue
            validate_mysql_table_name(table)
            _validate_identifier(pk_column)
            try:
                row = fetch_one(f"SELECT 1 FROM {table} WHERE {pk_column} = %s", (fk_value,))
                if not row:
                    warning_key = f"{entity}.{fk_name}={fk_value}"
                    now = time.time()
                    if now - self._fk_warning_reset > 60:
                        self._fk_warning_counts.clear()
                        self._fk_warning_reset = now
                    count = self._fk_warning_counts.get(warning_key, 0) + 1
                    self._fk_warning_counts[warning_key] = count
                    if count <= 3:
                        logger.warning(
                            "FK pai ausente: %s.%s=%s nao encontrado em %s.%s; pulando %s",
                            fk_name, fk_value, table, pk_column, entity, data.get("id"),
                        )
                    elif count == 4:
                        logger.warning(
                            "FK pai ausente repetida (%s): %s.%s=%s; suprimindo avisos por 60s",
                            warning_key, fk_name, fk_value, table,
                        )
                    return False
            except Exception as exc:
                logger.debug("Falha ao verificar FK %s.%s: %s", table, pk_column, exc)
                return False
        return True

    def _apply_create_to_mysql(self, entity: str, data: Dict[str, Any], id_reconciliation: Optional[Dict[int, int]] = None) -> bool:
        """Aplica INSERT no MySQL local."""
        try:
            if entity == "auth_user":
                return self._apply_create_auth_user_to_mysql(data, id_reconciliation)
            if entity == "students":
                return self._apply_create_student_to_mysql(data, id_reconciliation)
        except Exception as exc:
            logger.error("Erro ao executar CREATE para %s: %s", entity, exc)
            return False

        if not self._check_fk_parents_exist(entity, data):
            return False

        queries = {
            "appointments": (
                "INSERT INTO agendamento (student_id, data_hora, motivo, status, local, profissional, laudo, origem, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (data.get("student_id"), data.get("data_hora"), data.get("motivo"), data.get("status"),
                 data.get("local"), data.get("profissional"), data.get("laudo"), data.get("origem")),
            ),
            "orientations": (
                "INSERT INTO desktop_orientation (student_id, title, theme, session_date, content, is_markdown, motivational_message, action_plan, psychologist_id, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (data.get("student_id"), data.get("title"), data.get("theme"), data.get("session_date"),
                 data.get("content"), int(data.get("is_markdown", 0)), data.get("motivational_message"),
                 data.get("action_plan"), int(data.get("psychologist")) if str(data.get("psychologist") or "").isdigit() else None),
            ),
            "screenings": (
                "INSERT INTO desktop_screening (student_id, form_id, status, priority, scheduled_date, responses, observations, recommendations, requires_followup, followup_date, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (data.get("student_id"), data.get("form_id"), data.get("status"), data.get("priority"),
                 data.get("scheduled_date"), data.get("responses", "{}"), data.get("observations", ""),
                 data.get("recommendations", ""), int(data.get("requires_followup", 0)), data.get("followup_date")),
            ),
            "messages": (
                "INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (data.get("sender_id"), data.get("recipient_id"), data.get("text"),
                 data.get("timestamp", datetime.now().isoformat()), int(data.get("read", 0)),
                 data.get("caminho_arquivo"), data.get("tipo_arquivo")),
            ),
            "reports": (
                "INSERT INTO desktop_report (name, report_type, format, generated_at, parameters, data, file_path, file_size, is_public, expires_at, generated_by_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (data.get("name"), data.get("report_type"), data.get("format"),
                 data.get("generated_at", datetime.now().isoformat()), data.get("parameters", "{}"),
                 data.get("data", "{}"), data.get("file_path"), data.get("file_size"),
                 int(data.get("is_public", 0)), data.get("expires_at"), data.get("generated_by_id")),
            ),
            "alerts": (
                "UPDATE desktop_alert SET is_read = 1 WHERE id = %s",
                (data.get("id"),),
            ),
            "desktop_screeningform": (
                "INSERT INTO desktop_screeningform (id, name, description, questions, is_active, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) "
                "ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description), questions = VALUES(questions), is_active = VALUES(is_active)",
                (
                    data.get("id"),
                    data.get("name"),
                    data.get("description", ""),
                    json.dumps(data.get("questions")) if data.get("questions") is not None else "[]",
                    int(data.get("is_active", 1)),
                ),
            ),
        }

        if entity not in queries:
            logger.warning("Entidade desconhecida para apply CREATE: %s", entity)
            return True

        query, params = queries[entity]
        try:
            execute_non_query(query, params)
            logger.debug("CREATE aplicado no MySQL: %s %s", entity, data.get("id"))
            return True
        except Exception as exc:
            logger.error("Erro ao executar CREATE para %s: %s", entity, exc)
            return False

    def _apply_create_auth_user_to_mysql(self, data: Dict[str, Any], id_reconciliation: Optional[Dict[int, int]]) -> bool:
        local_id = data.get("id")
        if isinstance(local_id, int) and local_id < 0:
            query = (
                "INSERT INTO auth_user (id, username, email, password, first_name, last_name, is_staff, is_superuser, is_active, last_login) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL) "
                "ON DUPLICATE KEY UPDATE username = VALUES(username)"
            )
            params = (
                local_id,
                data.get("username"),
                data.get("email"),
                data.get("password", ""),
                data.get("first_name", ""),
                data.get("last_name", ""),
                int(data.get("is_staff", 0)),
                int(data.get("is_superuser", 0)),
                int(data.get("is_active", 1)),
            )
            execute_non_query(query, params)
            if id_reconciliation is not None:
                id_reconciliation[local_id] = local_id
            logger.debug("CREATE auth_user aplicado no MySQL: %s", local_id)
            return True

        query = (
            "INSERT INTO auth_user (username, email, password, first_name, last_name, is_staff, is_superuser, is_active, last_login) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)"
        )
        params = (
            data.get("username"),
            data.get("email"),
            data.get("password", ""),
            data.get("first_name", ""),
            data.get("last_name", ""),
            int(data.get("is_staff", 0)),
            int(data.get("is_superuser", 0)),
            int(data.get("is_active", 1)),
        )
        execute_non_query(query, params)
        logger.debug("CREATE auth_user aplicado no MySQL")
        return True

    def _apply_create_student_to_mysql(self, data: Dict[str, Any], id_reconciliation: Optional[Dict[int, int]]) -> bool:
        local_id = data.get("id")
        if isinstance(local_id, int) and local_id < 0:
            query = (
                "INSERT INTO aluno (id_aluno, nome, professor_responsavel, status, priority_level, tags, avatar, dark_mode, notifications_enabled, has_medical_report, requires_attention, created_at, updated_at, minigame_blocked) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s) "
                "ON DUPLICATE KEY UPDATE nome = VALUES(nome)"
            )
            params = (
                local_id,
                data.get("nome"),
                data.get("professor_responsavel") or "Não informado",
                data.get("status") or "ativo",
                int(data.get("priority_level") or 0),
                json.dumps(data.get("tags")) if data.get("tags") is not None else "[]",
                _shorten_avatar(data.get("avatar")),
                int(data.get("dark_mode") or 0),
                int(data.get("notifications_enabled") if data.get("notifications_enabled") is not None else 1),
                int(data.get("has_medical_report", 0)),
                int(data.get("requires_attention", 0)),
                int(data.get("minigame_blocked", 0)),
            )
            execute_non_query(query, params)
            if id_reconciliation is not None:
                id_reconciliation[local_id] = local_id
            logger.debug("CREATE student aplicado no MySQL: %s", local_id)
            return True

        query = (
            "INSERT INTO aluno (nome, professor_responsavel, status, priority_level, tags, avatar, dark_mode, notifications_enabled, has_medical_report, requires_attention, created_at, updated_at, minigame_blocked) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)"
        )
        params = (
            data.get("nome"),
            data.get("professor_responsavel") or "Não informado",
            data.get("status") or "ativo",
            int(data.get("priority_level") or 0),
            json.dumps(data.get("tags")) if data.get("tags") is not None else "[]",
            _shorten_avatar(data.get("avatar")),
            int(data.get("dark_mode") or 0),
            int(data.get("notifications_enabled") if data.get("notifications_enabled") is not None else 1),
            int(data.get("has_medical_report", 0)),
            int(data.get("requires_attention", 0)),
            int(data.get("minigame_blocked", 0)),
        )
        execute_non_query(query, params)
        logger.debug("CREATE student aplicado no MySQL")
        return True

    def _apply_update_to_mysql(self, entity: str, data: Dict[str, Any], entity_id: Any) -> bool:
        """Aplica UPDATE no MySQL local."""
        updates = []
        params = []
        for key, value in data.items():
            if key == 'id':
                continue
            updates.append(f"`{key}` = %s")
            params.append(value)

        if not updates:
            return False

        table_map = {
            "students": "aluno",
            "appointments": "agendamento",
            "orientations": "desktop_orientation",
            "screenings": "desktop_screening",
            "messages": "desktop_message",
            "reports": "desktop_report",
            "alerts": "desktop_alert",
            "auth_user": "auth_user",
            "desktop_screeningform": "desktop_screeningform",
        }

        pk_column_map = {
            "students": "id_aluno",
            "appointments": "id",
            "orientations": "id",
            "screenings": "id",
            "messages": "id",
            "reports": "id",
            "alerts": "id",
            "auth_user": "id",
            "desktop_screeningform": "id",
        }

        tables_with_updated_at = {
            "students", "appointments", "orientations", "screenings",
        }

        table = table_map.get(entity)
        if not table:
            logger.warning("Entidade desconhecida para apply UPDATE: %s", entity)
            return False

        validate_mysql_table_name(table)

        pk_column = pk_column_map.get(entity, "id")
        set_clause = ", ".join(updates)
        if entity in tables_with_updated_at:
            set_clause += ", updated_at = NOW()"
        query = f"UPDATE {table} SET {set_clause} WHERE {pk_column} = %s"
        params.append(entity_id)

        try:
            execute_non_query(query, tuple(params))
            logger.debug("UPDATE aplicado no MySQL: %s.%s", entity, entity_id)
            return True
        except Exception as exc:
            logger.error("Erro ao executar UPDATE para %s.%s: %s", entity, entity_id, exc)
            return False

    def _apply_delete_to_mysql(self, entity: str, entity_id: Any) -> bool:
        """Aplica DELETE no MySQL local."""
        table_map = {
            "students": "aluno",
            "appointments": "agendamento",
            "orientations": "desktop_orientation",
            "screenings": "desktop_screening",
            "messages": "desktop_message",
            "reports": "desktop_report",
            "alerts": "desktop_alert",
            "auth_user": "auth_user",
            "desktop_screeningform": "desktop_screeningform",
        }

        pk_column_map = {
            "students": "id_aluno",
            "appointments": "id",
            "orientations": "id",
            "screenings": "id",
            "messages": "id",
            "reports": "id",
            "alerts": "id",
            "auth_user": "id",
            "desktop_screeningform": "id",
        }

        table = table_map.get(entity)
        if not table:
            logger.warning("Entidade desconhecida para apply DELETE: %s", entity)
            return False

        validate_mysql_table_name(table)

        pk_column = pk_column_map.get(entity, "id")
        query = f"DELETE FROM {table} WHERE {pk_column} = %s"
        try:
            execute_non_query(query, (entity_id,))
            logger.debug("DELETE aplicado no MySQL: %s.%s", entity, entity_id)
            return True
        except Exception as exc:
            logger.error("Erro ao executar DELETE para %s.%s: %s", entity, entity_id, exc)
            return False

    def _sync_mysql_to_local_cache(self) -> None:
        """Puxa atualizacoes do MySQL local para o SQLite local."""
        try:
            self._sync_students_mysql_to_local()
        except Exception as exc:
            logger.error("Erro ao puxar estudantes do MySQL para SQLite: %s", exc)

        try:
            self._sync_appointments_mysql_to_local()
        except Exception as exc:
            logger.error("Erro ao puxar agendamentos do MySQL para SQLite: %s", exc)

    def _sync_students_mysql_to_local(self) -> None:
        """Sincroniza estudantes do MySQL local para SQLite local."""
        last_sync = self.config.last_sync
        query = (
            "SELECT a.id_aluno, a.nome, u.email AS email, "
            "a.has_medical_report, a.requires_attention, a.updated_at "
            "FROM aluno a "
            "LEFT JOIN auth_user u ON a.user_id = u.id"
        )
        params = ()
        if last_sync:
            query += " WHERE a.updated_at > %s"
            params = (last_sync,)

        rows = fetch_all(query, params)
        if not rows:
            return

        upserted = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            data = {
                'id': row.get('id_aluno'),
                'nome': row.get('nome'),
                'email': row.get('email'),
                'has_medical_report': row.get('has_medical_report', 0),
                'requires_attention': row.get('requires_attention', 0),
            }
            if data['id'] is None:
                continue
            local_cache.upsert_student(data)
            upserted += 1

        logger.info("Sync MySQL->SQLite students: %d atualizados", upserted)

    def _sync_appointments_mysql_to_local(self) -> None:
        """Sincroniza agendamentos do MySQL local para SQLite local."""
        last_sync = self.config.last_sync
        query = "SELECT * FROM agendamento"
        params = ()
        if last_sync:
            query += " WHERE updated_at > %s OR created_at > %s"
            params = (last_sync, last_sync)

        rows = fetch_all(query, params)
        if not rows:
            return

        upserted = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            data = {
                'id': row.get('id'),
                'student_id': row.get('student_id'),
                'data_hora': row.get('data_hora').isoformat() if hasattr(row.get('data_hora'), 'isoformat') else str(row.get('data_hora') or ''),
                'motivo': row.get('motivo'),
                'status': row.get('status'),
                'local': row.get('local'),
                'profissional': row.get('profissional'),
                'laudo': row.get('laudo'),
                'origem': row.get('origem'),
            }
            if data['id'] is None:
                continue
            local_cache.upsert_appointment(data)
            upserted += 1

        logger.info("Sync MySQL->SQLite appointments: %d atualizados", upserted)

    def _sync_students(self):
        """Sincroniza estudantes locais com a API"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            last_sync = self.config.last_sync
            query = "SELECT * FROM aluno"
            if last_sync:
                query += " WHERE updated_at > %s"
                cursor.execute(query, (last_sync,))
            else:
                cursor.execute(query)

            students = cursor.fetchall()

            if students:
                logger.info(f"Sincronizando {len(students)} estudantes")
                url = f"{self.config.api_base_url}/api/v1/desktop/students/sync/"
                self._session.post(url, json={'students': students}, timeout=30)

        except Exception as exc:
            logger.error(f"Erro ao sincronizar estudantes: {exc}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def _sync_appointments(self):
        """Sincroniza agendamentos locais com a API"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            last_sync = self.config.last_sync
            query = "SELECT * FROM agendamento"
            if last_sync:
                query += " WHERE updated_at > %s OR created_at > %s"
                cursor.execute(query, (last_sync, last_sync))
            else:
                cursor.execute(query)

            appointments = cursor.fetchall()

            if appointments:
                logger.info(f"Sincronizando {len(appointments)} agendamentos")
                url = f"{self.config.api_base_url}/api/v1/desktop/schedule/appointments/sync/"
                self._session.post(url, json={'appointments': appointments}, timeout=30)

        except Exception as exc:
            logger.error(f"Erro ao sincronizar agendamentos: {exc}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def add_to_queue(self, operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
        """Adiciona operacao na fila de sincronizacao"""
        if self.config.is_independent():
            return  # Nao adiciona na fila em modo independente

        self.queue.add(operation, entity, entity_id, data)

    def sync_now(self) -> Dict[str, Any]:
        """Executa sincronizacao imediata"""
        result = {
            'success': False,
            'api_available': False,
            'items_synced': 0,
            'items_pending': 0
        }

        if not self.check_api_availability():
            result['items_pending'] = len(self.queue.get_pending())
            return result

        result['api_available'] = True

        # Processa fila
        pending_before = len(self.queue.get_pending())
        self._process_queue()
        pending_after = len(self.queue.get_pending())
        result['items_synced'] = pending_before - pending_after
        result['items_pending'] = pending_after

        # Sincroniza dados locais
        self._sync_local_data()

        result['success'] = True
        return result

    def register_callback(self, event: str, callback: Callable):
        """Registra callback para eventos de sincronizacao"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _notify_callbacks(self, event: str, data: Any):
        """Notifica callbacks registrados"""
        callbacks = self._callbacks.get(event, [])
        for callback in callbacks:
            try:
                callback(data)
            except Exception as exc:
                logger.error("Erro em callback %s: %s", event, exc)

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do servico de sincronizacao"""
        return {
            'mode': self.config.mode.value,
            'api_available': self.config.api_available,
            'api_url': self.config.api_base_url,
            'last_sync': self.config.last_sync.isoformat() if self.config.last_sync else None,
            'pending_items': len(self.queue.get_pending()),
            'auto_sync': self.config.auto_sync,
            'running': self._running
        }


# Instancia global
sync_service = SyncService()


def get_sync_service() -> SyncService:
    """Retorna a instancia global do servico de sincronizacao"""
    return sync_service


def queue_sync(operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
    """Adiciona operacao na fila de sincronizacao"""
    sync_service.add_to_queue(operation, entity, entity_id, data)
