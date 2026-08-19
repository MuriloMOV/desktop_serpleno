"""Initial schema migration."""

from __future__ import annotations

UP_SQL = """
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
CREATE TABLE IF NOT EXISTS screeningforms (
    id INTEGER PRIMARY KEY,
    name TEXT,
    form_type TEXT,
    version TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
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
CREATE TABLE IF NOT EXISTS availability (
    horario TEXT PRIMARY KEY,
    is_active INTEGER DEFAULT 1,
    dias TEXT DEFAULT 'segunda-terca-quarta-quinta-sexta',
    updated_at TEXT
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
CREATE TABLE IF NOT EXISTS shared_clinical_data (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    shared_by_id INTEGER,
    shared_with_user_id INTEGER,
    shared_with_role TEXT,
    data_type TEXT,
    created_at TEXT
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
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    conducted_by_id INTEGER,
    date TEXT,
    intervention_type TEXT,
    duration_minutes INTEGER,
    intervention_notes TEXT,
    outcome TEXT DEFAULT 'pending',
    outcome_notes TEXT,
    follow_up_required INTEGER DEFAULT 0,
    follow_up_date TEXT,
    follow_up_completed INTEGER DEFAULT 0,
    is_confidential INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]',
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    role TEXT DEFAULT 'visitante',
    permissions TEXT DEFAULT '[]',
    is_active_profile INTEGER DEFAULT 1,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS orientation_attachments (
    id INTEGER PRIMARY KEY,
    orientation_id INTEGER,
    file_name TEXT,
    file_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    created_at TEXT
);
"""

DOWN_SQL = None


MIGRATION_ID = "001_initial_schema"
