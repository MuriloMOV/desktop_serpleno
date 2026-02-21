-- ============================================================
-- MySQL Workbench Forward Engineering - Ser Pleno
-- Script otimizado e corrigido para MySQL 8.0+
-- ============================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema ser_pleno
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `ser_pleno` 
  DEFAULT CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;
USE `ser_pleno`;

-- ============================================================
-- TABELAS DE AUTENTICAÇÃO (Django)
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_user`
-- Usuários do sistema
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `password` VARCHAR(128) NOT NULL COMMENT 'Hash da senha',
  `last_login` DATETIME(6) NULL COMMENT 'Último login',
  `is_superuser` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'É superusuário',
  `username` VARCHAR(150) NOT NULL COMMENT 'Nome de usuário',
  `first_name` VARCHAR(150) NOT NULL DEFAULT '' COMMENT 'Primeiro nome',
  `last_name` VARCHAR(150) NOT NULL DEFAULT '' COMMENT 'Sobrenome',
  `email` VARCHAR(254) NOT NULL DEFAULT '' COMMENT 'E-mail',
  `is_staff` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Pode acessar admin',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Usuário ativo',
  `date_joined` DATETIME(6) NOT NULL COMMENT 'Data de cadastro',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_username` (`username` ASC),
  INDEX `idx_email` (`email` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Usuários do sistema';

-- -----------------------------------------------------
-- Table `ser_pleno`.`django_content_type`
-- Tipos de conteúdo para permissões
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_content_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `app_label` VARCHAR(100) NOT NULL COMMENT 'Nome da aplicação',
  `model` VARCHAR(100) NOT NULL COMMENT 'Nome do modelo',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_app_model` (`app_label` ASC, `model` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Tipos de conteúdo';

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_permission`
-- Permissões do sistema
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_permission` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL COMMENT 'Nome da permissão',
  `content_type_id` INT NOT NULL COMMENT 'Referência ao tipo de conteúdo',
  `codename` VARCHAR(100) NOT NULL COMMENT 'Código da permissão',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_content_codename` (`content_type_id` ASC, `codename` ASC),
  INDEX `idx_content_type` (`content_type_id` ASC),
  CONSTRAINT `fk_auth_permission_content_type`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `ser_pleno`.`django_content_type` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Permissões do sistema';

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_group`
-- Grupos de usuários
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_group` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL COMMENT 'Nome do grupo',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_name` (`name` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Grupos de usuários';

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_group_permissions`
-- Permissões por grupo
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_group_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL COMMENT 'Referência ao grupo',
  `permission_id` INT NOT NULL COMMENT 'Referência à permissão',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_group_permission` (`group_id` ASC, `permission_id` ASC),
  INDEX `idx_group` (`group_id` ASC),
  INDEX `idx_permission` (`permission_id` ASC),
  CONSTRAINT `fk_auth_group_permissions_group`
    FOREIGN KEY (`group_id`)
    REFERENCES `ser_pleno`.`auth_group` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_auth_group_permissions_permission`
    FOREIGN KEY (`permission_id`)
    REFERENCES `ser_pleno`.`auth_permission` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Permissões por grupo';

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_user_groups`
-- Grupos por usuário
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_user_groups` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL COMMENT 'Referência ao usuário',
  `group_id` INT NOT NULL COMMENT 'Referência ao grupo',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user_group` (`user_id` ASC, `group_id` ASC),
  INDEX `idx_user` (`user_id` ASC),
  INDEX `idx_group` (`group_id` ASC),
  CONSTRAINT `fk_auth_user_groups_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_auth_user_groups_group`
    FOREIGN KEY (`group_id`)
    REFERENCES `ser_pleno`.`auth_group` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Grupos por usuário';

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_user_user_permissions`
-- Permissões diretas por usuário
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_user_user_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL COMMENT 'Referência ao usuário',
  `permission_id` INT NOT NULL COMMENT 'Referência à permissão',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user_permission` (`user_id` ASC, `permission_id` ASC),
  INDEX `idx_user` (`user_id` ASC),
  INDEX `idx_permission` (`permission_id` ASC),
  CONSTRAINT `fk_auth_user_user_permissions_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_auth_user_user_permissions_permission`
    FOREIGN KEY (`permission_id`)
    REFERENCES `ser_pleno`.`auth_permission` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Permissões diretas por usuário';

-- -----------------------------------------------------
-- Table `ser_pleno`.`user_profile`
-- Perfis de usuário estendidos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`user_profile` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL COMMENT 'Referência ao usuário',
  `role` VARCHAR(50) NOT NULL DEFAULT 'visitante' COMMENT 'Papel do usuário',
  `permissions` JSON NULL COMMENT 'Permissões adicionais em JSON',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user` (`user_id` ASC),
  INDEX `idx_role` (`role` ASC),
  CONSTRAINT `fk_user_profile_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Perfis de usuário estendidos';

-- ============================================================
-- TABELAS DE CONFIGURAÇÃO DJANGO
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`django_migrations`
-- Histórico de migrações Django
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_migrations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `app` VARCHAR(255) NOT NULL COMMENT 'Nome da aplicação',
  `name` VARCHAR(255) NOT NULL COMMENT 'Nome da migração',
  `applied` DATETIME(6) NOT NULL COMMENT 'Data de aplicação',
  PRIMARY KEY (`id`),
  INDEX `idx_app` (`app` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico de migrações Django';

-- -----------------------------------------------------
-- Table `ser_pleno`.`django_session`
-- Sessões de usuário
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_session` (
  `session_key` VARCHAR(40) NOT NULL COMMENT 'Chave da sessão',
  `session_data` LONGTEXT NOT NULL COMMENT 'Dados da sessão',
  `expire_date` DATETIME(6) NOT NULL COMMENT 'Data de expiração',
  PRIMARY KEY (`session_key`),
  INDEX `idx_expire_date` (`expire_date` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Sessões de usuário';

-- -----------------------------------------------------
-- Table `ser_pleno`.`django_admin_log`
-- Log de ações administrativas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_admin_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `action_time` DATETIME(6) NOT NULL COMMENT 'Data/hora da ação',
  `object_id` LONGTEXT NULL COMMENT 'ID do objeto afetado',
  `object_repr` VARCHAR(200) NOT NULL COMMENT 'Representação do objeto',
  `action_flag` SMALLINT UNSIGNED NOT NULL COMMENT 'Tipo de ação',
  `change_message` LONGTEXT NOT NULL COMMENT 'Mensagem de alteração',
  `content_type_id` INT NULL COMMENT 'Referência ao tipo de conteúdo',
  `user_id` INT NOT NULL COMMENT 'Referência ao usuário',
  PRIMARY KEY (`id`),
  INDEX `idx_content_type` (`content_type_id` ASC),
  INDEX `idx_user` (`user_id` ASC),
  CONSTRAINT `fk_django_admin_log_content_type`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `ser_pleno`.`django_content_type` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_django_admin_log_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Log de ações administrativas';

-- ============================================================
-- TABELAS PRINCIPAIS DO SISTEMA
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`aluno`
-- Cadastro de alunos/atendidos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`aluno` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NOT NULL COMMENT 'Nome completo',
  `sala` VARCHAR(45) NULL COMMENT 'Sala/Turma',
  `curso` VARCHAR(200) NULL COMMENT 'Curso',
  `professor_responsavel` VARCHAR(200) NOT NULL COMMENT 'Professor responsável',
  `user_id` INT NULL COMMENT 'Referência ao usuário',
  `attention_reason` LONGTEXT NULL COMMENT 'Motivo de atenção',
  `emergency_contact` VARCHAR(100) NULL COMMENT 'Contato de emergência',
  `emergency_phone` VARCHAR(20) NULL COMMENT 'Telefone de emergência',
  `enrollment_date` DATE NULL COMMENT 'Data de matrícula',
  `general_notes` LONGTEXT NULL COMMENT 'Observações gerais',
  `has_medical_report` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Possui laudo médico',
  `last_contact_date` DATE NULL COMMENT 'Data do último contato',
  `phone` VARCHAR(20) NULL COMMENT 'Telefone',
  `priority_level` INT NOT NULL DEFAULT 0 COMMENT 'Nível de prioridade',
  `requires_attention` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Requer atenção',
  `tags` JSON NULL COMMENT 'Tags em JSON',
  `age` INT NULL COMMENT 'Idade',
  `status` VARCHAR(20) NOT NULL DEFAULT 'ativo' COMMENT 'Status do aluno',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user` (`user_id` ASC),
  INDEX `idx_status` (`status` ASC),
  INDEX `idx_priority` (`priority_level` ASC),
  INDEX `idx_nome` (`nome` ASC),
  CONSTRAINT `fk_aluno_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Cadastro de alunos/atendidos';

-- -----------------------------------------------------
-- Table `ser_pleno`.`analista`
-- Cadastro de analistas/psicólogos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`analista` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NOT NULL COMMENT 'Nome completo',
  `email` VARCHAR(255) NOT NULL COMMENT 'E-mail',
  `user_id` INT NOT NULL COMMENT 'Referência ao usuário',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user` (`user_id` ASC),
  UNIQUE INDEX `uk_email` (`email` ASC),
  CONSTRAINT `fk_analista_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Cadastro de analistas/psicólogos';

-- -----------------------------------------------------
-- Table `ser_pleno`.`coordenacao`
-- Cadastro de coordenadores
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`coordenacao` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NOT NULL COMMENT 'Nome completo',
  `email` VARCHAR(255) NOT NULL COMMENT 'E-mail',
  `user_id` INT NOT NULL COMMENT 'Referência ao usuário',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user` (`user_id` ASC),
  UNIQUE INDEX `uk_email` (`email` ASC),
  CONSTRAINT `fk_coordenacao_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Cadastro de coordenadores';

-- ============================================================
-- TABELAS DE AGENDAMENTO
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_appointment`
-- Agendamentos do desktop
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_appointment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `time` INT NULL COMMENT 'Horário em minutos',
  `date` DATE NOT NULL COMMENT 'Data do agendamento',
  `status` VARCHAR(20) NOT NULL DEFAULT 'scheduled' COMMENT 'Status do agendamento',
  `notes` TEXT NULL COMMENT 'Observações',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  PRIMARY KEY (`id`),
  INDEX `idx_student_date` (`student_id` ASC, `date` ASC),
  INDEX `idx_date_status` (`date` ASC, `status` ASC),
  CONSTRAINT `fk_desktop_appointment_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Agendamentos do desktop';

-- -----------------------------------------------------
-- Table `ser_pleno`.`agendamento`
-- Agendamentos (sistema legado)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`agendamento` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NULL COMMENT 'Nome do agendamento',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `data_hora` DATETIME(6) NOT NULL COMMENT 'Data e hora',
  `motivo` LONGTEXT NOT NULL COMMENT 'Motivo do agendamento',
  `status` VARCHAR(20) NOT NULL DEFAULT 'scheduled' COMMENT 'Status',
  `local` VARCHAR(200) NULL COMMENT 'Local',
  `profissional` VARCHAR(200) NULL COMMENT 'Profissional responsável',
  `laudo` VARCHAR(255) NULL COMMENT 'Laudo/Relatório',
  `origem` VARCHAR(20) NULL COMMENT 'Origem do agendamento',
  `desktop_appointment_id` BIGINT NULL COMMENT 'Referência ao agendamento desktop',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  PRIMARY KEY (`id`),
  INDEX `idx_student` (`student_id` ASC),
  INDEX `idx_data_hora` (`data_hora` ASC),
  INDEX `idx_status` (`status` ASC),
  INDEX `idx_data_status` (`data_hora` ASC, `status` ASC),
  CONSTRAINT `fk_agendamento_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_agendamento_desktop_appointment`
    FOREIGN KEY (`desktop_appointment_id`)
    REFERENCES `ser_pleno`.`desktop_appointment` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Agendamentos (sistema legado)';

-- -----------------------------------------------------
-- Table `ser_pleno`.`disponibilidade`
-- Disponibilidade de horários dos analistas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`disponibilidade` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `dias` VARCHAR(45) NULL COMMENT 'Dias disponíveis',
  `horario` TIME NOT NULL COMMENT 'Horário',
  `analista_id` INT NULL COMMENT 'Referência ao analista',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Disponibilidade ativa',
  PRIMARY KEY (`id`),
  INDEX `idx_analista` (`analista_id` ASC),
  INDEX `idx_horario` (`horario` ASC),
  CONSTRAINT `fk_disponibilidade_analista`
    FOREIGN KEY (`analista_id`)
    REFERENCES `ser_pleno`.`analista` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Disponibilidade de horários dos analistas';

-- ============================================================
-- TABELAS DE INTERVENÇÃO E TRIAGEM
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_screeningform`
-- Formulários de triagem
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_screeningform` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL COMMENT 'Nome do formulário',
  `description` LONGTEXT NOT NULL COMMENT 'Descrição',
  `questions` JSON NOT NULL COMMENT 'Questões em JSON',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Formulário ativo',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `created_by_id` INT NULL COMMENT 'Criado por',
  PRIMARY KEY (`id`),
  INDEX `idx_active_created` (`is_active` ASC, `created_at` ASC),
  CONSTRAINT `fk_desktop_screeningform_created_by`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Formulários de triagem';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_screening`
-- Triagens realizadas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_screening` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `status` VARCHAR(20) NOT NULL DEFAULT 'pendente' COMMENT 'Status da triagem',
  `priority` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT 'Prioridade',
  `scheduled_date` DATE NULL COMMENT 'Data agendada',
  `completed_date` DATE NULL COMMENT 'Data de conclusão',
  `responses` JSON NOT NULL COMMENT 'Respostas em JSON',
  `score` INT NULL COMMENT 'Pontuação',
  `observations` LONGTEXT NOT NULL COMMENT 'Observações',
  `recommendations` LONGTEXT NOT NULL COMMENT 'Recomendações',
  `requires_followup` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Requer acompanhamento',
  `followup_date` DATE NULL COMMENT 'Data de acompanhamento',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `conducted_by_id` INT NULL COMMENT 'Realizado por',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `form_id` BIGINT NOT NULL COMMENT 'Referência ao formulário',
  PRIMARY KEY (`id`),
  INDEX `idx_student_status` (`student_id` ASC, `status` ASC),
  INDEX `idx_scheduled_date` (`scheduled_date` ASC),
  INDEX `idx_priority_status` (`priority` ASC, `status` ASC),
  CONSTRAINT `fk_desktop_screening_conducted_by`
    FOREIGN KEY (`conducted_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_screening_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_screening_form`
    FOREIGN KEY (`form_id`)
    REFERENCES `ser_pleno`.`desktop_screeningform` (`id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Triagens realizadas';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_intervention`
-- Intervenções realizadas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_intervention` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `date` DATE NOT NULL COMMENT 'Data da intervenção',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `conducted_by_id` INT NULL COMMENT 'Realizado por',
  `duration_minutes` INT NULL COMMENT 'Duração em minutos',
  `follow_up_completed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Acompanhamento concluído',
  `follow_up_date` DATE NULL COMMENT 'Data de acompanhamento',
  `follow_up_required` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Requer acompanhamento',
  `intervention_notes` LONGTEXT NOT NULL COMMENT 'Notas da intervenção',
  `intervention_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de intervenção',
  `is_confidential` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Confidencial',
  `outcome` VARCHAR(50) NOT NULL COMMENT 'Resultado',
  `outcome_notes` LONGTEXT NOT NULL COMMENT 'Notas do resultado',
  `tags` JSON NULL COMMENT 'Tags em JSON',
  PRIMARY KEY (`id`),
  INDEX `idx_student_date` (`student_id` ASC, `date` ASC),
  INDEX `idx_date` (`date` ASC),
  INDEX `idx_intervention_type` (`intervention_type` ASC),
  INDEX `idx_follow_up` (`follow_up_required` ASC, `follow_up_date` ASC),
  INDEX `idx_outcome` (`outcome` ASC),
  CONSTRAINT `fk_desktop_intervention_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_intervention_conducted_by`
    FOREIGN KEY (`conducted_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Intervenções realizadas';

-- ============================================================
-- TABELAS DE NOTAS E DOCUMENTOS
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_note`
-- Notas e anotações
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_note` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `title` VARCHAR(200) NOT NULL COMMENT 'Título',
  `content` LONGTEXT NOT NULL COMMENT 'Conteúdo',
  `note_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de nota',
  `is_private` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Nota privada',
  `is_pinned` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Nota fixada',
  `tags` JSON NULL COMMENT 'Tags em JSON',
  `created_by_id` INT NULL COMMENT 'Criado por',
  `related_intervention_id` BIGINT NULL COMMENT 'Intervenção relacionada',
  `related_screening_id` BIGINT NULL COMMENT 'Triagem relacionada',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_student_created` (`student_id` ASC, `created_at` ASC),
  INDEX `idx_note_type` (`note_type` ASC, `created_at` ASC),
  INDEX `idx_created_by` (`created_by_id` ASC, `created_at` ASC),
  INDEX `idx_pinned` (`is_pinned` ASC, `created_at` ASC),
  CONSTRAINT `fk_desktop_note_created_by`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_note_intervention`
    FOREIGN KEY (`related_intervention_id`)
    REFERENCES `ser_pleno`.`desktop_intervention` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_note_screening`
    FOREIGN KEY (`related_screening_id`)
    REFERENCES `ser_pleno`.`desktop_screening` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_note_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Notas e anotações';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_document`
-- Documentos anexados
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_document` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `title` VARCHAR(200) NOT NULL COMMENT 'Título',
  `description` LONGTEXT NOT NULL COMMENT 'Descrição',
  `document_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de documento',
  `file` VARCHAR(500) NOT NULL COMMENT 'Caminho do arquivo',
  `file_name` VARCHAR(255) NOT NULL COMMENT 'Nome do arquivo',
  `file_size` INT NULL COMMENT 'Tamanho do arquivo em bytes',
  `mime_type` VARCHAR(100) NOT NULL COMMENT 'Tipo MIME',
  `issue_date` DATE NULL COMMENT 'Data de emissão',
  `expiry_date` DATE NULL COMMENT 'Data de validade',
  `is_confidential` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Documento confidencial',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `uploaded_by_id` INT NULL COMMENT 'Enviado por',
  PRIMARY KEY (`id`),
  INDEX `idx_student_created` (`student_id` ASC, `created_at` ASC),
  INDEX `idx_document_type` (`document_type` ASC),
  INDEX `idx_expiry_date` (`expiry_date` ASC),
  CONSTRAINT `fk_desktop_document_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_document_uploaded_by`
    FOREIGN KEY (`uploaded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Documentos anexados';

-- ============================================================
-- TABELAS DE METAS E OBJETIVOS
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_goal`
-- Metas dos alunos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_goal` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `title` VARCHAR(200) NOT NULL COMMENT 'Título da meta',
  `description` LONGTEXT NOT NULL COMMENT 'Descrição',
  `category` VARCHAR(50) NOT NULL COMMENT 'Categoria',
  `priority` VARCHAR(20) NOT NULL DEFAULT 'media' COMMENT 'Prioridade',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pendente' COMMENT 'Status',
  `target_date` DATE NULL COMMENT 'Data alvo',
  `completed_date` DATE NULL COMMENT 'Data de conclusão',
  `progress_percentage` INT NOT NULL DEFAULT 0 COMMENT 'Percentual de progresso',
  `notes` LONGTEXT NOT NULL COMMENT 'Notas',
  `success_criteria` LONGTEXT NOT NULL COMMENT 'Critérios de sucesso',
  `created_by_id` INT NULL COMMENT 'Criado por',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_student_status` (`student_id` ASC, `status` ASC),
  INDEX `idx_category_status` (`category` ASC, `status` ASC),
  INDEX `idx_target_date` (`target_date` ASC),
  INDEX `idx_priority_status` (`priority` ASC, `status` ASC),
  CONSTRAINT `fk_desktop_goal_created_by`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_goal_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Metas dos alunos';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_goalprogress`
-- Progresso das metas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_goalprogress` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `percentage` INT NOT NULL COMMENT 'Percentual',
  `notes` LONGTEXT NOT NULL COMMENT 'Notas',
  `recorded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de registro',
  `goal_id` BIGINT NOT NULL COMMENT 'Referência à meta',
  `recorded_by_id` INT NULL COMMENT 'Registrado por',
  PRIMARY KEY (`id`),
  INDEX `idx_goal` (`goal_id` ASC),
  CONSTRAINT `fk_desktop_goalprogress_goal`
    FOREIGN KEY (`goal_id`)
    REFERENCES `ser_pleno`.`desktop_goal` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_goalprogress_recorded_by`
    FOREIGN KEY (`recorded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Progresso das metas';

-- ============================================================
-- TABELAS DE BEM-ESTAR E HUMOR
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_moodentry`
-- Registros de humor
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_moodentry` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `mood_level` INT NOT NULL COMMENT 'Nível de humor (1-5)',
  `mood_emoji` VARCHAR(10) NOT NULL COMMENT 'Emoji do humor',
  `energy_level` INT NULL COMMENT 'Nível de energia',
  `stress_level` INT NULL COMMENT 'Nível de estresse',
  `sleep_quality` INT NULL COMMENT 'Qualidade do sono',
  `notes` LONGTEXT NOT NULL COMMENT 'Notas',
  `triggers` JSON NULL COMMENT 'Gatilhos em JSON',
  `activities` JSON NULL COMMENT 'Atividades em JSON',
  `entry_date` DATE NOT NULL COMMENT 'Data do registro',
  `entry_time` TIME NULL COMMENT 'Hora do registro',
  `recorded_by_id` INT NULL COMMENT 'Registrado por',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_student_date` (`student_id` ASC, `entry_date` ASC),
  INDEX `idx_mood_date` (`mood_level` ASC, `entry_date` ASC),
  CONSTRAINT `fk_desktop_moodentry_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_moodentry_recorded_by`
    FOREIGN KEY (`recorded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Registros de humor';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_wellnesscheckin`
-- Check-ins de bem-estar
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_wellnesscheckin` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `check_in_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de check-in',
  `check_in_date` DATE NOT NULL COMMENT 'Data do check-in',
  `overall_wellbeing` INT NOT NULL COMMENT 'Bem-estar geral',
  `responses` JSON NOT NULL COMMENT 'Respostas em JSON',
  `attention_areas` JSON NOT NULL COMMENT 'Áreas de atenção em JSON',
  `recommendations` LONGTEXT NOT NULL COMMENT 'Recomendações',
  `follow_up_needed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Necessita acompanhamento',
  `follow_up_date` DATE NULL COMMENT 'Data de acompanhamento',
  `professional_notes` LONGTEXT NOT NULL COMMENT 'Notas profissionais',
  `conducted_by_id` INT NULL COMMENT 'Realizado por',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_student_date` (`student_id` ASC, `check_in_date` ASC),
  INDEX `idx_type_date` (`check_in_type` ASC, `check_in_date` ASC),
  INDEX `idx_follow_up` (`follow_up_needed` ASC, `follow_up_date` ASC),
  CONSTRAINT `fk_desktop_wellnesscheckin_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_wellnesscheckin_conducted_by`
    FOREIGN KEY (`conducted_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Check-ins de bem-estar';

-- ============================================================
-- TABELAS DE ORIENTAÇÕES
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_orientation`
-- Orientações profissionais
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_orientation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `title` VARCHAR(255) NOT NULL COMMENT 'Título',
  `theme` VARCHAR(120) NOT NULL COMMENT 'Tema',
  `session_date` DATE NULL COMMENT 'Data da sessão',
  `content` LONGTEXT NOT NULL COMMENT 'Conteúdo',
  `is_markdown` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Conteúdo em Markdown',
  `motivational_message` LONGTEXT NOT NULL COMMENT 'Mensagem motivacional',
  `action_plan` JSON NOT NULL COMMENT 'Plano de ação em JSON',
  `psychologist_id` INT NULL COMMENT 'Psicólogo responsável',
  `student_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_student` (`student_id` ASC),
  CONSTRAINT `fk_desktop_orientation_psychologist`
    FOREIGN KEY (`psychologist_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_orientation_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Orientações profissionais';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_orientationattachment`
-- Anexos das orientações
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_orientationattachment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `file` VARCHAR(100) NOT NULL COMMENT 'Caminho do arquivo',
  `file_name` VARCHAR(255) NOT NULL COMMENT 'Nome do arquivo',
  `mime_type` VARCHAR(100) NOT NULL COMMENT 'Tipo MIME',
  `orientation_id` BIGINT NOT NULL COMMENT 'Referência à orientação',
  `uploaded_by_id` INT NULL COMMENT 'Enviado por',
  PRIMARY KEY (`id`),
  INDEX `idx_orientation` (`orientation_id` ASC),
  CONSTRAINT `fk_desktop_orientationattachment_orientation`
    FOREIGN KEY (`orientation_id`)
    REFERENCES `ser_pleno`.`desktop_orientation` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_orientationattachment_uploaded_by`
    FOREIGN KEY (`uploaded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Anexos das orientações';

-- ============================================================
-- TABELAS DE ALERTAS E MENSAGENS
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_alert`
-- Alertas do sistema
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_alert` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `alert_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de alerta',
  `severity` VARCHAR(20) NOT NULL COMMENT 'Severidade',
  `message` LONGTEXT NOT NULL COMMENT 'Mensagem',
  `details` JSON NOT NULL COMMENT 'Detalhes em JSON',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Lido',
  `is_resolved` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Resolvido',
  `resolved_at` DATETIME(6) NULL COMMENT 'Data de resolução',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `assigned_to_id` INT NULL COMMENT 'Atribuído a',
  `resolved_by_id` INT NULL COMMENT 'Resolvido por',
  `student_id` INT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_read_resolved` (`is_read` ASC, `is_resolved` ASC),
  INDEX `idx_type_severity` (`alert_type` ASC, `severity` ASC),
  INDEX `idx_assigned_resolved` (`assigned_to_id` ASC, `is_resolved` ASC),
  CONSTRAINT `fk_desktop_alert_assigned_to`
    FOREIGN KEY (`assigned_to_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_alert_resolved_by`
    FOREIGN KEY (`resolved_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_alert_student`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Alertas do sistema';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_message`
-- Mensagens entre usuários
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_message` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `sender_id` INT NULL COMMENT 'Remetente',
  `text` LONGTEXT NOT NULL COMMENT 'Texto da mensagem',
  `timestamp` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data/hora',
  `read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Lida',
  `caminho_arquivo` VARCHAR(500) NULL COMMENT 'Caminho do arquivo anexo',
  `tipo_arquivo` VARCHAR(50) NULL COMMENT 'Tipo do arquivo anexo',
  `recipient_id` INT NULL COMMENT 'Destinatário',
  PRIMARY KEY (`id`),
  INDEX `idx_sender_recipient_time` (`sender_id` ASC, `recipient_id` ASC, `timestamp` ASC),
  INDEX `idx_recipient_read` (`recipient_id` ASC, `read` ASC),
  CONSTRAINT `fk_desktop_message_sender`
    FOREIGN KEY (`sender_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_desktop_message_recipient`
    FOREIGN KEY (`recipient_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Mensagens entre usuários';

-- ============================================================
-- TABELAS DE RELATÓRIOS
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_reporttemplate`
-- Templates de relatórios
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_reporttemplate` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL COMMENT 'Nome do template',
  `report_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de relatório',
  `description` LONGTEXT NOT NULL COMMENT 'Descrição',
  `template_config` JSON NOT NULL COMMENT 'Configuração do template em JSON',
  `default_parameters` JSON NOT NULL COMMENT 'Parâmetros padrão em JSON',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Template ativo',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `created_by_id` INT NULL COMMENT 'Criado por',
  PRIMARY KEY (`id`),
  INDEX `idx_type_active` (`report_type` ASC, `is_active` ASC),
  CONSTRAINT `fk_desktop_reporttemplate_created_by`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Templates de relatórios';

-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_report`
-- Relatórios gerados
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_report` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL COMMENT 'Nome do relatório',
  `report_type` VARCHAR(50) NOT NULL COMMENT 'Tipo de relatório',
  `format` VARCHAR(20) NOT NULL COMMENT 'Formato (PDF, XLSX, etc)',
  `generated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de geração',
  `parameters` JSON NOT NULL COMMENT 'Parâmetros em JSON',
  `data` JSON NOT NULL COMMENT 'Dados em JSON',
  `file_path` VARCHAR(500) NOT NULL COMMENT 'Caminho do arquivo',
  `file_size` INT NULL COMMENT 'Tamanho do arquivo em bytes',
  `is_public` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Relatório público',
  `expires_at` DATETIME(6) NULL COMMENT 'Data de expiração',
  `generated_by_id` INT NULL COMMENT 'Gerado por',
  PRIMARY KEY (`id`),
  INDEX `idx_type_generated` (`report_type` ASC, `generated_at` ASC),
  INDEX `idx_generated_by` (`generated_by_id` ASC, `generated_at` ASC),
  CONSTRAINT `fk_desktop_report_generated_by`
    FOREIGN KEY (`generated_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Relatórios gerados';

-- ============================================================
-- TABELAS DE GAMIFICAÇÃO
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`badge`
-- Conquistas/Badges
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`badge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(100) NOT NULL COMMENT 'Chave única',
  `title` VARCHAR(255) NOT NULL COMMENT 'Título',
  `icon` VARCHAR(100) NULL COMMENT 'Ícone',
  `description` LONGTEXT NULL COMMENT 'Descrição',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_key` (`key` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Conquistas/Badges';

-- -----------------------------------------------------
-- Table `ser_pleno`.`challenge`
-- Desafios
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`challenge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(100) NOT NULL COMMENT 'Chave única',
  `title` VARCHAR(255) NOT NULL COMMENT 'Título',
  `description` LONGTEXT NULL COMMENT 'Descrição',
  `xp` INT NOT NULL DEFAULT 0 COMMENT 'Pontos de experiência',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_key` (`key` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Desafios';

-- -----------------------------------------------------
-- Table `ser_pleno`.`gamificacao`
-- Dados de gamificação dos alunos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`gamificacao` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `pontos_atuais` INT NOT NULL DEFAULT 0 COMMENT 'Pontos atuais',
  `nivel` INT NOT NULL DEFAULT 1 COMMENT 'Nível atual',
  `conquistas` VARCHAR(100) NOT NULL DEFAULT '' COMMENT 'Conquistas',
  `check_in` INT NOT NULL DEFAULT 0 COMMENT 'Check-ins consecutivos',
  `metas_pessoais` VARCHAR(100) NOT NULL DEFAULT '' COMMENT 'Metas pessoais',
  `last_check_in_date` DATE NULL COMMENT 'Data do último check-in',
  `aluno_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_aluno` (`aluno_id` ASC),
  CONSTRAINT `fk_gamificacao_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Dados de gamificação dos alunos';

-- -----------------------------------------------------
-- Table `ser_pleno`.`autoavaliacao`
-- Autoavaliações dos alunos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`autoavaliacao` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `data_avaliacao` DATE NULL COMMENT 'Data da avaliação',
  `bem_estar_academico` VARCHAR(255) NULL COMMENT 'Bem-estar acadêmico',
  `bem_estar_emocional` VARCHAR(255) NULL COMMENT 'Bem-estar emocional',
  `bem_estar_social` VARCHAR(255) NULL COMMENT 'Bem-estar social',
  `reflexoes_pessoais` LONGTEXT NULL COMMENT 'Reflexões pessoais',
  `pontos_xp` INT NULL DEFAULT 0 COMMENT 'Pontos de experiência',
  `aluno_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_aluno` (`aluno_id` ASC),
  CONSTRAINT `fk_autoavaliacao_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Autoavaliações dos alunos';

-- ============================================================
-- TABELAS DE HISTÓRICO E REGISTROS
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`meu_historico`
-- Histórico dos alunos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`meu_historico` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `humor_media` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Média de humor',
  `dias_consecutivos` INT NOT NULL DEFAULT 0 COMMENT 'Dias consecutivos',
  `total_registros` INT NOT NULL DEFAULT 0 COMMENT 'Total de registros',
  `aluno_id` INT NOT NULL COMMENT 'Referência ao aluno',
  PRIMARY KEY (`id`),
  INDEX `idx_aluno` (`aluno_id` ASC),
  CONSTRAINT `fk_meu_historico_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Histórico dos alunos';

-- -----------------------------------------------------
-- Table `ser_pleno`.`registros_diarios`
-- Registros diários de humor
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`registros_diarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `data_registro` DATE NULL COMMENT 'Data do registro',
  `humor` VARCHAR(50) NULL COMMENT 'Humor registrado',
  `historico_id` INT NULL COMMENT 'Referência ao histórico',
  PRIMARY KEY (`id`),
  INDEX `idx_historico` (`historico_id` ASC),
  CONSTRAINT `fk_registros_diarios_historico`
    FOREIGN KEY (`historico_id`)
    REFERENCES `ser_pleno`.`meu_historico` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Registros diários de humor';

-- ============================================================
-- TABELAS DE COMUNICAÇÃO
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`mensagens`
-- Mensagens do sistema legado
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`mensagens` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `remetente` VARCHAR(255) NULL COMMENT 'Remetente',
  `titulo` VARCHAR(255) NULL COMMENT 'Título',
  `conteudo` LONGTEXT NULL COMMENT 'Conteúdo',
  `lida` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Mensagem lida',
  `data_envio` DATE NULL COMMENT 'Data de envio',
  `aluno_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `agendamento_id` BIGINT NULL COMMENT 'Referência ao agendamento',
  `tipo` VARCHAR(50) NOT NULL DEFAULT 'geral' COMMENT 'Tipo de mensagem',
  PRIMARY KEY (`id`),
  INDEX `idx_aluno` (`aluno_id` ASC),
  CONSTRAINT `fk_mensagens_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_mensagens_agendamento`
    FOREIGN KEY (`agendamento_id`)
    REFERENCES `ser_pleno`.`agendamento` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Mensagens do sistema legado';

-- -----------------------------------------------------
-- Table `ser_pleno`.`help_requests`
-- Pedidos de ajuda
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`help_requests` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `tipo` VARCHAR(50) NOT NULL COMMENT 'Tipo de pedido',
  `mensagem` LONGTEXT NULL COMMENT 'Mensagem',
  `prioridade` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT 'Prioridade',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pendente' COMMENT 'Status',
  `localizacao` VARCHAR(100) NULL COMMENT 'Localização',
  `dados_extras` JSON NULL COMMENT 'Dados extras em JSON',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `viewed_at` DATETIME(6) NULL COMMENT 'Data de visualização',
  `resolved_at` DATETIME(6) NULL COMMENT 'Data de resolução',
  `aluno_id` INT NOT NULL COMMENT 'Referência ao aluno',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  PRIMARY KEY (`id`),
  INDEX `idx_aluno` (`aluno_id` ASC),
  CONSTRAINT `fk_help_requests_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Pedidos de ajuda';

-- -----------------------------------------------------
-- Table `ser_pleno`.`mural_posts`
-- Posts do mural
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`mural_posts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data de criação',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Data de atualização',
  `titulo` VARCHAR(255) NOT NULL COMMENT 'Título',
  `conteudo` LONGTEXT NOT NULL COMMENT 'Conteúdo',
  `autor` VARCHAR(150) NULL COMMENT 'Autor',
  `publicado_em` DATETIME(6) NOT NULL COMMENT 'Data de publicação',
  `ativo` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Post ativo',
  `categoria` VARCHAR(20) NOT NULL DEFAULT 'geral' COMMENT 'Categoria',
  `data_agendamento` DATETIME(6) NULL COMMENT 'Data de agendamento',
  `link_externo` VARCHAR(200) NULL COMMENT 'Link externo',
  `blocos` JSON NULL COMMENT 'Blocos de conteúdo em JSON',
  `layout` VARCHAR(20) NOT NULL DEFAULT 'padrao' COMMENT 'Layout',
  `horario_evento` DATETIME(6) NULL COMMENT 'Horário do evento',
  `local_fisico` VARCHAR(200) NULL COMMENT 'Local físico',
  PRIMARY KEY (`id`),
  INDEX `idx_ativo_publicado` (`ativo` ASC, `publicado_em` ASC),
  INDEX `idx_categoria` (`categoria` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Posts do mural';

-- ============================================================
-- TABELAS DE RECURSOS E ESTÁTICOS
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`guided_resource`
-- Recursos guiados
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`guided_resource` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(100) NULL COMMENT 'Chave única',
  `title` VARCHAR(255) NOT NULL COMMENT 'Título',
  `icon` VARCHAR(100) NULL COMMENT 'Ícone',
  `duration` VARCHAR(50) NULL COMMENT 'Duração',
  `category` VARCHAR(100) NULL COMMENT 'Categoria',
  `content` LONGTEXT NULL COMMENT 'Conteúdo',
  `video_url` VARCHAR(200) NULL COMMENT 'URL do vídeo',
  `share_url` VARCHAR(200) NULL COMMENT 'URL de compartilhamento',
  PRIMARY KEY (`id`),
  INDEX `idx_key` (`key` ASC),
  INDEX `idx_category` (`category` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Recursos guiados';

-- -----------------------------------------------------
-- Table `ser_pleno`.`static_avatar`
-- Avatares disponíveis
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`static_avatar` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `filename` VARCHAR(100) NOT NULL COMMENT 'Nome do arquivo',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_filename` (`filename` ASC)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Avatares disponíveis';

-- ============================================================
-- TABELA DE AUDITORIA
-- ============================================================

-- -----------------------------------------------------
-- Table `ser_pleno`.`audit_log`
-- Log de auditoria do sistema
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`audit_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `table_name` VARCHAR(100) NOT NULL COMMENT 'Nome da tabela afetada',
  `record_id` BIGINT NULL COMMENT 'ID do registro afetado',
  `action` VARCHAR(20) NOT NULL COMMENT 'Tipo de ação: CREATE, UPDATE, DELETE, LOGIN, etc.',
  `old_values` JSON NULL COMMENT 'Valores anteriores (para UPDATE/DELETE)',
  `new_values` JSON NULL COMMENT 'Novos valores (para CREATE/UPDATE)',
  `user_id` INT NULL COMMENT 'ID do usuário que fez a ação',
  `username` VARCHAR(150) NULL COMMENT 'Nome de usuário',
  `ip_address` VARCHAR(45) NULL COMMENT 'Endereço IP',
  `user_agent` VARCHAR(500) NULL COMMENT 'User agent do navegador',
  `details` TEXT NULL COMMENT 'Detalhes adicionais',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Data/hora da ação',
  PRIMARY KEY (`id`),
  INDEX `idx_table_record` (`table_name` ASC, `record_id` ASC),
  INDEX `idx_user` (`user_id` ASC),
  INDEX `idx_action` (`action` ASC),
  INDEX `idx_created` (`created_at` ASC),
  INDEX `idx_username` (`username` ASC),
  CONSTRAINT `fk_audit_log_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Log de auditoria do sistema';

-- ============================================================
-- PROCEDURES ARMAZENADAS
-- ============================================================

DELIMITER $$

-- -----------------------------------------------------
-- Procedure sp_audit_statistics
-- Estatísticas de auditoria
-- -----------------------------------------------------
USE `ser_pleno`$$
CREATE PROCEDURE IF NOT EXISTS `sp_audit_statistics`(IN days_back INT)
BEGIN
    SELECT 
        action, 
        COUNT(*) as total, 
        DATE(created_at) as log_date
    FROM audit_log
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL days_back DAY)
    GROUP BY action, DATE(created_at)
    ORDER BY log_date DESC;
END$$

-- -----------------------------------------------------
-- Procedure sp_cleanup_audit_logs
-- Limpeza de logs antigos
-- -----------------------------------------------------
USE `ser_pleno`$$
CREATE PROCEDURE IF NOT EXISTS `sp_cleanup_audit_logs`(IN days_to_keep INT)
BEGIN
    DELETE FROM audit_log 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
END$$

DELIMITER ;

-- ============================================================
-- TRIGGERS DE AUDITORIA
-- ============================================================

DELIMITER $$

-- -----------------------------------------------------
-- Trigger aluno_audit_delete
-- Auditoria de exclusão de aluno
-- -----------------------------------------------------
USE `ser_pleno`$$
CREATE TRIGGER IF NOT EXISTS `aluno_audit_delete`
BEFORE DELETE ON `ser_pleno`.`aluno`
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values)
    VALUES ('aluno', OLD.id, 'DELETE',
            JSON_OBJECT('nome', OLD.nome, 'status', OLD.status));
END$$

-- -----------------------------------------------------
-- Trigger aluno_audit_insert
-- Auditoria de inserção de aluno
-- -----------------------------------------------------
USE `ser_pleno`$$
CREATE TRIGGER IF NOT EXISTS `aluno_audit_insert`
AFTER INSERT ON `ser_pleno`.`aluno`
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, new_values)
    VALUES ('aluno', NEW.id, 'CREATE', 
            JSON_OBJECT('nome', NEW.nome, 'status', NEW.status, 'prioridade', NEW.priority_level));
END$$

-- -----------------------------------------------------
-- Trigger aluno_audit_update
-- Auditoria de atualização de aluno
-- -----------------------------------------------------
USE `ser_pleno`$$
CREATE TRIGGER IF NOT EXISTS `aluno_audit_update`
AFTER UPDATE ON `ser_pleno`.`aluno`
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values)
    VALUES ('aluno', NEW.id, 'UPDATE',
            JSON_OBJECT('nome', OLD.nome, 'status', OLD.status, 'prioridade', OLD.priority_level),
            JSON_OBJECT('nome', NEW.nome, 'status', NEW.status, 'prioridade', NEW.priority_level));
END$$

DELIMITER ;

-- ============================================================
-- VIEWS
-- ============================================================

-- -----------------------------------------------------
-- View v_audit_log
-- Visão de auditoria com dados do usuário
-- -----------------------------------------------------
CREATE OR REPLACE ALGORITHM=UNDEFINED 
DEFINER=CURRENT_USER 
SQL SECURITY INVOKER 
VIEW `ser_pleno`.`v_audit_log` AS
SELECT 
    al.id AS id,
    al.table_name AS table_name,
    al.record_id AS record_id,
    al.action AS action,
    al.old_values AS old_values,
    al.new_values AS new_values,
    al.user_id AS user_id,
    al.username AS username,
    al.ip_address AS ip_address,
    al.user_agent AS user_agent,
    al.details AS details,
    al.created_at AS created_at,
    u.email AS user_email,
    u.username AS auth_username
FROM audit_log al
LEFT JOIN auth_user u ON al.user_id = u.id;

-- ============================================================
-- RESTAURAR CONFIGURAÇÕES
-- ============================================================

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
