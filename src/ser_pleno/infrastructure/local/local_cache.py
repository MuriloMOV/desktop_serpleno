# -*- coding: utf-8 -*-
"""Cache local SQLite para funcionamento offline."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


TABLE_WHITELIST = {
    "students",
    "appointments",
    "orientations",
    "screenings",
    "mural_posts",
    "sync_queue",
    "wellness_mood",
    "wellness_checkin",
    "wellness_challenges",
    "wellness_challenge_assignments",
    "alerts",
    "messages",
    "reports",
    "user_preferences",
    "orientation_attachments",
    "goals",
    "goal_progress",
    "help_requests",
    "notifications",
    "report_templates",
    "shared_clinical_data",
    "auth_users",
}


def validate_table_name(table: str) -> None:
    if table not in TABLE_WHITELIST:
        raise ValueError(
            f"Nome de tabela invalido: {table!r}. "
            f"Tabelas permitidas: {sorted(TABLE_WHITELIST)}"
        )


def _validate_identifier(name: str, kind: str = "identificador") -> None:
    if not name.isidentifier():
        raise ValueError(f"Nome de {kind} invalido: {name!r}")


from ser_pleno.config.paths import get_project_root

class LocalCache:
    """Cache local SQLite para dados que devem funcionar offline."""

    _BASE_DIR = get_project_root()
    DB_FILE = os.path.join(_BASE_DIR, "config", "ser_pleno_local.db")

    def __init__(self) -> None:
        self._local = threading.local()
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        local = getattr(self, "_local", None)
        if local is None:
            local = threading.local()
            self._local = local
        try:
            conn = local.connection
        except AttributeError:
            conn = None
        if conn is None:
            os.makedirs(os.path.dirname(self.DB_FILE), exist_ok=True)
            conn = sqlite3.connect(self.DB_FILE)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            local.connection = conn
        return conn

    def close_connection(self) -> None:
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            try:
                conn.close()
            except Exception as exc:
                logger.debug("Falha ao fechar conexão local: %s", exc)
            self._local.connection = None

    def _ensure_tables(self) -> None:
        conn = self._get_connection()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    nome TEXT,
                    email TEXT,
                    curso TEXT,
                    age INTEGER,
                    phone TEXT,
                    professor_responsavel TEXT,
                    emergency_contact TEXT,
                    emergency_phone TEXT,
                    attention_reason TEXT,
                    general_notes TEXT,
                    has_medical_report INTEGER DEFAULT 0,
                    requires_attention INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'ativo',
                    priority_level INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    data_hora TEXT,
                    motivo TEXT,
                    status TEXT,
                    local TEXT,
                    profissional TEXT,
                    laudo TEXT,
                    origem TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS orientations (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    title TEXT,
                    theme TEXT,
                    session_date TEXT,
                    content TEXT,
                    is_markdown INTEGER DEFAULT 0,
                    motivational_message TEXT,
                    action_plan TEXT,
                    psychologist TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS screenings (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    form_id INTEGER,
                    status TEXT,
                    priority TEXT,
                    scheduled_date TEXT,
                    responses TEXT,
                    observations TEXT,
                    recommendations TEXT,
                    requires_followup INTEGER DEFAULT 0,
                    followup_date TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS mural_posts (
                    id INTEGER PRIMARY KEY,
                    titulo TEXT,
                    conteudo TEXT,
                    autor TEXT,
                    publicado_em TEXT,
                    ativo INTEGER DEFAULT 1,
                    categoria TEXT,
                    data_agendamento TEXT,
                    link_externo TEXT,
                    blocos TEXT,
                    layout TEXT,
                    horario_evento TEXT,
                    local_fisico TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id TEXT PRIMARY KEY,
                    operation TEXT,
                    entity TEXT,
                    entity_id INTEGER,
                    data TEXT,
                    created_at TEXT,
                    attempts INTEGER DEFAULT 0,
                    last_attempt TEXT
                );
                CREATE TABLE IF NOT EXISTS wellness_mood (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    mood_level INTEGER,
                    entry_date TEXT,
                    notes TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS wellness_checkin (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    overall_wellbeing INTEGER,
                    check_in_date TEXT,
                    check_in_type TEXT,
                    responses TEXT,
                    attention_areas TEXT,
                    recommendations TEXT,
                    follow_up_needed INTEGER DEFAULT 0,
                    follow_up_date TEXT,
                    professional_notes TEXT,
                    conducted_by_id INTEGER,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS wellness_challenges (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    difficulty TEXT,
                    points INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS wellness_challenge_assignments (
                    id INTEGER PRIMARY KEY,
                    challenge_id INTEGER,
                    student_id INTEGER,
                    assigned_by_id INTEGER,
                    status TEXT DEFAULT 'assigned',
                    assigned_at TEXT,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY,
                    alert_type TEXT,
                    message TEXT,
                    created_at TEXT,
                    is_read INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    sender_id INTEGER,
                    recipient_id INTEGER,
                    text TEXT,
                    timestamp TEXT,
                    read INTEGER DEFAULT 0,
                    caminho_arquivo TEXT,
                    tipo_arquivo TEXT
                );
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    report_type TEXT,
                    format TEXT,
                    generated_at TEXT,
                    parameters TEXT,
                    data TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    is_public INTEGER DEFAULT 0,
                    expires_at TEXT,
                    generated_by_id INTEGER,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    theme TEXT,
                    notifications TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS shared_clinical_data (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER,
                    shared_by_id INTEGER,
                    shared_with_user_id INTEGER,
                    shared_with_role TEXT,
                    data_type TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS help_requests (
                    id INTEGER PRIMARY KEY,
                    aluno_id INTEGER,
                    tipo TEXT,
                    mensagem TEXT,
                    prioridade TEXT,
                    status TEXT,
                    localizacao TEXT,
                    dados_extras TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    viewed_at TEXT,
                    resolved_at TEXT,
                    resposta_enviada INTEGER DEFAULT 0,
                    resposta_em TEXT,
                    resposta_lida INTEGER DEFAULT 0,
                    atendimento_finalizado INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    password_hash TEXT,
                    is_superuser INTEGER DEFAULT 0,
                    is_staff INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    last_login TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS report_templates (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    report_type TEXT,
                    template_config TEXT,
                    default_parameters TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_by_id INTEGER,
                    created_at TEXT,
                    updated_at TEXT
                );
                """
            )
            conn.commit()
            self._migrate_wellness_checkin(conn)
        except Exception as exc:
            logger.debug("Falha ao garantir tabelas locais: %s", exc)

    def _migrate_wellness_checkin(self, conn: sqlite3.Connection) -> None:
        """Migra wellness_checkin se houver colunas obsoletas."""
        try:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(wellness_checkin)").fetchall()}
            dead_cols = {"academic_pressure", "social_wellbeing", "emotional_state"}
            missing_new = {"check_in_type", "responses", "attention_areas", "recommendations",
                           "follow_up_needed", "follow_up_date", "professional_notes", "conducted_by_id"}
            if cols & dead_cols or not (cols & missing_new):
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS wellness_checkin_new (
                        id INTEGER PRIMARY KEY,
                        student_id INTEGER,
                        overall_wellbeing INTEGER,
                        check_in_date TEXT,
                        check_in_type TEXT,
                        responses TEXT,
                        attention_areas TEXT,
                        recommendations TEXT,
                        follow_up_needed INTEGER DEFAULT 0,
                        follow_up_date TEXT,
                        professional_notes TEXT,
                        conducted_by_id INTEGER,
                        updated_at TEXT
                    );
                    INSERT OR IGNORE INTO wellness_checkin_new
                        (id, student_id, overall_wellbeing, check_in_date, updated_at)
                    SELECT id, student_id, overall_wellbeing, check_in_date, updated_at
                    FROM wellness_checkin;
                    DROP TABLE wellness_checkin;
                    ALTER TABLE wellness_checkin_new RENAME TO wellness_checkin;
                """)
                conn.commit()
        except Exception as exc:
            logger.debug("Migracao wellness_checkin nao aplicada: %s", exc)

    # Generic helpers

    def upsert(self, table: str, data: Dict[str, Any], pk_field: str = "id") -> None:
        validate_table_name(table)
        if not data:
            return
        keys = list(data.keys())
        for key in keys:
            _validate_identifier(key, kind="coluna")
        placeholders = ", ".join(["?"] * len(keys))
        columns = ", ".join(keys)
        update_clause = ", ".join([f"{k}=excluded.{k}" for k in keys if k != pk_field])
        _validate_identifier(pk_field, kind="campo PK")
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {update_clause};"
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in data.values()]
        conn = self._get_connection()
        try:
            conn.execute(query, values)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception as exc:
                logger.debug("Falha no rollback: %s", exc)
            raise

    def update(self, table: str, data: Dict[str, Any], pk_field: str, entity_id: Any) -> None:
        validate_table_name(table)
        if not data:
            return
        for key in data.keys():
            _validate_identifier(key, kind="coluna")
        set_clause = ", ".join(f"{k}=?" for k in data.keys())
        keys = list(data.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in data.values()]
        values.append(entity_id)
        _validate_identifier(pk_field, kind="campo PK")
        query = f"UPDATE {table} SET {set_clause} WHERE {pk_field}=?"
        conn = self._get_connection()
        try:
            conn.execute(query, values)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception as exc:
                logger.debug("Falha no rollback: %s", exc)
            raise

    def list_all(self, table: str, where_clause: Optional[str] = None, params: tuple = ()) -> List[Dict[str, Any]]:
        validate_table_name(table)
        query = f"SELECT * FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.debug("Falha em list_all(%s): %s", table, exc)
            return []

    def delete(self, table: str, pk_field: str, entity_id: Any) -> None:
        validate_table_name(table)
        _validate_identifier(pk_field, kind="campo PK")
        conn = self._get_connection()
        try:
            conn.execute(f"DELETE FROM {table} WHERE {pk_field}=?", (entity_id,))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception as exc:
                logger.debug("Falha no rollback: %s", exc)
            raise

    def add_sync_queue(self, operation: str, entity: str, entity_id: int, data: Dict[str, Any]) -> None:
        item = {
            "id": f"{operation}_{entity}_{entity_id}_{datetime.now().timestamp()}",
            "operation": operation,
            "entity": entity,
            "entity_id": entity_id,
            "data": json.dumps(data),
            "created_at": datetime.now().isoformat(),
            "attempts": 0,
            "last_attempt": None,
        }
        self.upsert("sync_queue", item, pk_field="id")

    def update_sync_queue_attempt(self, item_id: str, attempts: int, last_attempt: Optional[str]) -> None:
        self.update(
            "sync_queue",
            {"attempts": attempts, "last_attempt": last_attempt},
            pk_field="id",
            entity_id=item_id,
        )

    def clear_old_sync_queue(self, max_attempts: int = 5) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                "DELETE FROM sync_queue WHERE attempts >= ?",
                (max_attempts,),
            )
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception as exc:
                logger.debug("Falha no rollback: %s", exc)

    # Students

    def upsert_student(self, student: Dict[str, Any]) -> None:
        student["updated_at"] = datetime.now().isoformat()
        self.upsert("students", student)

    def list_students(self, busca: Optional[str] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if busca:
            where = "nome LIKE ? OR email LIKE ?"
            params = (f"%{busca}%", f"%{busca}%")
        return self.list_all("students", where_clause=where, params=params)

    # Appointments

    def upsert_appointment(self, appointment: Dict[str, Any]) -> None:
        appointment["updated_at"] = datetime.now().isoformat()
        self.upsert("appointments", appointment)

    def list_appointments(self, data: Optional[str] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if data:
            where = "DATE(data_hora)=?"
            params = (data,)
        return self.list_all("appointments", where_clause=where, params=params)

    # Orientations

    def upsert_orientation(self, orientation: Dict[str, Any]) -> None:
        orientation["updated_at"] = datetime.now().isoformat()
        self.upsert("orientations", orientation)

    def list_orientations(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if student_id:
            where = "student_id=?"
            params = (student_id,)
        return self.list_all("orientations", where_clause=where, params=params)

    # Screenings

    def upsert_screening(self, screening: Dict[str, Any]) -> None:
        screening["updated_at"] = datetime.now().isoformat()
        self.upsert("screenings", screening)

    def list_screenings(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if student_id:
            where = "student_id=?"
            params = (student_id,)
        return self.list_all("screenings", where_clause=where, params=params)

    # Mural

    def upsert_mural_post(self, post: Dict[str, Any]) -> None:
        post["updated_at"] = datetime.now().isoformat()
        self.upsert("mural_posts", post)

    def list_mural_posts(self, busca: Optional[str] = None) -> List[Dict[str, Any]]:
        where = "ativo=1"
        params: tuple = ()
        if busca:
            where += " AND (titulo LIKE ? OR conteudo LIKE ? OR autor LIKE ?)"
            params = (f"%{busca}%", f"%{busca}%", f"%{busca}%")
        return self.list_all("mural_posts", where_clause=where, params=params)

    # Wellness / Mood

    def upsert_wellness_mood(self, mood: Dict[str, Any]) -> None:
        mood["updated_at"] = datetime.now().isoformat()
        self.upsert("wellness_mood", mood)

    def list_wellness_moods(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if student_id:
            where = "student_id=?"
            params = (student_id,)
        return self.list_all("wellness_mood", where_clause=where, params=params)

    def upsert_wellness_checkin(self, checkin: Dict[str, Any]) -> None:
        checkin["updated_at"] = datetime.now().isoformat()
        self.upsert("wellness_checkin", checkin)

    def list_wellness_checkins(self) -> List[Dict[str, Any]]:
        return self.list_all("wellness_checkin")

    def upsert_wellness_challenge(self, challenge: Dict[str, Any]) -> None:
        challenge["updated_at"] = datetime.now().isoformat()
        self.upsert("wellness_challenges", challenge)

    def list_wellness_challenges(self) -> List[Dict[str, Any]]:
        return self.list_all("wellness_challenges")

    def upsert_wellness_challenge_assignment(self, assignment: Dict[str, Any]) -> None:
        assignment["updated_at"] = datetime.now().isoformat()
        self.upsert("wellness_challenge_assignments", assignment)

    def list_wellness_challenge_assignments(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if student_id is not None:
            where = "student_id=?"
            params = (student_id,)
        return self.list_all("wellness_challenge_assignments", where_clause=where, params=params)

    def get_student_name_map(self) -> Dict[int, str]:
        """Retorna mapa student_id -> nome para enriquecimento de leituras locais."""
        rows = self.list_all("students")
        return {r.get("id"): r.get("nome", "") for r in rows if r.get("id") is not None}

    # Help Requests

    def upsert_help_request(self, help_request: Dict[str, Any]) -> None:
        help_request["updated_at"] = datetime.now().isoformat()
        self.upsert("help_requests", help_request)

    def list_help_requests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if status:
            where = "status=?"
            params = (status,)
        return self.list_all("help_requests", where_clause=where, params=params)

    # Alerts

    def upsert_alert(self, alert: Dict[str, Any]) -> None:
        self.upsert("alerts", alert)

    def list_alerts(self) -> List[Dict[str, Any]]:
        return self.list_all("alerts")

    # Messages

    def upsert_message(self, message: Dict[str, Any]) -> None:
        self.upsert("messages", message)

    def list_messages(self, sender_id: Optional[int] = None, recipient_id: Optional[int] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        if sender_id is not None and recipient_id is not None:
            where = "(sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?)"
            params = (sender_id, recipient_id, recipient_id, sender_id)
        elif sender_id is not None:
            where = "sender_id=?"
            params = (sender_id,)
        elif recipient_id is not None:
            where = "recipient_id=?"
            params = (recipient_id,)
        return self.list_all("messages", where_clause=where, params=params)

    def list_group_messages(self) -> List[Dict[str, Any]]:
        return self.list_all("messages", where_clause="recipient_id IS NULL")

    # Reports

    def upsert_report(self, report: Dict[str, Any]) -> None:
        report["updated_at"] = datetime.now().isoformat()
        self.upsert("reports", report)

    def list_reports(self) -> List[Dict[str, Any]]:
        return self.list_all("reports")

    # Report Templates

    def upsert_report_template(self, template: Dict[str, Any]) -> None:
        template["updated_at"] = datetime.now().isoformat()
        self.upsert("report_templates", template)

    def list_report_templates(self) -> List[Dict[str, Any]]:
        return self.list_all("report_templates")

    # User preferences

    def upsert_user_preferences(self, prefs: Dict[str, Any]) -> None:
        self.upsert("user_preferences", prefs)

    def list_user_preferences(self) -> List[Dict[str, Any]]:
        return self.list_all("user_preferences")

    # Orientation attachments

    def upsert_orientation_attachment(self, attachment: Dict[str, Any]) -> None:
        self.upsert("orientation_attachments", attachment)

    def list_orientation_attachments(self, orientation_id: int) -> List[Dict[str, Any]]:
        return self.list_all("orientation_attachments", where_clause="orientation_id=?", params=(orientation_id,))

    def delete_orientation_attachment(self, attachment_id: int) -> None:
        self.delete("orientation_attachments", "id", attachment_id)

    # Shared Clinical Data

    def upsert_shared_data(self, data: Dict[str, Any]) -> None:
        self.upsert("shared_clinical_data", data)

    def list_shared_data(self, busca: Optional[str] = None, data_type: Optional[str] = None, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        where = None
        params: tuple = ()
        parts = []
        if data_type:
            parts.append("data_type=?")
            params = params + (data_type,)
        if student_id:
            parts.append("student_id=?")
            params = params + (student_id,)
        if parts:
            where = " AND ".join(parts)
        rows = self.list_all("shared_clinical_data", where_clause=where, params=params)
        if busca:
            termo = busca.lower()
            rows = [r for r in rows if termo in r.get("student_name", "").lower()]
        return rows


# Singleton do cache local SQLite.
_local_cache_instance: Optional["LocalCache"] = None
_local_cache_lock = threading.RLock()


def get_local_cache() -> "LocalCache":
    global _local_cache_instance
    if _local_cache_instance is None:
        with _local_cache_lock:
            if _local_cache_instance is None:
                _local_cache_instance = LocalCache()
    return _local_cache_instance


# Atalho para uso direto em repositories/services.
local_cache: "LocalCache" = get_local_cache()
