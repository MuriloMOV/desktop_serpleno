#!/usr/bin/env python3
"""Script para executar o SQL de criação da tabela agendamento modificada."""

import logging
from ser_pleno.infrastructure.database import get_db_connection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_sql_script():
    """Executa o script SQL para criar a tabela agendamento."""
    sql_statements = [
        "SET FOREIGN_KEY_CHECKS = 0",
        """
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
COLLATE = utf8mb4_0900_ai_ci
        """,
        "SET FOREIGN_KEY_CHECKS = 1"
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Executando script SQL para criação da tabela agendamento")
        
        for sql in sql_statements:
            if sql.strip():
                cursor.execute(sql.strip())
                logger.debug(f"Executado: {sql[:50]}...")
        
        conn.commit()
        
        logger.info("Tabela agendamento criada com sucesso")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Erro ao executar script SQL: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Iniciando execução do script")
    success = execute_sql_script()
    
    if success:
        logger.info("Script executado com sucesso")
    else:
        logger.error("Falha ao executar o script")
