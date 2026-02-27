-- ===================================================================
-- Script de População do Banco de Dados - SerPleno
-- Railway MySQL - Dados Iniciais
-- ===================================================================
-- Este script deve ser executado APÓS a criação das tabelas (ser_pleno.sql)
-- Executar: mysql -u <user> -p -h <host> <database> < populate_database.sql
-- ===================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

USE `ser_pleno`;

-- ===================================================================
-- USUÁRIOS DO SISTEMA (Django Auth)
-- ===================================================================

-- Usuário Administrador
INSERT INTO `auth_user` (`id`, `password`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `is_superuser`, `date_joined`) VALUES
(1, 'pbkdf2_sha256$870000$defaultadminpassword', 'admin', 'Administrador', 'Sistema', 'admin@serpleno.com', 1, 1, 1, NOW());

-- Usuário Psicólogo (analista1)
INSERT INTO `auth_user` (`id`, `password`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `is_superuser`, `date_joined`) VALUES
(2, 'pbkdf2_sha256$870000$defaultpsicologopassword', 'psicologo1', 'Dra. Maria', 'Santos', 'psicologo@serpleno.com', 1, 1, 0, NOW());

-- Usuário Coordenador
INSERT INTO `auth_user` (`id`, `password`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `is_superuser`, `date_joined`) VALUES
(3, 'pbkdf2_sha256$870000$defaultcoordenadorpassword', 'coordenador1', 'João', 'Silva', 'coordenador@serpleno.com', 1, 1, 0, NOW());

-- ===================================================================
-- PERFIS DE USUÁRIO
-- ===================================================================

-- Admin perfil
INSERT INTO `user_profile` (`id`, `user_id`, `role`, `permissions`) VALUES
(1, 1, 'admin', JSON_ARRAY());

-- Psicólogo perfil
INSERT INTO `user_profile` (`id`, `user_id`, `role`, `permissions`) VALUES
(2, 2, 'psicologo', JSON_ARRAY());

-- Coordenador perfil
INSERT INTO `user_profile` (`id`, `user_id`, `role`, `permissions`) VALUES
(3, 3, 'coordenador', JSON_ARRAY());

-- ===================================================================
-- ANALISTAS (Psicólogos/Profissionais)
-- ===================================================================

INSERT INTO `analista` (`id`, `nome`, `email`, `user_id`) VALUES
(1, 'Dra. Maria Santos', 'psicologo@serpleno.com', 2),
(2, 'Dr. Pedro Oliveira', 'pedro.oliveira@serpleno.com', NULL),
(3, 'Dra. Carla Rodrigues', 'carla.rodrigues@serpleno.com', NULL);

-- ===================================================================
-- COORDENAÇÃO
-- ===================================================================

INSERT INTO `coordenacao` (`id`, `nome`, `email`, `user_id`) VALUES
(1, 'João Silva', 'coordenador@serpleno.com', 3),
(2, 'Ana Pereira', 'ana.pereira@serpleno.com', NULL);

-- ===================================================================
-- ESTUDANTES (ALUNOS)
-- ===================================================================

