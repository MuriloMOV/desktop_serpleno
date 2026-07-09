CREATE TABLE IF NOT EXISTS `ser_pleno`.`agendamento` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL,
  `data_hora` DATETIME(6) NOT NULL,
  `motivo` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'scheduled',
  `local` VARCHAR(200) NULL DEFAULT NULL,
  `profissional` VARCHAR(200) NULL DEFAULT NULL,
  `laudo` VARCHAR(45) NULL DEFAULT NULL,
  `origem` VARCHAR(20) NULL DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  INDEX `agendamento_student_id_idx` (`student_id` ASC) VISIBLE,
  INDEX `agendamento_data_hora_idx` (`data_hora` ASC) VISIBLE,
  INDEX `agendamento_status_idx` (`status` ASC) VISIBLE,
  INDEX `agendamento_data_status_idx` (`data_hora` ASC, `status` ASC) VISIBLE,
  FOREIGN KEY (`student_id`) REFERENCES `ser_pleno`.`aluno` (`id_aluno`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
) ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;
