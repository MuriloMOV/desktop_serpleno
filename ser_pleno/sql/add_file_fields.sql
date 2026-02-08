-- Adiciona campos para armazenamento de arquivos na tabela desktop_message
ALTER TABLE `ser_pleno`.`desktop_message` 
ADD COLUMN `caminho_arquivo` VARCHAR(500) NULL AFTER `read`,
ADD COLUMN `tipo_arquivo` VARCHAR(50) NULL AFTER `caminho_arquivo`;