INSERT INTO `aluno` (`id`, `nome`, `sala`, `curso`, `professor_responsavel`, `age`, `phone`, `status`, `has_medical_report`, `requires_attention`, `attention_reason`, `priority_level`, `emergency_contact`, `emergency_phone`, `enrollment_date`) VALUES
(1, 'Ana Carolina Silva', 'Turma A', 'Psicologia', 'Dra. Maria Santos', 20, '11999990001', 'ativo', 1, 1, 'Acompanhamento psicológico contínuo', 2, 'Carlos Silva', '11988880001', '2024-02-15'),
(2, 'Bruno Oliveira Santos', 'Turma B', 'Engenharia Civil', 'Dra. Maria Santos', 22, '11999990002', 'ativo', 0, 0, '', 0, 'Marcia Oliveira', '11988880002', '2024-02-15'),
(3, 'Carla Mendes Costa', 'Turma A', 'Medicina', 'Dr. Pedro Oliveira', 21, '11999990003', 'ativo', 1, 1, 'Necessita de suporte acadêmico especial', 3, 'Roberto Costa', '11988880003', '2024-02-15'),
(4, 'Daniel Ferreira Lima', 'Turma C', 'Direito', 'Dra. Carla Rodrigues', 23, '11999990004', 'ativo', 0, 0, '', 0, 'Julia Lima', '11988880004', '2024-02-15'),
(5, 'Eduarda Almeida Souza', 'Turma B', 'Arquitetura', 'Dra. Maria Santos', 19, '11999990005', 'ativo', 1, 0, '', 1, 'Paulo Souza', '11988880005', '2024-02-15'),
(6, 'Felipe Rodrigues', 'Turma A', 'Engenharia de Produção', 'Dr. Pedro Oliveira', 21, '11999990006', 'ativo', 0, 0, '', 0, 'Amanda Rodrigues', '11988880006', '2024-02-15'),
(7, 'Gabriela Ferreira', 'Turma C', 'Pedagogia', 'Dra. Carla Rodrigues', 20, '11999990007', 'ativo', 0, 1, 'Dificuldades de adaptação', 2, 'Ricardo Ferreira', '11988880007', '2024-02-15'),
(8, 'Henrique Costa', 'Turma B', 'Engenharia Elétrica', 'Dra. Maria Santos', 22, '11999990008', 'ativo', 0, 0, '', 0, 'Beatriz Costa', '11988880008', '2024-02-15'),
(9, 'Isabela Dias', 'Turma A', 'Nutrição', 'Dr. Pedro Oliveira', 20, '11999990009', 'ativo', 0, 0, '', 0, 'Carlos Dias', '11988880009', '2024-02-15'),
(10, 'João Pedro Martins', 'Turma C', 'Ciências Contábeis', 'Dra. Carla Rodrigues', 24, '11999990010', 'ativo', 1, 0, '', 1, 'Fernanda Martins', '11988880010', '2024-02-15'),
(11, 'Karine Souza', 'Turma A', 'Farmácia', 'Dra. Maria Santos', 21, '11999990011', 'ativo', 0, 0, '', 0, 'Marcos Souza', '11988880011', '2024-02-15'),
(12, 'Leonardo Almeida', 'Turma B', 'Engenharia Mecânica', 'Dr. Pedro Oliveira', 23, '11999990012', 'ativo', 0, 0, '', 0, 'Patrícia Almeida', '11988880012', '2024-02-15'),
(13, 'Mariana Castro', 'Turma C', 'Biologia', 'Dra. Carla Rodrigues', 20, '11999990013', 'ativo', 0, 0, '', 0, 'Roberto Castro', '11988880013', '2024-02-15'),
(14, 'Nicolas Ribeiro', 'Turma A', 'Física', 'Dra. Maria Santos', 22, '11999990014', 'ativo', 0, 0, '', 0, 'Carla Ribeiro', '11988880014', '2024-02-15'),
(15, 'Olivia Batista', 'Turma B', 'Química', 'Dr. Pedro Oliveira', 21, '11999990015', 'ativo', 0, 0, '', 0, 'André Batista', '11988880015', '2024-02-15');

-- ===================================================================
-- HORÁRIOS DISPONÍVEIS
-- ===================================================================

