-- Script SQL para criar tabela de auditoria
-- Executar no banco de dados MySQL/MariaDB

-- Tabela de log de auditoria
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL COMMENT 'Nome da tabela afetada',
    record_id BIGINT COMMENT 'ID do registro afetado',
    action VARCHAR(20) NOT NULL COMMENT 'Tipo de ação: CREATE, UPDATE, DELETE, LOGIN, etc.',
    old_values JSON COMMENT 'Valores anteriores (para UPDATE/DELETE)',
    new_values JSON COMMENT 'Novos valores (para CREATE/UPDATE)',
    user_id INT COMMENT 'ID do usuário que fez a ação',
    username VARCHAR(150) COMMENT 'Nome de usuário',
    ip_address VARCHAR(45) COMMENT 'Endereço IP',
    user_agent VARCHAR(500) COMMENT 'User agent do navegador',
    details TEXT COMMENT 'Detalhes adicionais',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data/hora da ação',
    
    -- Índices
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de auditoria do sistema';

-- Tabela de perfis de usuário (para roles)
CREATE TABLE IF NOT EXISTS user_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'ID do usuário (auth_user)',
    role VARCHAR(50) DEFAULT 'visitante' COMMENT 'Role do usuário: admin, psicologo, coordenador, estudante, visitante',
    permissions JSON COMMENT 'Permissões extras em formato JSON',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    UNIQUE KEY uk_user (user_id),
    INDEX idx_role (role),
    
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Perfil de usuário com roles e permissões';

-- Trigger para auditoria automática (opcional)
-- Exemplo para tabela aluno

DELIMITER //

CREATE TRIGGER IF NOT EXISTS aluno_audit_insert
AFTER INSERT ON aluno
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, new_values, created_at)
    VALUES ('aluno', NEW.id_aluno, 'CREATE', 
            JSON_OBJECT('nome', NEW.nome, 'email', NEW.email, 'has_medical_report', NEW.has_medical_report),
            NOW(6));
END//

CREATE TRIGGER IF NOT EXISTS aluno_audit_update
AFTER UPDATE ON aluno
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, created_at)
    VALUES ('aluno', NEW.id_aluno, 'UPDATE',
            JSON_OBJECT('nome', OLD.nome, 'email', OLD.email, 'has_medical_report', OLD.has_medical_report),
            JSON_OBJECT('nome', NEW.nome, 'email', NEW.email, 'has_medical_report', NEW.has_medical_report),
            NOW(6));
END//

CREATE TRIGGER IF NOT EXISTS aluno_audit_delete
BEFORE DELETE ON aluno
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, created_at)
    VALUES ('aluno', OLD.id_aluno, 'DELETE',
            JSON_OBJECT('nome', OLD.nome, 'email', OLD.email, 'has_medical_report', OLD.has_medical_report),
            NOW(6));
END//

DELIMITER ;

-- View para facilitar consultas de auditoria
CREATE OR REPLACE VIEW v_audit_log AS
SELECT 
    al.id,
    al.table_name,
    al.record_id,
    al.action,
    al.old_values,
    al.new_values,
    al.user_id,
    al.username,
    al.ip_address,
    al.details,
    al.created_at,
    u.email as user_email,
    CASE al.action
        WHEN 'CREATE' THEN 'Criação'
        WHEN 'UPDATE' THEN 'Atualização'
        WHEN 'DELETE' THEN 'Exclusão'
        WHEN 'LOGIN' THEN 'Login'
        WHEN 'LOGOUT' THEN 'Logout'
        WHEN 'ACCESS' THEN 'Acesso'
        WHEN 'EXPORT' THEN 'Exportação'
        WHEN 'IMPORT' THEN 'Importação'
        WHEN 'BACKUP' THEN 'Backup'
        WHEN 'RESTORE' THEN 'Restauração'
        ELSE al.action
    END as action_description
FROM audit_log al
LEFT JOIN auth_user u ON al.user_id = u.id
ORDER BY al.created_at DESC;

-- Procedure para limpar logs antigos
DELIMITER //

CREATE PROCEDURE sp_cleanup_audit_logs(IN days_to_keep INT)
BEGIN
    DELETE FROM audit_log 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    SELECT ROW_COUNT() as deleted_rows;
END//

DELIMITER ;

-- Procedure para estatísticas de auditoria
DELIMITER //

CREATE PROCEDURE sp_audit_statistics(IN days_back INT)
BEGIN
    SELECT 
        action,
        COUNT(*) as total,
        DATE(created_at) as date
    FROM audit_log
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL days_back DAY)
    GROUP BY action, DATE(created_at)
    ORDER BY date DESC, total DESC;
END//

DELIMITER ;
