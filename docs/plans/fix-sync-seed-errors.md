# Plano de Correção - Erros de Sincronização e Seed

**Data**: 2026-08-16  
**Projeto**: desktop_serpleno  
**Modo**: db_primary  

## Racional Arquitetural

O sistema opera em modo `db_primary` onde MySQL é a fonte da verdade. Quando MySQL fica indisponível, operações de escrita são enfileiradas e aplicadas como fallback local (SQLite). Quando MySQL volta, a fila é aplicada no MySQL e um seed rebaseia dados do MySQL para o SQLite local.

Os erros no log indicam três classes de falhas:

1. **Schema drift entre MySQL e SQLite**: colunas inexistentes no MySQL sendo usadas no seed (`aluno.email`, `desktop_screeningform.version`).
2. **SQL syntax error**: uso de palavra reservada MySQL (`read`) sem backticks no seed.
3. **Foreign key violations na sync queue**: registros filho (messages, appointments, orientations) são aplicados antes ou sem que os registros pai (auth_user, aluno) existam no MySQL.

## Backlog de Tarefas

### [Execução/Desenvolvimento]

- [x] **T1** Corrigir query de seed de `aluno` que referencia coluna inexistente `a.email`
  - Arquivo: `src/ser_pleno/infrastructure/local/seed_service.py`
  - Causa: coluna `email` pertence a `auth_user`, não a `aluno`
  - Solução: separar colunas de `aluno` das colunas de `auth_user` na construção do SELECT com JOIN

- [x] **T2** Remover coluna `version` do `SEED_COLUMNS` de `desktop_screeningform`
  - Arquivo: `src/ser_pleno/infrastructure/local/seed_service.py`
  - Causa: tabela MySQL `desktop_screeningform` não possui coluna `version` (schema drift)

- [x] **T3** Corrigir reserved word `read` no seed de `desktop_message`
  - Arquivo: `src/ser_pleno/infrastructure/local/seed_service.py`
  - Causa: `read` é palavra reservada MySQL; SELECT sem backticks causa erro 1064

- [x] **T4** Adicionar verificação de existência de FK antes de INSERT no sync_service
  - Arquivo: `src/ser_pleno/infrastructure/api/sync_service.py`
  - Causa: registros filho são aplicados sem garantir que o pai existe no MySQL
  - Solução: para `messages`, verificar `sender_id` e `recipient_id` em `auth_user`; para `appointments`/`orientations`, verificar `student_id` em `aluno`

### [Validação/QA]

- [ ] **V1** Executar seed e validar que `aluno`, `desktop_screeningform` e `desktop_message` não geram erros
- [ ] **V2** Aplicar sync queue e validar que FKs são respeitadas
- [ ] **V3** Verificar logs em cenário de MySQL down/up para confirmar ausência de erros 1452, 1054, 1064

## Critérios de Aceite

- Seed de `aluno` completa sem erro 1054
- Seed de `desktop_screeningform` completa sem erro 1054
- Seed de `desktop_message` completa sem erro 1064
- Sync queue não gera erros 1452 de FK violada
- Logs de seed e sync não contêm mensagens de erro das tabelas acima