INSERT INTO `disponibilidade` (`id`, `dias`, `horario`, `analista_id`, `is_active`) VALUES
(1, 'Segunda', '08:00:00', 1, 1),
(2, 'Segunda', '09:00:00', 1, 1),
(3, 'Segunda', '10:00:00', 1, 1),
(4, 'Segunda', '14:00:00', 1, 1),
(5, 'Segunda', '15:00:00', 1, 1),
(6, 'Terça', '08:00:00', 2, 1),
(7, 'Terça', '09:00:00', 2, 1),
(8, 'Terça', '10:00:00', 2, 1),
(9, 'Terça', '14:00:00', 1, 1),
(10, 'Terça', '15:00:00', 1, 1),
(11, 'Quarta', '08:00:00', 1, 1),
(12, 'Quarta', '09:00:00', 1, 1),
(13, 'Quarta', '10:00:00', 3, 1),
(14, 'Quarta', '14:00:00', 3, 1),
(15, 'Quarta', '15:00:00', 3, 1),
(16, 'Quinta', '08:00:00', 2, 1),
(17, 'Quinta', '09:00:00', 2, 1),
(18, 'Quinta', '10:00:00', 1, 1),
(19, 'Quinta', '14:00:00', 1, 1),
(20, 'Quinta', '15:00:00', 1, 1),
(21, 'Sexta', '08:00:00', 1, 1),
(22, 'Sexta', '09:00:00', 3, 1),
(23, 'Sexta', '10:00:00', 3, 1),
(24, 'Sexta', '14:00:00', 3, 1);

-- ===================================================================
-- FORMULÁRIOS DE TRIAGEM
-- ===================================================================

INSERT INTO `desktop_screeningform` (`id`, `name`, `description`, `questions`, `is_active`, `created_at`, `updated_at`, `created_by_id`) VALUES
(1, 'Triagem Inicial', 'Formulário de triagem inicial para novos estudantes', 
    JSON_ARRAY(
        JSON_OBJECT('id', 'q1', 'question', 'Como você está se sentindo hoje?', 'type', 'mood_scale', 'required', true),
        JSON_OBJECT('id', 'q2', 'question', 'Você está tendo dificuldades nos estudos?', 'type', 'yes_no', 'required', true),
        JSON_OBJECT('id', 'q3', 'question', 'Descreva brevemente seus principais desafios:', 'type', 'text', 'required', false),
        JSON_OBJECT('id', 'q4', 'question', 'Você tem se sentido ansioso(a)?', 'type', 'scale_1_5', 'required', true),
        JSON_OBJECT('id', 'q5', 'question', 'Você tem dormido bem?', 'type', 'yes_no', 'required', true),
        JSON_OBJECT('id', 'q6', 'question', 'Está havendo alguma mudança significativa na sua vida?', 'type', 'text', 'required', false)
    ),
    1, NOW(), NOW(), 2);

INSERT INTO `desktop_screeningform` (`id`, `name`, `description`, `questions`, `is_active`, `created_at`, `updated_at`, `created_by_id`) VALUES
(2, 'Acompanhamento Mensal', 'Formulário de acompanhamento mensal de estudantes', 
    JSON_ARRAY(
        JSON_OBJECT('id', 'q1', 'question', 'Como foi seu mês em relação ao bem-estar?', 'type', 'mood_scale', 'required', true),
        JSON_OBJECT('id', 'q2', 'question', 'Você manteve suas metas acadêmicas?', 'type', 'yes_no', 'required', true),
        JSON_OBJECT('id', 'q3', 'question', 'Você参加了 alguna atividade extracurricular?', 'type', 'yes_no', 'required', false),
        JSON_OBJECT('id', 'q4', 'question', 'Nível de estresse (1-5):', 'type', 'scale_1_5', 'required', true),
        JSON_OBJECT('id', 'q5', 'question', 'Observações adicionais:', 'type', 'text', 'required', false)
    ),
    1, NOW(), NOW(), 2);

-- ===================================================================
-- TRIAGENS (Alguns exemplos)
-- ===================================================================

