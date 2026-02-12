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
-- Table `ser_pleno`.`agendamento`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`agendamento` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(200) NULL DEFAULT NULL,
  `student_id` INT NOT NULL,
  `data_hora` DATETIME(6) NOT NULL,
  `motivo` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'scheduled',
  `local` VARCHAR(200) NULL DEFAULT NULL,
  `profissional` VARCHAR(200) NULL DEFAULT NULL,
  `laudo` VARCHAR(45) NULL DEFAULT NULL,
  `origem` VARCHAR(20) NULL DEFAULT NULL,
  `desktop_appointment_id` INT NULL DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  INDEX `agendamento_student_id_idx` (`student_id` ASC) VISIBLE,
  INDEX `agendamento_data_hora_idx` (`data_hora` ASC) VISIBLE,
  INDEX `agendamento_status_idx` (`status` ASC) VISIBLE,
  INDEX `agendamento_data_status_idx` (`data_hora` ASC, `status` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 17
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
  PRIMARY KEY (`id_aluno`),
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 33
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
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 2
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
ENGINE = MyISAM
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
  INDEX `auth_group_permissions_group_id_b120cbf9` (`group_id` ASC) VISIBLE,
  INDEX `auth_group_permissions_permission_id_84c5c92e` (`permission_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `auth_permission_content_type_id_2f476e4b` (`content_type_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 165
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


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
ENGINE = MyISAM
AUTO_INCREMENT = 34
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
  INDEX `auth_user_groups_user_id_6a12ed8b` (`user_id` ASC) VISIBLE,
  INDEX `auth_user_groups_group_id_97559544` (`group_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `auth_user_user_permissions_user_id_a95ead1b` (`user_id` ASC) VISIBLE,
  INDEX `auth_user_user_permissions_permission_id_1fbb5f2c` (`permission_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `autoavaliacao_Aluno_id_aluno_3cb52ec3` (`Aluno_id_aluno` ASC) VISIBLE)
ENGINE = MyISAM
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
ENGINE = MyISAM
AUTO_INCREMENT = 6
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
ENGINE = MyISAM
AUTO_INCREMENT = 5
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
  UNIQUE INDEX `user_id` (`user_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 2
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
  INDEX `desktop_alert_assigned_to_id_5c0fd53f` (`assigned_to_id` ASC) VISIBLE,
  INDEX `desktop_alert_resolved_by_id_789d567a` (`resolved_by_id` ASC) VISIBLE,
  INDEX `desktop_alert_student_id_633f8551` (`student_id` ASC) VISIBLE,
  INDEX `desktop_ale_is_read_15ec4b_idx` (`is_read` ASC, `is_resolved` ASC) VISIBLE,
  INDEX `desktop_ale_alert_t_e32351_idx` (`alert_type` ASC, `severity` ASC) VISIBLE,
  INDEX `desktop_ale_assigne_709829_idx` (`assigned_to_id` ASC, `is_resolved` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 17
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`desktop_appointment`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`desktop_appointment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL,
  `time` INT NULL DEFAULT NULL,
  `date` DATE NOT NULL,
  `status` VARCHAR(20) NULL DEFAULT 'scheduled',
  `notes` TEXT NULL DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`))
ENGINE = InnoDB
AUTO_INCREMENT = 2
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
  INDEX `desktop_doc_student_4214ea_idx` (`student_id` ASC, `created_at` ASC) VISIBLE,
  INDEX `desktop_doc_documen_833470_idx` (`document_type` ASC) VISIBLE,
  INDEX `desktop_doc_expiry__89def3_idx` (`expiry_date` ASC) VISIBLE,
  INDEX `desktop_document_student_id_cd8d5b75` (`student_id` ASC) VISIBLE,
  INDEX `desktop_document_uploaded_by_id_25f83f7f` (`uploaded_by_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 5
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
  INDEX `desktop_goa_student_af7814_idx` (`student_id` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_goa_categor_c44b94_idx` (`category` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_goa_target__0e3fa1_idx` (`target_date` ASC) VISIBLE,
  INDEX `desktop_goa_priorit_bfb8f3_idx` (`priority` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_goal_created_by_id_609e367a` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_goal_student_id_e18da841` (`student_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 14
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
  INDEX `desktop_goalprogress_goal_id_2961e8f7` (`goal_id` ASC) VISIBLE,
  INDEX `desktop_goalprogress_recorded_by_id_5510062f` (`recorded_by_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `desktop_intervention_student_id_27ec8a66` (`student_id` ASC) VISIBLE,
  INDEX `desktop_int_student_202c5a_idx` (`student_id` ASC, `date` ASC) VISIBLE,
  INDEX `desktop_int_date_412a25_idx` (`date` ASC) VISIBLE,
  INDEX `desktop_int_interve_d0100b_idx` (`intervention_type` ASC) VISIBLE,
  INDEX `desktop_int_follow__b9866e_idx` (`follow_up_required` ASC, `follow_up_date` ASC) VISIBLE,
  INDEX `desktop_int_outcome_5cc100_idx` (`outcome` ASC) VISIBLE,
  INDEX `desktop_intervention_conducted_by_id_1a18fe97` (`conducted_by_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  `caminho_arquivo` VARCHAR(500) NULL DEFAULT NULL,
  `tipo_arquivo` VARCHAR(50) NULL DEFAULT NULL,
  `recipient_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `desktop_message_sender_id_19765a9f` (`sender_id` ASC) VISIBLE,
  INDEX `desktop_mes_sender__f98485_idx` (`sender_id` ASC, `recipient_id` ASC, `timestamp` ASC) VISIBLE,
  INDEX `desktop_mes_recipie_d928be_idx` (`recipient_id` ASC, `read` ASC) VISIBLE,
  INDEX `desktop_message_recipient_id_139ce2a4` (`recipient_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 6
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
  INDEX `desktop_moo_student_d74782_idx` (`student_id` ASC, `entry_date` ASC) VISIBLE,
  INDEX `desktop_moo_mood_le_d662c8_idx` (`mood_level` ASC, `entry_date` ASC) VISIBLE,
  INDEX `desktop_moodentry_recorded_by_id_fb857831` (`recorded_by_id` ASC) VISIBLE,
  INDEX `desktop_moodentry_student_id_44fdad85` (`student_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 771
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
  INDEX `desktop_not_student_d0ded8_idx` (`student_id` ASC, `created_at` ASC) VISIBLE,
  INDEX `desktop_not_note_ty_e75afa_idx` (`note_type` ASC, `created_at` ASC) VISIBLE,
  INDEX `desktop_not_created_54811f_idx` (`created_by_id` ASC, `created_at` ASC) VISIBLE,
  INDEX `desktop_not_is_pinn_146e19_idx` (`is_pinned` ASC, `created_at` ASC) VISIBLE,
  INDEX `desktop_note_created_by_id_af03be4c` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_note_related_intervention_id_76b5598e` (`related_intervention_id` ASC) VISIBLE,
  INDEX `desktop_note_related_screening_id_a42b931b` (`related_screening_id` ASC) VISIBLE,
  INDEX `desktop_note_student_id_a7824b1d` (`student_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 11
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
  INDEX `desktop_orientation_psychologist_id_77354f94` (`psychologist_id` ASC) VISIBLE,
  INDEX `desktop_orientation_student_id_79c60345` (`student_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 9
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
  INDEX `desktop_orientationattachment_orientation_id_9d49b853` (`orientation_id` ASC) VISIBLE,
  INDEX `desktop_orientationattachment_uploaded_by_id_e3f4f2a0` (`uploaded_by_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `desktop_report_generated_by_id_a6ac8bcd` (`generated_by_id` ASC) VISIBLE,
  INDEX `desktop_rep_report__062547_idx` (`report_type` ASC, `generated_at` ASC) VISIBLE,
  INDEX `desktop_rep_generat_9c71ec_idx` (`generated_by_id` ASC, `generated_at` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `desktop_reporttemplate_created_by_id_3c1bed51` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_rep_report__afe023_idx` (`report_type` ASC, `is_active` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 5
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
  INDEX `desktop_screening_conducted_by_id_506bfae4` (`conducted_by_id` ASC) VISIBLE,
  INDEX `desktop_screening_student_id_3d956d98` (`student_id` ASC) VISIBLE,
  INDEX `desktop_screening_form_id_d3925c20` (`form_id` ASC) VISIBLE,
  INDEX `desktop_scr_student_f445de_idx` (`student_id` ASC, `status` ASC) VISIBLE,
  INDEX `desktop_scr_schedul_433f0d_idx` (`scheduled_date` ASC) VISIBLE,
  INDEX `desktop_scr_priorit_33083c_idx` (`priority` ASC, `status` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 25
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
  INDEX `desktop_screeningform_created_by_id_e4d37df9` (`created_by_id` ASC) VISIBLE,
  INDEX `desktop_scr_is_acti_d7532a_idx` (`is_active` ASC, `created_at` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 2
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
  INDEX `desktop_wel_student_07068a_idx` (`student_id` ASC, `check_in_date` ASC) VISIBLE,
  INDEX `desktop_wel_check_i_525c86_idx` (`check_in_type` ASC, `check_in_date` ASC) VISIBLE,
  INDEX `desktop_wel_follow__957e45_idx` (`follow_up_needed` ASC, `follow_up_date` ASC) VISIBLE,
  INDEX `desktop_wellnesscheckin_conducted_by_id_98f3219f` (`conducted_by_id` ASC) VISIBLE,
  INDEX `desktop_wellnesscheckin_student_id_e358bcad` (`student_id` ASC) VISIBLE)
ENGINE = MyISAM
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
  INDEX `disponibilidade_Analista_id_analista_04058a77` (`Analista_id_analista` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 10
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
  INDEX `django_admin_log_content_type_id_c4bce8eb` (`content_type_id` ASC) VISIBLE,
  INDEX `django_admin_log_user_id_c564eba6` (`user_id` ASC) VISIBLE)
ENGINE = MyISAM
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
ENGINE = MyISAM
AUTO_INCREMENT = 42
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
ENGINE = MyISAM
AUTO_INCREMENT = 48
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
ENGINE = MyISAM
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
  INDEX `gamificacao_Aluno_id_aluno_d96ca6dd` (`Aluno_id_aluno` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 31
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
ENGINE = MyISAM
AUTO_INCREMENT = 3
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
  `aluno_id` INT NOT NULL,
  `updated_at` DATETIME(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `help_requests_aluno_id_b47fdf02` (`aluno_id` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 6
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
  `Aluno_id_aluno` INT NOT NULL,
  `agendamento_id` INT NULL DEFAULT NULL,
  `tipo` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_mensagem`),
  INDEX `mensagens_Aluno_id_aluno_53a4144f` (`Aluno_id_aluno` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 3
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ser_pleno`.`meu_historico`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ser_pleno`.`meu_historico` (
  `id_historico` INT NOT NULL AUTO_INCREMENT,
  `humor_media` DECIMAL(10,0) NOT NULL,
  `dias_consecutivos` INT NOT NULL,
  `total_registros` INT NOT NULL,
  `Aluno_id_aluno` INT NOT NULL,
  PRIMARY KEY (`id_historico`),
  INDEX `meu_historico_Aluno_id_aluno_cfd03397` (`Aluno_id_aluno` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 31
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
  `conteudo` LONGTEXT NOT NULL,
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
ENGINE = MyISAM
AUTO_INCREMENT = 5
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
  INDEX `registros_diarios_id_historico_9a188efe` (`id_historico` ASC) VISIBLE)
ENGINE = MyISAM
AUTO_INCREMENT = 771
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
ENGINE = MyISAM
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
