-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema ser_pleno
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema ser_pleno
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `ser_pleno` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `ser_pleno` ;

-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_user`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `password` VARCHAR(128) NOT NULL,
  `last_login` DATETIME(6) NULL DEFAULT NULL,
  `is_superuser` TINYINT(1) NOT NULL,
  `username` VARCHAR(150) NOT NULL,
  `first_name` VARCHAR(150) NOT NULL,
  `last_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `is_staff` TINYINT(1) NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `date_joined` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username` (`username` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 80
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`aluno`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`aluno` (
  `id_aluno` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NOT NULL,
  `sala` VARCHAR(45) NULL DEFAULT NULL,
  `curso` VARCHAR(200) NULL DEFAULT NULL,
  `professor_responsavel` VARCHAR(200) NOT NULL,
  `user_id` INT NULL DEFAULT NULL,
  `attention_reason` LONGTEXT NULL DEFAULT NULL,
  `emergency_contact` VARCHAR(100) NULL DEFAULT NULL,
  `emergency_phone` VARCHAR(20) NULL DEFAULT NULL,
  `enrollment_date` DATE NULL DEFAULT NULL,
  `general_notes` LONGTEXT NULL DEFAULT NULL,
  `has_medical_report` TINYINT(1) NOT NULL,
  `last_contact_date` DATE NULL DEFAULT NULL,
  `phone` VARCHAR(20) NULL DEFAULT NULL,
  `priority_level` INT NOT NULL,
  `requires_attention` TINYINT(1) NOT NULL,
  `tags` JSON NOT NULL DEFAULT _utf8mb4'[]',
  `age` INT NULL DEFAULT NULL,
  `created_at` DATETIME(6) NULL DEFAULT NULL,
  `updated_at` DATETIME(6) NULL DEFAULT NULL,
  `status` VARCHAR(20) NOT NULL,
  `avatar` VARCHAR(10) NOT NULL,
  `dark_mode` TINYINT(1) NOT NULL,
  `notifications_enabled` TINYINT(1) NOT NULL,
  PRIMARY KEY (`id_aluno`),
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE,
  INDEX `idx_status_nome` (`status` ASC, `nome` ASC) VISIBLE,
  INDEX `idx_attention_priority` (`requires_attention` ASC, `priority_level` ASC) VISIBLE,
  INDEX `idx_aluno_user` (`user_id` ASC) VISIBLE,
  CONSTRAINT `aluno_user_id_0036d271_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 36
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`agendamento`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`agendamento` (
  `nome` VARCHAR(200) NULL DEFAULT NULL,
  `data_hora` DATETIME(6) NOT NULL,
  `motivo` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `laudo` VARCHAR(45) NULL DEFAULT NULL,
  `local` VARCHAR(200) NULL DEFAULT NULL,
  `origem` VARCHAR(20) NULL DEFAULT NULL,
  `profissional` VARCHAR(200) NULL DEFAULT NULL,
  `student_id` INT NULL DEFAULT NULL,
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NULL DEFAULT NULL,
  `updated_at` DATETIME(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `agendamentos_student_id_9f14d758_fk_aluno_id_aluno` (`student_id` ASC) VISIBLE,
  INDEX `idx_agendamento_profissional_data` (`profissional`(191) ASC, `data_hora` ASC) VISIBLE,
  CONSTRAINT `agendamentos_student_id_9f14d758_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 52
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`algorithm_challenge`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`algorithm_challenge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `difficulty` VARCHAR(20) NOT NULL,
  `available_blocks` JSON NOT NULL,
  `correct_sequence` JSON NOT NULL,
  `pseudocode_template` LONGTEXT NULL DEFAULT NULL,
  `category` VARCHAR(100) NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 7
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`analista`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`analista` (
  `id_analista` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id_analista`),
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE,
  UNIQUE INDEX `analista_email_2f0a36ce_uniq` (`email` ASC) VISIBLE,
  CONSTRAINT `analista_user_id_1c97d952_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_group`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_group` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name` (`name` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 17
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`django_content_type`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_content_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `app_label` VARCHAR(100) NOT NULL,
  `model` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label` ASC, `model` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 50
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_permission`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_permission` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `content_type_id` INT NOT NULL,
  `codename` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id` ASC, `codename` ASC) VISIBLE,
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `ser_pleno`.`django_content_type` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 197
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_group_permissions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_group_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id` ASC, `permission_id` ASC) VISIBLE,
  INDEX `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id` ASC) VISIBLE,
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm`
    FOREIGN KEY (`permission_id`)
    REFERENCES `ser_pleno`.`auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `ser_pleno`.`auth_group` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_user_groups`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_user_groups` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `group_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id` ASC, `group_id` ASC) VISIBLE,
  INDEX `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id` ASC) VISIBLE,
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `ser_pleno`.`auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 3
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`auth_user_user_permissions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`auth_user_user_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id` ASC, `permission_id` ASC) VISIBLE,
  INDEX `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id` ASC) VISIBLE,
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm`
    FOREIGN KEY (`permission_id`)
    REFERENCES `ser_pleno`.`auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`authtoken_token`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`authtoken_token` (
  `key` VARCHAR(40) NOT NULL,
  `created` DATETIME(6) NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`key`),
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE,
  CONSTRAINT `authtoken_token_user_id_35299eff_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`autoavaliacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`autoavaliacao` (
  `id_autoavaliacao` INT NOT NULL AUTO_INCREMENT,
  `data_avaliacao` DATE NULL DEFAULT NULL,
  `bem_estar_academico` VARCHAR(255) NULL DEFAULT NULL,
  `bem_estar_emocional` VARCHAR(255) NULL DEFAULT NULL,
  `bem_estar_social` VARCHAR(255) NULL DEFAULT NULL,
  `reflexoes_pessoais` LONGTEXT NULL DEFAULT NULL,
  `pontos_xp` INT NULL DEFAULT NULL,
  `Aluno_id_aluno` INT NOT NULL,
  PRIMARY KEY (`id_autoavaliacao`),
  INDEX `autoavaliacao_Aluno_id_aluno_3cb52ec3_fk_aluno_id_aluno` (`Aluno_id_aluno` ASC) VISIBLE,
  CONSTRAINT `autoavaliacao_Aluno_id_aluno_3cb52ec3_fk_aluno_id_aluno`
    FOREIGN KEY (`Aluno_id_aluno`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 14
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`backpack_challenge`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`backpack_challenge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `difficulty` VARCHAR(20) NOT NULL,
  `backpack_config` JSON NOT NULL,
  `available_items` JSON NOT NULL,
  `optimal_score` INT NOT NULL,
  `category` VARCHAR(100) NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`badge`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`badge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(100) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `icon` VARCHAR(100) NULL DEFAULT NULL,
  `description` LONGTEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `key` (`key` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`challenge`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`challenge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(100) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `description` LONGTEXT NULL DEFAULT NULL,
  `xp` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `key` (`key` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`coordenacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`coordenacao` (
  `id_coordenacao` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id_coordenacao`),
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE,
  UNIQUE INDEX `coordenacao_email_1c63c984_uniq` (`email` ASC) VISIBLE,
  CONSTRAINT `coordenacao_user_id_21d891a6_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 3
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_alert`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_alert` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `alert_type` VARCHAR(50) NOT NULL,
  `severity` VARCHAR(20) NOT NULL,
  `message` LONGTEXT NOT NULL,
  `details` JSON NOT NULL,
  `is_read` TINYINT(1) NOT NULL,
  `is_resolved` TINYINT(1) NOT NULL,
  `resolved_at` DATETIME(6) NULL DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `assigned_to_id` INT NULL DEFAULT NULL,
  `resolved_by_id` INT NULL DEFAULT NULL,
  `student_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_alert_resolved_by_id_789d567a_fk_auth_user_id` (`resolved_by_id` ASC) VISIBLE,
  INDEX `desktop_ale_is_read_15ec4b_idx` (`is_read` ASC, `is_resolved` ASC) VISIBLE,
  INDEX `desktop_ale_alert_t_e32351_idx` (`alert_type` ASC, `severity` ASC) VISIBLE,
  INDEX `desktop_ale_assigne_709829_idx` (`assigned_to_id` ASC, `is_resolved` ASC) VISIBLE,
  INDEX `desktop_alert_student_id_633f8551_fk_aluno_id_aluno` (`student_id` ASC) VISIBLE,
  CONSTRAINT `desktop_alert_assigned_to_id_5c0fd53f_fk_auth_user_id`
    FOREIGN KEY (`assigned_to_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_alert_resolved_by_id_789d567a_fk_auth_user_id`
    FOREIGN KEY (`resolved_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_alert_student_id_633f8551_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 54
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_appointment`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_appointment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `time` INT NULL DEFAULT NULL,
  `date` DATE NOT NULL,
  `status` VARCHAR(20) NULL DEFAULT NULL,
  `notes` LONGTEXT NULL DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `student_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_appointment_student_id_a017d62e_fk_aluno_id_aluno` (`student_id` ASC) VISIBLE,
  CONSTRAINT `desktop_appointment_student_id_a017d62e_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_auditlog`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_auditlog` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `action` VARCHAR(20) NOT NULL,
  `model_name` VARCHAR(100) NOT NULL,
  `object_id` VARCHAR(100) NULL DEFAULT NULL,
  `object_repr` VARCHAR(255) NULL DEFAULT NULL,
  `changes` JSON NOT NULL,
  `ip_address` CHAR(39) NULL DEFAULT NULL,
  `user_agent` VARCHAR(255) NULL DEFAULT NULL,
  `request_path` VARCHAR(255) NULL DEFAULT NULL,
  `user_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_aud_user_id_e19a20_idx` (`user_id` ASC, `action` ASC) VISIBLE,
  INDEX `desktop_aud_model_n_44d8a9_idx` (`model_name` ASC, `object_id` ASC) VISIBLE,
  INDEX `desktop_aud_created_e36ee6_idx` (`created_at` ASC) VISIBLE,
  CONSTRAINT `desktop_auditlog_user_id_49b9640c_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 25
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_document`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_document` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `document_type` VARCHAR(50) NOT NULL,
  `file` VARCHAR(500) NOT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `file_size` INT NULL DEFAULT NULL,
  `mime_type` VARCHAR(100) NOT NULL,
  `issue_date` DATE NULL DEFAULT NULL,
  `expiry_date` DATE NULL DEFAULT NULL,
  `is_confidential` TINYINT(1) NOT NULL,
  `student_id` INT NOT NULL,
  `uploaded_by_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_document_uploaded_by_id_25f83f7f_fk_auth_user_id` (`uploaded_by_id` ASC) VISIBLE,
  INDEX `desktop_doc_student_4214ea_idx` (`student_id` ASC, `created_at` DESC) VISIBLE,
  INDEX `desktop_doc_documen_833470_idx` (`document_type` ASC) VISIBLE,
  INDEX `desktop_doc_expiry__89def3_idx` (`expiry_date` ASC) VISIBLE,
  CONSTRAINT `desktop_document_student_id_cd8d5b75_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`),
  CONSTRAINT `desktop_document_uploaded_by_id_25f83f7f_fk_auth_user_id`
    FOREIGN KEY (`uploaded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 10
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_goal`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_goal` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `category` VARCHAR(50) NOT NULL,
  `priority` VARCHAR(20) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `target_date` DATE NULL DEFAULT NULL,
  `completed_date` DATE NULL DEFAULT NULL,
  `progress_percentage` INT NOT NULL,
  `notes` LONGTEXT NOT NULL,
  `success_criteria` LONGTEXT NOT NULL,
  `created_by_id` INT NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_goal_created_by_id_609e367a_fk_auth_user_id` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_goa_student_af7814_idx` (`student_id` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_goa_categor_c44b94_idx` (`category` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_goa_target__0e3fa1_idx` (`target_date` ASC) VISIBLE,
  INDEX `desktop_goa_priorit_bfb8f3_idx` (`priority` ASC, `status` ASC) VISIBLE,
  CONSTRAINT `desktop_goal_created_by_id_609e367a_fk_auth_user_id`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_goal_student_id_e18da841_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_goalprogress`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_goalprogress` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `percentage` INT NOT NULL,
  `notes` LONGTEXT NOT NULL,
  `recorded_at` DATETIME(6) NOT NULL,
  `goal_id` BIGINT NOT NULL,
  `recorded_by_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `dgp_goal_idx` (`goal_id` ASC) VISIBLE,
  INDEX `dgp_recorded_by_idx` (`recorded_by_id` ASC) VISIBLE,
  CONSTRAINT `desktop_goalprogress_goal_id_2961e8f7_fk_desktop_goal_id`
    FOREIGN KEY (`goal_id`)
    REFERENCES `ser_pleno`.`desktop_goal` (`id`),
  CONSTRAINT `desktop_goalprogress_recorded_by_id_5510062f_fk_auth_user_id`
    FOREIGN KEY (`recorded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 46
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_intervention`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_intervention` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `date` DATE NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `student_id` INT NOT NULL,
  `conducted_by_id` INT NULL DEFAULT NULL,
  `duration_minutes` INT NULL DEFAULT NULL,
  `follow_up_completed` TINYINT(1) NOT NULL,
  `follow_up_date` DATE NULL DEFAULT NULL,
  `follow_up_required` TINYINT(1) NOT NULL,
  `intervention_notes` LONGTEXT NOT NULL,
  `intervention_type` VARCHAR(50) NOT NULL,
  `is_confidential` TINYINT(1) NOT NULL,
  `outcome` VARCHAR(50) NOT NULL,
  `outcome_notes` LONGTEXT NOT NULL,
  `tags` JSON NOT NULL DEFAULT _utf8mb4'[]',
  PRIMARY KEY (`id`),
  INDEX `desktop_intervention_conducted_by_id_1a18fe97_fk_auth_user_id` (`conducted_by_id` ASC) VISIBLE,
  INDEX `desktop_int_student_202c5a_idx` (`student_id` ASC, `date` ASC) VISIBLE,
  INDEX `desktop_int_date_412a25_idx` (`date` DESC) VISIBLE,
  INDEX `desktop_int_interve_d0100b_idx` (`intervention_type` ASC) VISIBLE,
  INDEX `desktop_int_follow__b9866e_idx` (`follow_up_required` ASC, `follow_up_date` ASC) VISIBLE,
  INDEX `desktop_int_outcome_5cc100_idx` (`outcome` ASC) VISIBLE,
  CONSTRAINT `desktop_intervention_conducted_by_id_1a18fe97_fk_auth_user_id`
    FOREIGN KEY (`conducted_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_intervention_student_id_27ec8a66_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_message`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_message` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `sender_id` INT NULL DEFAULT NULL,
  `text` LONGTEXT NOT NULL,
  `timestamp` DATETIME(6) NOT NULL,
  `read` TINYINT(1) NOT NULL,
  `recipient_id` INT NULL DEFAULT NULL,
  `caminho_arquivo` VARCHAR(500) NULL DEFAULT NULL,
  `tipo_arquivo` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_message_sender_id_19765a9f` (`sender_id` ASC) VISIBLE,
  INDEX `desktop_mes_sender__f98485_idx` (`sender_id` ASC, `recipient_id` ASC, `timestamp` ASC) VISIBLE,
  INDEX `desktop_mes_recipie_d928be_idx` (`recipient_id` ASC, `read` ASC) VISIBLE,
  CONSTRAINT `desktop_message_recipient_id_139ce2a4_fk_auth_user_id`
    FOREIGN KEY (`recipient_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_message_sender_id_19765a9f_fk_auth_user_id`
    FOREIGN KEY (`sender_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 57
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_moodentry`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_moodentry` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `mood_level` INT NOT NULL,
  `mood_emoji` VARCHAR(10) NOT NULL,
  `energy_level` INT NULL DEFAULT NULL,
  `stress_level` INT NULL DEFAULT NULL,
  `sleep_quality` INT NULL DEFAULT NULL,
  `notes` LONGTEXT NOT NULL,
  `triggers` JSON NOT NULL,
  `activities` JSON NOT NULL,
  `entry_date` DATE NOT NULL,
  `entry_time` TIME NULL DEFAULT NULL,
  `recorded_by_id` INT NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_moodentry_recorded_by_id_fb857831_fk_auth_user_id` (`recorded_by_id` ASC) VISIBLE,
  INDEX `desktop_moo_student_d74782_idx` (`student_id` ASC, `entry_date` DESC) VISIBLE,
  INDEX `desktop_moo_mood_le_d662c8_idx` (`mood_level` ASC, `entry_date` DESC) VISIBLE,
  INDEX `idx_moodentry_student_date` (`student_id` ASC, `entry_date` ASC) VISIBLE,
  CONSTRAINT `desktop_moodentry_recorded_by_id_fb857831_fk_auth_user_id`
    FOREIGN KEY (`recorded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_moodentry_student_id_44fdad85_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 301
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_screeningform`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_screeningform` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `questions` JSON NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `created_by_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_screeningform_created_by_id_e4d37df9_fk_auth_user_id` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_scr_is_acti_d7532a_idx` (`is_active` ASC, `created_at` DESC) VISIBLE,
  CONSTRAINT `desktop_screeningform_created_by_id_e4d37df9_fk_auth_user_id`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_screening`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_screening` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `status` VARCHAR(20) NOT NULL,
  `priority` VARCHAR(20) NOT NULL,
  `scheduled_date` DATE NULL DEFAULT NULL,
  `completed_date` DATE NULL DEFAULT NULL,
  `responses` JSON NOT NULL,
  `score` INT NULL DEFAULT NULL,
  `observations` LONGTEXT NOT NULL,
  `recommendations` LONGTEXT NOT NULL,
  `requires_followup` TINYINT(1) NOT NULL,
  `followup_date` DATE NULL DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `conducted_by_id` INT NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  `form_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_screening_conducted_by_id_506bfae4_fk_auth_user_id` (`conducted_by_id` ASC) VISIBLE,
  INDEX `desktop_screening_form_id_d3925c20_fk_desktop_screeningform_id` (`form_id` ASC) VISIBLE,
  INDEX `desktop_scr_student_f445de_idx` (`student_id` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_scr_schedul_433f0d_idx` (`scheduled_date` ASC) VISIBLE,
  INDEX `desktop_scr_priorit_33083c_idx` (`priority` ASC, `status` ASC) VISIBLE,
  INDEX `idx_screening_student_completed` (`student_id` ASC, `completed_date` ASC) VISIBLE,
  CONSTRAINT `desktop_screening_conducted_by_id_506bfae4_fk_auth_user_id`
    FOREIGN KEY (`conducted_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_screening_form_id_d3925c20_fk_desktop_screeningform_id`
    FOREIGN KEY (`form_id`)
    REFERENCES `ser_pleno`.`desktop_screeningform` (`id`),
  CONSTRAINT `desktop_screening_student_id_3d956d98_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 47
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_note`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_note` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `note_type` VARCHAR(50) NOT NULL,
  `is_private` TINYINT(1) NOT NULL,
  `is_pinned` TINYINT(1) NOT NULL,
  `tags` JSON NOT NULL,
  `created_by_id` INT NULL DEFAULT NULL,
  `related_intervention_id` BIGINT NULL DEFAULT NULL,
  `related_screening_id` BIGINT NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_note_related_intervention_76b5598e_fk_desktop_i` (`related_intervention_id` ASC) VISIBLE,
  INDEX `desktop_note_related_screening_id_a42b931b_fk_desktop_s` (`related_screening_id` ASC) VISIBLE,
  INDEX `desktop_not_student_d0ded8_idx` (`student_id` ASC, `created_at` DESC) VISIBLE,
  INDEX `desktop_not_note_ty_e75afa_idx` (`note_type` ASC, `created_at` DESC) VISIBLE,
  INDEX `desktop_not_created_54811f_idx` (`created_by_id` ASC, `created_at` DESC) VISIBLE,
  INDEX `desktop_not_is_pinn_146e19_idx` (`is_pinned` DESC, `created_at` DESC) VISIBLE,
  CONSTRAINT `desktop_note_created_by_id_af03be4c_fk_auth_user_id`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_note_related_intervention_76b5598e_fk_desktop_i`
    FOREIGN KEY (`related_intervention_id`)
    REFERENCES `ser_pleno`.`desktop_intervention` (`id`),
  CONSTRAINT `desktop_note_related_screening_id_a42b931b_fk_desktop_s`
    FOREIGN KEY (`related_screening_id`)
    REFERENCES `ser_pleno`.`desktop_screening` (`id`),
  CONSTRAINT `desktop_note_student_id_a7824b1d_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_orientation`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_orientation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `theme` VARCHAR(120) NOT NULL,
  `session_date` DATE NULL DEFAULT NULL,
  `content` LONGTEXT NOT NULL,
  `is_markdown` TINYINT(1) NOT NULL,
  `motivational_message` LONGTEXT NOT NULL,
  `action_plan` JSON NOT NULL,
  `psychologist_id` INT NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `do_psychologist_idx` (`psychologist_id` ASC) VISIBLE,
  INDEX `do_student_idx` (`student_id` ASC) VISIBLE,
  CONSTRAINT `desktop_orientation_psychologist_id_77354f94_fk_auth_user_id`
    FOREIGN KEY (`psychologist_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_orientation_student_id_79c60345_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 47
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_orientationattachment`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_orientationattachment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `file` VARCHAR(100) NOT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `mime_type` VARCHAR(100) NOT NULL,
  `orientation_id` BIGINT NOT NULL,
  `uploaded_by_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `doa_orientation_idx` (`orientation_id` ASC) VISIBLE,
  INDEX `doa_uploaded_by_idx` (`uploaded_by_id` ASC) VISIBLE,
  CONSTRAINT `desktop_orientationa_orientation_id_9d49b853_fk_desktop_o`
    FOREIGN KEY (`orientation_id`)
    REFERENCES `ser_pleno`.`desktop_orientation` (`id`),
  CONSTRAINT `desktop_orientationa_uploaded_by_id_e3f4f2a0_fk_auth_user`
    FOREIGN KEY (`uploaded_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 7
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_report`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_report` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL,
  `report_type` VARCHAR(50) NOT NULL,
  `format` VARCHAR(20) NOT NULL,
  `generated_at` DATETIME(6) NOT NULL,
  `parameters` JSON NOT NULL,
  `data` JSON NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_size` INT NULL DEFAULT NULL,
  `is_public` TINYINT(1) NOT NULL,
  `expires_at` DATETIME(6) NULL DEFAULT NULL,
  `generated_by_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_rep_report__062547_idx` (`report_type` ASC, `generated_at` DESC) VISIBLE,
  INDEX `desktop_rep_generat_9c71ec_idx` (`generated_by_id` ASC, `generated_at` DESC) VISIBLE,
  CONSTRAINT `desktop_report_generated_by_id_a6ac8bcd_fk_auth_user_id`
    FOREIGN KEY (`generated_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_reporttemplate`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_reporttemplate` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NOT NULL,
  `report_type` VARCHAR(50) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `template_config` JSON NOT NULL,
  `default_parameters` JSON NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `created_by_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_reporttemplate_created_by_id_3c1bed51_fk_auth_user_id` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_rep_report__afe023_idx` (`report_type` ASC, `is_active` ASC) VISIBLE,
  CONSTRAINT `desktop_reporttemplate_created_by_id_3c1bed51_fk_auth_user_id`
    FOREIGN KEY (`created_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_userprofile`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_userprofile` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `custom_permissions` JSON NOT NULL,
  `department` VARCHAR(100) NULL DEFAULT NULL,
  `phone` VARCHAR(20) NULL DEFAULT NULL,
  `avatar` VARCHAR(100) NULL DEFAULT NULL,
  `is_active_profile` TINYINT(1) NOT NULL,
  `last_login_ip` CHAR(39) NULL DEFAULT NULL,
  `user_id` INT NOT NULL,
  `last_page_url` VARCHAR(255) NULL DEFAULT NULL,
  `last_app` VARCHAR(20) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE,
  CONSTRAINT `desktop_userprofile_user_id_06f7b02c_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 51
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_wellnesscheckin`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_wellnesscheckin` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NOT NULL,
  `check_in_type` VARCHAR(50) NOT NULL,
  `check_in_date` DATE NOT NULL,
  `overall_wellbeing` INT NOT NULL,
  `responses` JSON NOT NULL,
  `attention_areas` JSON NOT NULL,
  `recommendations` LONGTEXT NOT NULL,
  `follow_up_needed` TINYINT(1) NOT NULL,
  `follow_up_date` DATE NULL DEFAULT NULL,
  `professional_notes` LONGTEXT NOT NULL,
  `conducted_by_id` INT NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_wellnesscheckin_conducted_by_id_98f3219f_fk_auth_user_id` (`conducted_by_id` ASC) VISIBLE,
  INDEX `desktop_wel_student_07068a_idx` (`student_id` ASC, `check_in_date` DESC) VISIBLE,
  INDEX `desktop_wel_check_i_525c86_idx` (`check_in_type` ASC, `check_in_date` DESC) VISIBLE,
  INDEX `desktop_wel_follow__957e45_idx` (`follow_up_needed` ASC, `follow_up_date` ASC) VISIBLE,
  CONSTRAINT `desktop_wellnesscheckin_conducted_by_id_98f3219f_fk_auth_user_id`
    FOREIGN KEY (`conducted_by_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`),
  CONSTRAINT `desktop_wellnesscheckin_student_id_e358bcad_fk_aluno_id_aluno`
    FOREIGN KEY (`student_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`disponibilidade`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`disponibilidade` (
  `id_disponibilidade` INT NOT NULL AUTO_INCREMENT,
  `Dias` VARCHAR(45) NULL DEFAULT NULL,
  `Horario` TIME NOT NULL,
  `Analista_id_analista` INT NULL DEFAULT NULL,
  `is_active` TINYINT(1) NOT NULL,
  PRIMARY KEY (`id_disponibilidade`),
  UNIQUE INDEX `disponibilidade_Horario_71321063_uniq` (`Horario` ASC) VISIBLE,
  UNIQUE INDEX `disponibilidade_Horario_Analista_id_analista_1004465e_uniq` (`Horario` ASC, `Analista_id_analista` ASC) VISIBLE,
  INDEX `disponibilidade_Analista_id_analista_fk` (`Analista_id_analista` ASC) VISIBLE,
  CONSTRAINT `disponibilidade_Analista_id_analista_fk`
    FOREIGN KEY (`Analista_id_analista`)
    REFERENCES `ser_pleno`.`analista` (`id_analista`))
ENGINE = InnoDB
AUTO_INCREMENT = 22
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`django_admin_log`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_admin_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `action_time` DATETIME(6) NOT NULL,
  `object_id` LONGTEXT NULL DEFAULT NULL,
  `object_repr` VARCHAR(200) NOT NULL,
  `action_flag` SMALLINT UNSIGNED NOT NULL,
  `change_message` LONGTEXT NOT NULL,
  `content_type_id` INT NULL DEFAULT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id` ASC) VISIBLE,
  INDEX `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id` ASC) VISIBLE,
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co`
    FOREIGN KEY (`content_type_id`)
    REFERENCES `ser_pleno`.`django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `ser_pleno`.`auth_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`django_migrations`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_migrations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `app` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `applied` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 84
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`django_session`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`django_session` (
  `session_key` VARCHAR(40) NOT NULL,
  `session_data` LONGTEXT NOT NULL,
  `expire_date` DATETIME(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  INDEX `django_session_expire_date_a5c62663` (`expire_date` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`fallacy_challenge`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`fallacy_challenge` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `texto_problema` LONGTEXT NOT NULL,
  `falacia_correta` VARCHAR(50) NOT NULL,
  `explicacao_didatica` LONGTEXT NOT NULL,
  `contra_argumento` LONGTEXT NULL DEFAULT NULL,
  `dificuldade` VARCHAR(20) NOT NULL,
  `categoria` VARCHAR(100) NOT NULL,
  `ativo` TINYINT(1) NOT NULL,
  `criado_em` DATETIME(6) NOT NULL,
  `atualizado_em` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 31
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`gamificacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`gamificacao` (
  `id_gamificacao` INT NOT NULL AUTO_INCREMENT,
  `pontos_atuais` INT NOT NULL,
  `nivel` INT NOT NULL,
  `conquistas` VARCHAR(100) NOT NULL,
  `check_in` INT NOT NULL,
  `metas_pessoais` VARCHAR(100) NOT NULL,
  `last_check_in_date` DATE NULL DEFAULT NULL,
  `Aluno_id_aluno` INT NOT NULL,
  PRIMARY KEY (`id_gamificacao`),
  INDEX `gamificacao_Aluno_id_aluno_d96ca6dd_fk_aluno_id_aluno` (`Aluno_id_aluno` ASC) VISIBLE,
  CONSTRAINT `gamificacao_Aluno_id_aluno_d96ca6dd_fk_aluno_id_aluno`
    FOREIGN KEY (`Aluno_id_aluno`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 30
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`guided_resource`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`guided_resource` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(100) NULL DEFAULT NULL,
  `title` VARCHAR(255) NOT NULL,
  `icon` VARCHAR(100) NULL DEFAULT NULL,
  `duration` VARCHAR(50) NULL DEFAULT NULL,
  `category` VARCHAR(100) NULL DEFAULT NULL,
  `content` LONGTEXT NULL DEFAULT NULL,
  `video_url` VARCHAR(200) NULL DEFAULT NULL,
  `share_url` VARCHAR(200) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`help_requests`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`help_requests` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `tipo` VARCHAR(50) NOT NULL,
  `mensagem` LONGTEXT NULL DEFAULT NULL,
  `prioridade` VARCHAR(20) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `localizacao` VARCHAR(100) NULL DEFAULT NULL,
  `dados_extras` JSON NOT NULL,
  `created_at` DATETIME(6) NULL DEFAULT NULL,
  `viewed_at` DATETIME(6) NULL DEFAULT NULL,
  `resolved_at` DATETIME(6) NULL DEFAULT NULL,
  `aluno_id` INT NULL DEFAULT NULL,
  `updated_at` DATETIME(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `help_requests_aluno_id_b47fdf02_fk_aluno_id_aluno` (`aluno_id` ASC) VISIBLE,
  CONSTRAINT `help_requests_aluno_id_b47fdf02_fk_aluno_id_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 24
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`mensagens`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`mensagens` (
  `id_mensagem` INT NOT NULL AUTO_INCREMENT,
  `remetente` VARCHAR(255) NULL DEFAULT NULL,
  `titulo` VARCHAR(255) NULL DEFAULT NULL,
  `conteudo` LONGTEXT NULL DEFAULT NULL,
  `lida` TINYINT(1) NOT NULL,
  `data_envio` DATE NULL DEFAULT NULL,
  `aluno_id` INT NOT NULL,
  `agendamento_id` INT NULL DEFAULT NULL,
  `tipo` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_mensagem`),
  INDEX `mensagens_Aluno_id_aluno_53a4144f_fk_aluno_id_aluno` (`aluno_id` ASC) VISIBLE,
  CONSTRAINT `mensagens_Aluno_id_aluno_53a4144f_fk_aluno_id_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`meu_historico`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`meu_historico` (
  `id_historico` INT NOT NULL AUTO_INCREMENT,
  `humor_media` DECIMAL(10,2) NOT NULL,
  `dias_consecutivos` INT NOT NULL,
  `total_registros` INT NOT NULL,
  `Aluno_id_aluno` INT NOT NULL,
  PRIMARY KEY (`id_historico`),
  INDEX `meu_historico_Aluno_id_aluno_cfd03397_fk_aluno_id_aluno` (`Aluno_id_aluno` ASC) VISIBLE,
  CONSTRAINT `meu_historico_Aluno_id_aluno_cfd03397_fk_aluno_id_aluno`
    FOREIGN KEY (`Aluno_id_aluno`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`))
ENGINE = InnoDB
AUTO_INCREMENT = 30
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`mural_posts`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`mural_posts` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `created_at` DATETIME(6) NULL DEFAULT NULL,
  `updated_at` DATETIME(6) NULL DEFAULT NULL,
  `titulo` VARCHAR(255) NOT NULL,
  `conteudo` TEXT NULL DEFAULT NULL,
  `autor` VARCHAR(150) NULL DEFAULT NULL,
  `publicado_em` DATETIME(6) NOT NULL,
  `ativo` TINYINT(1) NOT NULL,
  `categoria` VARCHAR(20) NOT NULL,
  `data_agendamento` DATETIME(6) NULL DEFAULT NULL,
  `link_externo` VARCHAR(200) NULL DEFAULT NULL,
  `blocos` JSON NOT NULL DEFAULT _utf8mb4'[]',
  `layout` VARCHAR(20) NOT NULL,
  `horario_evento` DATETIME(6) NULL DEFAULT NULL,
  `local_fisico` VARCHAR(200) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 22
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`player_stats`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`player_stats` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `game_id` VARCHAR(50) NOT NULL,
  `difficulty_level` INT NOT NULL,
  `best_time` INT NULL DEFAULT NULL,
  `min_moves` INT NULL DEFAULT NULL,
  `completed_at` DATETIME(6) NOT NULL,
  `aluno_id` INT NULL DEFAULT NULL,
  `high_score` INT NULL DEFAULT NULL,
  `victories` INT NULL DEFAULT '0',
  `ranking_type` VARCHAR(20) NOT NULL DEFAULT 'lower_is_better',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `unique_aluno_game_difficulty` (`aluno_id` ASC, `game_id` ASC, `difficulty_level` ASC) VISIBLE,
  CONSTRAINT `fk_playerstats_aluno`
    FOREIGN KEY (`aluno_id`)
    REFERENCES `ser_pleno`.`aluno` (`id_aluno`)
    ON DELETE CASCADE)
ENGINE = InnoDB
AUTO_INCREMENT = 20
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`registros_diarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`registros_diarios` (
  `id_registros` INT NOT NULL AUTO_INCREMENT,
  `data_registro` DATE NULL DEFAULT NULL,
  `humor` VARCHAR(50) NULL DEFAULT NULL,
  `id_historico` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id_registros`),
  INDEX `registros_diarios_id_historico_9a188efe_fk_meu_histo` (`id_historico` ASC) VISIBLE,
  CONSTRAINT `registros_diarios_id_historico_9a188efe_fk_meu_histo`
    FOREIGN KEY (`id_historico`)
    REFERENCES `ser_pleno`.`meu_historico` (`id_historico`))
ENGINE = InnoDB
AUTO_INCREMENT = 507
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`static_avatar`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`static_avatar` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `filename` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `filename` (`filename` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 21
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;


-- Índices adicionais para performance do dashboard
ALTER TABLE `ser_pleno`.`desktop_screening`
  ADD INDEX `idx_desktop_screening_status` (`status` ASC) VISIBLE;

ALTER TABLE `ser_pleno`.`desktop_moodentry`
  ADD INDEX `idx_desktop_moodentry_entry_date` (`entry_date` ASC) VISIBLE;

ALTER TABLE `ser_pleno`.`desktop_wellnesscheckin`
  ADD INDEX `idx_desktop_wellnesscheckin_check_in_date` (`check_in_date` ASC) VISIBLE;