INSERT INTO `desktop_screening` (`id`, `status`, `priority`, `scheduled_date`, `completed_date`, `responses`, `score`, `observations`, `recommendations`, `requires_followup`, `followup_date`, `created_at`, `updated_at`, `conducted_by_id`, `student_id`, `form_id`) VALUES
(1, 'completed', 'high', '2025-02-01', '2025-02-01', 
    JSON_OBJECT('q1', 2, 'q2', true, 'q3', 'Dificuldade em organizar estudos', 'q4', 4, 'q5', false),
    65, 'Estudante demonstra ansiedade moderada. Dificuldades com organização.', 'Sessões semanais recomendadas', 1, '2025-02-15', NOW(), NOW(), 2, 1, 1);

INSERT INTO `desktop_screening` (`id`, `status`, `priority`, `scheduled_date`, `completed_date`, `responses`, `score`, `observations`, `recommendations`, `requires_followup`, `followup_date`, `created_at`, `updated_at`, `conducted_by_id`, `student_id`, `form_id`) VALUES
(2, 'completed', 'normal', '2025-02-05', '2025-02-05', 
    JSON_OBJECT('q1', 4, 'q2', false, 'q3', '', 'q4', 2, 'q5', true),
    85, 'Tudo bem, mas questões de sono precisam de atenção.', 'Boas práticas de higiene do sono', 0, NULL, NOW(), NOW(), 2, 2, 1);

-- ===================================================================
-- INTERVENÇÕES (Alguns exemplos)
-- ===================================================================

INSERT INTO `desktop_intervention` (`id`, `date`, `created_at`, `student_id`, `conducted_by_id`, `duration_minutes`, `follow_up_completed`, `follow_up_date`, `follow_up_required`, `intervention_notes`, `intervention_type`, `is_confidential`, `outcome`, `outcome_notes`, `tags`) VALUES
(1, '2025-02-10', NOW(), 1, 2, 60, 0, '2025-02-24', 1, 'Sessão de acompanhamento. Estudante demonstrou progresso significativo.', 'counseling', 0, 'positive', 'Excelente evolução no enfrentamento da ansiedade.', JSON_ARRAY('ansiedade', 'acompanhamento')),
(2, '2025-02-12', NOW(), 7, 2, 45, 0, '2025-02-26', 1, 'Avaliação inicial. Dificuldades de adaptação ao ambiente universitário.', 'counseling', 0, 'needs_followup', 'Plano de adaptação sugerido.', JSON_ARRAY('adaptação', 'inicial'));

-- ===================================================================
-- METAS (Alguns exemplos)
-- ===================================================================

INSERT INTO `desktop_goal` (`id`, `created_at`, `updated_at`, `title`, `description`, `category`, `priority`, `status`, `target_date`, `completed_date`, `progress_percentage`, `notes`, `success_criteria`, `created_by_id`, `student_id`) VALUES
(1, NOW(), NOW(), 'Melhorar organização de estudos', 'Criar rotina de estudos mais estruturada', 'academic', 'alta', 'in_progress', '2025-03-15', NULL, 50, 'Estudante está implementando quadro de horários', '至少 3 dias por semana de estudo estruturado', 2, 1),
(2, NOW(), NOW(), 'Reduzir níveis de ansiedade', 'Práticas diárias de mindfulness e respiração', 'emotional', 'media', 'pendente', '2025-04-01', NULL, 25, 'Iniciado exercícios de respiração', 'Redução de 50% nos níveis de ansiedade', 2, 1),
(3, NOW(), NOW(), 'Desenvolvimento de habilidades sociais', 'Participar de atividades em grupo', 'social', 'media', 'pendente', '2025-05-01', NULL, 0, '', 'Participar de pelo menos 2 eventos sociais', 2, 7);

-- ===================================================================
-- REGISTROS DE HUMOR
-- ===================================================================

INSERT INTO `desktop_moodentry` (`id`, `created_at`, `mood_level`, `mood_emoji`, `energy_level`, `stress_level`, `sleep_quality`, `notes`, `triggers`, `activities`, `entry_date`, `entry_time`, `recorded_by_id`, `student_id`) VALUES
(1, NOW(), 3, '😐', 3, 4, 3, 'Dia comum de estudos', JSON_ARRAY('provas'), JSON_ARRAY('aula', 'biblioteca'), '2025-02-20', '20:00:00', NULL, 1),
(2, NOW(), 4, '😊', 4, 2, 4, 'Bom dia produtivo', JSON_ARRAY(), JSON_ARRAY('esporte', 'estudos'), '2025-02-21', '21:00:00', NULL, 1),
(3, NOW(), 2, '😕', 2, 5, 2, 'Estressado com deadlines', JSON_ARRAY('trabalho', 'provas'), JSON_ARRAY('estudos'), '2025-02-22', '22:00:00', NULL, 1);

-- ===================================================================
-- CHECK-INS DE BEM-ESTAR
-- ===================================================================

INSERT INTO `desktop_wellnesscheckin` (`id`, `created_at`, `check_in_type`, `check_in_date`, `overall_wellbeing`, `responses`, `attention_areas`, `recommendations`, `follow_up_needed`, `follow_up_date`, `professional_notes`, `conducted_by_id`, `student_id`) VALUES
(1, NOW(), 'weekly', '2025-02-15', 7, 
    JSON_OBJECT('satisfaction', 7, 'sleep_quality', 6, 'social_connection', 8),
    JSON_ARRAY('sono'),
    'Continuar trabalhando na rotina de sono',
    1, '2025-02-22', 'Boa evolução geral', 2, 1);

-- ===================================================================
-- ALERTAS
-- ===================================================================

INSERT INTO `desktop_alert` (`id`, `alert_type`, `severity`, `message`, `details`, `is_read`, `is_resolved`, `resolved_at`, `created_at`, `assigned_to_id`, `resolved_by_id`, `student_id`) VALUES
(1, 'screening_pending', 'warning', 'Triagem pendente para Ana Carolina Silva', JSON_OBJECT('form', 'Triagem Inicial'), 0, 0, NULL, NOW(), 2, NULL, 1),
(2, 'followup_required', 'info', 'Acompanhamento agendado para esta semana', JSON_OBJECT('date', '2025-02-24'), 0, 0, NULL, NOW(), 2, NULL, 1),
(3, 'high_risk', 'critical', 'Estudante requer atenção imediata', JSON_OBJECT('reason', 'Mudanças significativas de comportamento'), 0, 0, NULL, NOW(), 2, NULL, 7);

-- ===================================================================
-- MENSAGENS
-- ===================================================================

INSERT INTO `desktop_message` (`id`, `sender_id`, `text`, `timestamp`, `read`, `caminho_arquivo`, `tipo_arquivo`, `recipient_id`) VALUES
(1, 2, 'Olá! Gostaria de lembrá-la sobre nossa sessão agendada para amanhã às 14h.', NOW(), 1, NULL, NULL, NULL),
(2, 2, 'Segue o material de apoio que mencionamos na última sessão.', NOW(), 0, 'material_apoio.pdf', 'application/pdf', NULL),
(3, 3, 'Por favor, confirmar presença na reunião de coordenação amanhã.', NOW(), 0, NULL, NULL, 2);

-- ===================================================================
-- ORIENTAÇÕES
-- ===================================================================

INSERT INTO `desktop_orientation` (`id`, `created_at`, `updated_at`, `title`, `theme`, `session_date`, `content`, `is_markdown`, `motivational_message`, `action_plan`, `psychologist_id`, `student_id`) VALUES
(1, NOW(), NOW(), 'Estratégias de Estudo', 'Desenvolvimento Acadêmico', '2025-02-10', 
    '# Estratégias de Estudo Eficientes\n\n## Pomodoro\nUse a técnica Pomodoro: 25 minutos de estudo + 5 minutos de pausa.\n\n## Organize seu ambiente\n- Local silencioso\n- Materiais organizados\n- Sem distrações\n\n## Metas diárias\nDefina 3 principais tarefas para cada dia.', 
    1, 'Lembre-se: pequenas melhorias diárias levam a grandes resultados! Continue assim! 💪', 
    JSON_ARRAY(JSON_OBJECT('text', 'Criar quadro de horários', 'done', true), JSON_OBJECT('text', 'Baixar app Pomodoro', 'done', false), JSON_OBJECT('text', 'Definir local de estudos', 'done', true)),
    2, 1);

-- ===================================================================
-- TEMPLATES DE RELATÓRIOS
-- ===================================================================

INSERT INTO `desktop_reporttemplate` (`id`, `name`, `report_type`, `description`, `template_config`, `default_parameters`, `is_active`, `created_at`, `created_by_id`) VALUES
(1, 'Relatório Geral de Atendimentos', 'general', 'Relatório consolidado de todos os atendimentos do período',
    JSON_OBJECT('sections', JSON_ARRAY('resumo', 'atendimentos', 'intervencoes', 'recomendacoes')),
    JSON_OBJECT('periodo', 'mensal', 'incluir_graficos', true),
    1, NOW(), 2),
(2, 'Relatório de Estudante', 'student', 'Relatório detalhado de um estudante específico',
    JSON_OBJECT('sections', JSON_ARRAY('dados_pessoais', 'historico', 'triagens', 'intervencoes', 'metas')),
    JSON_OBJECT('incluir_documentos', true, 'incluir_graficos', true),
    1, NOW(), 2);

-- ===================================================================
-- MURAL (Posts)
-- ===================================================================

INSERT INTO `mural_posts` (`id`, `created_at`, `updated_at`, `titulo`, `conteudo`, `autor`, `publicado_em`, `ativo`, `categoria`, `link_externo`, `layout`) VALUES
(1, NOW(), NOW(), 'Bem-vindos ao Semestre!', 'Olá comunidade acadêmica! Desejamos um excelente semestre a todos. Estamos aqui para apoiá-los em sua jornada.', 'Equipe SerPleno', NOW(), 1, 'geral', NULL, 'padrao'),
(2, NOW(), NOW(), 'Workshop de Gestão do Estresse', 'No dia 15/03 realizaremos um workshop sobre técnicas de gerenciamento do estresse. Inscreva-se!', 'Dra. Maria Santos', NOW(), 1, 'evento', NULL, 'padrao'),
(3, NOW(), NOW(), 'Horário de Atendimento Atualizado', 'Novo horário de atendimento a partir de Fevereiro. Confiram os novos horários disponíveis.', 'Coordenação', NOW(), 1, 'informativo', NULL, 'padrao');

-- ===================================================================
-- RECURSOS GUIADOS
-- ===================================================================

INSERT INTO `guided_resource` (`id`, `key`, `title`, `icon`, `duration`, `category`, `content`, `video_url`, `share_url`) VALUES
(1, 'breathing-101', 'Técnicas de Respiração', '🧘', '10 min', 'bem-estar', 'Guia completo de técnicas de respiração para redução do estresse e ansiedade.', NULL, NULL),
(2, 'meditation-basics', 'Meditação para Iniciantes', '🧘‍♀️', '15 min', 'bem-estar', 'Introdução à prática de meditação mindfulness.', NULL, NULL),
(3, 'study-organization', 'Organização de Estudos', '📚', '20 min', 'acadêmico', 'Dicas e técnicas para organizar seus estudos de forma eficiente.', NULL, NULL),
(4, 'stress-management', 'Gerenciamento do Estresse', '💆', '25 min', 'bem-estar', 'Estratégias práticas para lidar com o estresse acadêmico.', NULL, NULL);

-- ===================================================================
-- CONQUISTAS (BADGES)
-- ===================================================================

INSERT INTO `badge` (`id`, `key`, `title`, `icon`, `description`) VALUES
(1, 'first-checkin', 'Primeiro Check-in', '🌟', 'Completou seu primeiro check-in de bem-estar'),
(2, 'week-streak', 'Sequência de 7 Dias', '🔥', 'Registrou seu humor por 7 dias consecutivos'),
(3, 'goal-achiever', 'Conquistador de Metas', '🏆', 'Completou sua primeira meta'),
(4, 'engaged-student', 'Estudante Engajado', '📖', 'Participou de 5 ou mais sessões');

-- ===================================================================
-- DESAFIOS (CHALLENGES)
-- ===================================================================

INSERT INTO `challenge` (`id`, `key`, `title`, `description`, `xp`) VALUES
(1, 'daily-mood', 'Registro Diário', 'Registre seu humor todos os dias por uma semana', 50),
(2, 'goal-setter', 'Definidor de Metas', 'Crie pelo menos 3 metas para este mês', 30),
(3, 'mindful-week', 'Semana Mindfulness', 'Pratique técnicas de relaxamento por 5 dias', 75);

-- ===================================================================
-- GAMIFICAÇÃO (Exemplo para um aluno)
-- ===================================================================

INSERT INTO `gamificacao` (`id`, `pontos_atuais`, `nivel`, `conquistas`, `check_in`, `metas_pessoais`, `last_check_in_date`, `aluno_id`) VALUES
(1, 150, 2, 'first-checkin,week-streak', 5, 'meta_1,meta_2', '2025-02-20', 1);

-- ===================================================================
-- AUTOAVALIAÇÃO (Exemplo)
-- ===================================================================

INSERT INTO `autoavaliacao` (`id`, `data_avaliacao`, `bem_estar_academico`, `bem_estar_emocional`, `bem_estar_social`, `reflexoes_pessoais`, `pontos_xp`, `aluno_id`) VALUES
(1, '2025-02-15', 'Bom', 'Regular', 'Bom', 'Preciso melhorar a organização dos estudos', 25, 1),
(2, '2025-02-20', 'Bom', 'Bom', 'Ótimo', 'Mês muito produtivo!', 30, 1);

-- ===================================================================
-- HISTÓRICO DO ALUNO
-- ===================================================================

INSERT INTO `meu_historico` (`id`, `humor_media`, `dias_consecutivos`, `total_registros`, `aluno_id`) VALUES
(1, 3.50, 10, 15, 1),
(2, 3.80, 5, 8, 2);

-- ===================================================================
-- REGISTROS DIÁRIOS (Exemplos)
-- ===================================================================

INSERT INTO `registros_diarios` (`id`, `data_registro`, `humor`, `historico_id`) VALUES
(1, '2025-02-18', 'Bom', 1),
(2, '2025-02-19', 'Regular', 1),
(3, '2025-02-20', 'Bom', 1);

-- ===================================================================
-- PEDIDOS DE AJUDA
-- ===================================================================

INSERT INTO `help_requests` (`id`, `tipo`, `mensagem`, `prioridade`, `status`, `localizacao`, `dados_extras`, `created_at`, `viewed_at`, `resolved_at`, `aluno_id`, `updated_at`) VALUES
(1, 'academico', 'Preciso de ajuda para organizar minha rotina de estudos', 'normal', 'pendente', 'Biblioteca Central', JSON_OBJECT('materia', 'Geral'), NOW(), NULL, NULL, 1, NOW()),
(2, 'emocional', 'Estou me sentindo muito ansioso com as provas', 'high', 'em_andamento', 'Sala de apoio', JSON_OBJECT('prova', 'Cálculo 1'), NOW(), NOW(), NULL, 7, NOW());

-- ===================================================================
-- RESTAURAR CONFIGURAÇÕES
-- ===================================================================

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- ===================================================================
-- FIM DO SCRIPT
-- ===================================================================
-- Execute este script após ser_pleno.sql
-- Verifique se os dados foram inseridos corretamente
-- ===================================================================
