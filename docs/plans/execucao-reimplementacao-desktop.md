# Execução: Reimplementação Desktop Nativa CustomTkinter

**Data:** 2026-08-18  
**Projeto:** `desktop_serpleno`  
**Referência:** `reimplementação-desktop-nativa-customtkinter.md`  
**Status:** Em execução — Fase 1

---

## 1. Estado Atual Real (auditado)

| Métrica | Valor |
|---------|-------|
| Testes passing | 229/229 |
| Views registradas | 19 |
| Features (service+repo) | 18 |
| Domain models | 8 dataclasses mínimas |
| Cobertura de API | ~45 endpoints consumidos de ~336 |
| Arquitetura | Feature-based com fallback API→SQLite |

---

## 2. Gaps Reais (não arquiteturais)

### 2.1 Domain Models — entidades ricas ausentes

| Model | Status | Esforço |
|-------|--------|---------|
| RBAC: UserProfile, Role, Permission, AuditLog | ❌ Ausente | Alto |
| Student com métodos de negócio | ⚠️ Dataclass mínima | Médio |
| Appointment/AvailableTime com estados | ⚠️ Parcial | Médio |
| Intervention com tipos/outcomes/tags | ⚠️ Service existe, model não | Baixo |
| Message com sender/receiver/attachments | ❌ Ausente | Médio |
| ScreeningForm/Screening com score | ❌ Ausente | Alto |
| Report/ReportTemplate com render/export | ⚠️ Service existe, model não | Baixo |
| Alert com is_critical/mark_read/dismiss | ⚠️ Service existe, model não | Baixo |
| Goal/GoalProgress com calculate/check_overdue | ⚠️ Service existe, model não | Baixo |
| MoodEntry/WellnessCheckIn com averages/percentile | ⚠️ Service existe, model não | Baixo |
| WellnessChallenge com assign/complete | ⚠️ Service existe, model não | Baixo |
| Orientation/Template/Theme com publish | ⚠️ Service existe, model não | Baixo |
| SharedClinicalData | ⚠️ Service existe, model não | Baixo |
| MinigameBlockLog | ⚠️ Repo existe, model não | Baixo |
| Notification com mark_read/delete | ⚠️ Service existe, model não | Baixo |
| Base: TimestampMixin, CreatedAtMixin, ActiveMixin | ❌ Ausente | Baixo |

### 2.2 Services — lógica transversal faltante

| Service | Status | Esforço |
|---------|--------|---------|
| `_helpers.py` — paginate_and_serialize, date_to_datetime_range | ❌ Ausente | Baixo |
| `dashboard.py` — build_dashboard_context por role | ❌ Ausente | Médio |
| `serpleno_service.py` — map_humor, risk_level, help_requests | ❌ Ausente | Médio |
| `pdf.py` — geração local de PDF | ❌ Ausente | Alto |
| `exports.py` — batch export helpers | ⚠️ Parcial | Baixo |
| `guidance.py` — publish_if_ready, validate_content | ❌ Ausente | Baixo |
| `_orientation_helpers.py` — theme hierarchy, template validation | ❌ Ausente | Baixo |
| `analytics.py` — search_students, quick_actions, trend_stats | ⚠️ Parcial | Médio |
| `settings.py` — global + user profile settings sync | ❌ Ausente | Médio |
| `signals.py` — sync events, alert triggers | ❌ Ausente | Médio |

### 2.3 UI — fluxos incompletos

| Fluxo | Status | Prioridade |
|-------|--------|-----------|
| Configurações — persistência backend | ❌ UI não consome service | CRÍTICO |
| Agenda — auto-reload após edição de horários | ❌ Síncrono | ALTO |
| Bem-Estar — modal de check-in | ❌ Ausente | CRÍTICO |
| Triagem — listar_formularios não consumida | ❌ Campos hardcoded | MÉDIO |
| Help Requests — actions update/respond | ❌ Ausente | ALTO |
| Notificações — view sem controller/serviço | ❌ Incompleto | ALTO |
| Orientações — duplicar não implementado | ❌ Botão morto | ALTO |
| Relatórios — modal de geração com filtros | ❌ PDF hardcoded | MÉDIO |
| Comunicação — validação de arquivo | ❌ Ausente | MÉDIO |
| Controllers instanciados em dobro | ❌ Inconsistência | BAIXO |
| Datas — normalização dd/mm/aaaa | ❌ Ausente | BAIXO |

### 2.4 Features completamente ausentes

| Feature | Prioridade |
|---------|-----------|
| Wellness Challenges — view dedicada | CRÍTICO |
| Interventions — view dedicada | CRÍTICO |
| Notifications nativa — controller/serviço | ALTO |
| Orientation Templates/Themes — CRUD | MÉDIO |
| Exportação avançada — filtros + múltiplos formatos | MÉDIO |
| Metas — progresso e estatísticas | MÉDIO |
| Busca global | BAIXO |

---

## 3. Fases de Execução

### Fase 1 — Fundação (2–3 semanas)

**Objetivo:** Completar models de domínio e services transversais.

| ID | Tarefa | Categoria | Esforço |
|----|--------|-----------|---------|
| 1.1 | Criar `domain/models/auth.py` — UserProfile, Role, Permission, AuditLog | Models | Alto |
| 1.2 | Expandir `domain/models/estudantes.py` — propriedades e métodos | Models | Médio |
| 1.3 | Expandir `domain/models/dashboard.py` — Appointment com estados | Models | Médio |
| 1.4 | Criar models para Intervention, Message, Screening, Alert, Goal, MoodEntry, WellnessChallenge, Orientation, SharedClinicalData, MinigameBlockLog, Notification | Models | Alto |
| 1.5 | Criar `domain/models/base.py` — TimestampMixin, CreatedAtMixin, ActiveMixin | Models | Baixo |
| 1.6 | Criar `application/services/_helpers.py` — paginate, date_range, cache invalidation | Services | Baixo |
| 1.7 | Expandir `application/services/dashboard.py` — context builders por role | Services | Médio |
| 1.8 | Criar `application/services/serpleno_service.py` — integração mobile | Services | Médio |
| 1.9 | Criar `application/services/pdf.py` — geração local de PDF | Services | Alto |
| 1.10 | Expandir `application/services/settings.py` — global + user profile | Services | Médio |

### Fase 2 — Funcionalidades Core (4–5 semanas)

**Objetivo:** Completar fluxos UI e features faltantes.

| ID | Tarefa | Categoria | Esforço |
|----|--------|-----------|---------|
| 2.1 | Configurações — conectar UI ao service | UI | CRÍTICO |
| 2.2 | Agenda — auto-reload async + callback-aware | UI | ALTO |
| 2.3 | Bem-Estar — modal de check-in | UI | CRÍTICO |
| 2.4 | Triagem — consumir listar_formularios + normalizar datas | UI | MÉDIO |
| 2.5 | Help Requests — actions update/respond | UI | ALTO |
| 2.6 | Notificações — controller + serviço nativo | UI | ALTO |
| 2.7 | Orientações — implementar duplicar | UI | ALTO |
| 2.8 | Relatórios — modal de geração com filtros | UI | MÉDIO |
| 2.9 | Comunicação — validação de arquivo + feedback | UI | MÉDIO |
| 2.10 | Wellness Challenges — view dedicada | UI | CRÍTICO |
| 2.11 | Interventions — view dedicada | UI | CRÍTICO |
| 2.12 | Analytics — search_students + quick_actions | Services | MÉDIO |
| 2.13 | Exportação — filtros + múltiplos formatos UI | UI | MÉDIO |
| 2.14 | Metas — progresso e estatísticas UI | UI | MÉDIO |
| 2.15 | Orientation Templates/Themes — CRUD UI | UI | MÉDIO |

### Fase 3 — Acessibilidade (2–3 semanas)

**Objetivo:** Polimento, logs, seeds, migrations.

| ID | Tarefa | Categoria | Esforço |
|----|--------|-----------|---------|
| 3.1 | Signals — sync events e alert triggers | Backend | Médio |
| 3.2 | Management commands — cleanup, setup | Backend | Baixo |
| 3.3 | Seeds iniciais — RBAC + Templates | Backend | Baixo |
| 3.4 | Migrations versionadas para SQLite | Backend | Médio |
| 3.5 | Logs estruturados + audit decorators | Backend | Baixo |
| 3.6 | Controllers duplicados — remover instanciações internas | Arquitetura | Baixo |
| 3.7 | Normalização de datas — parser dd/mm/aaaa | Utils | Baixo |

### Fase 4 — Polimento (2 semanas)

**Objetivo:** Features avançadas e UX.

| ID | Tarefa | Categoria | Esforço |
|----|--------|-----------|---------|
| 4.1 | WebSocket opcional — chat em tempo real | Infra | Alto |
| 4.2 | Onboarding tour | UI | Baixo |
| 4.3 | Busca global | UI | Baixo |
| 4.4 | Quick actions | UI | Baixo |
| 4.5 | Anexos em orientações | UI | Médio |
| 4.6 | Notificações desktop nativas | UI | Baixo |
| 4.7 | Service Worker / Push notifications | Infra | Baixo |

---

## 4. Backlog Executivo

### Sprint 1 (Semana 1)
- [ ] **1.1** RBAC domain models
- [ ] **1.5** Base models (mixins)
- [ ] **1.6** Services helpers
- [ ] **2.1** Configurações — conectar UI

### Sprint 2 (Semana 2)
- [ ] **1.2** Student model expandido
- [ ] **1.3** Appointment model com estados
- [ ] **1.4** Models restantes (Intervention, Message, Screening, Alert, Goal, MoodEntry, WellnessChallenge, Orientation, SharedClinicalData, MinigameBlockLog, Notification)
- [ ] **2.3** Bem-Estar — modal check-in

### Sprint 3 (Semana 3)
- [ ] **1.7** Dashboard context builders
- [ ] **1.8** SerPleno integration service
- [ ] **1.10** Settings service
- [ ] **2.2** Agenda — auto-reload async
- [ ] **2.7** Orientações — duplicar

### Sprint 4 (Semana 4)
- [ ] **1.9** PDF generation
- [ ] **2.4** Triagem — formulários dinâmicos
- [ ] **2.5** Help Requests — actions
- [ ] **2.6** Notificações — controller/serviço

### Sprint 5 (Semana 5)
- [ ] **2.8** Relatórios — modal com filtros
- [ ] **2.9** Comunicação — validação arquivo
- [ ] **2.12** Analytics — search + quick actions
- [ ] **2.13** Exportação — filtros UI

### Sprint 6 (Semana 6)
- [ ] **2.10** Wellness Challenges — view dedicada
- [ ] **2.11** Interventions — view dedicada
- [ ] **2.14** Metas — progresso UI
- [ ] **2.15** Orientation Templates/Themes

### Sprint 7 (Semana 7)
- [ ] **3.1** Signals — sync events
- [ ] **3.2** Management commands
- [ ] **3.3** Seeds iniciais
- [ ] **3.6** Controllers duplicados — fix
- [ ] **3.7** Normalização de datas

### Sprint 8 (Semana 8)
- [ ] **3.4** Migrations versionadas
- [ ] **3.5** Logs + audit decorators
- [ ] **4.1** WebSocket opcional
- [ ] **4.2** Onboarding tour
- [ ] **4.3** Busca global
- [ ] **4.4** Quick actions
- [ ] **4.5** Anexos orientações
- [ ] **4.6** Notificações desktop
- [ ] **4.7** Service Worker

---

## 5. Critérios de Aceite

### Fase 1
- [ ] Todos os domain models com métodos de negócio
- [ ] Services helpers e context builders implementados
- [ ] PDF generation local funcionando
- [ ] Cobertura de testes ≥ 85%
- [ ] Sem erros de lint (ruff)
- [ ] Sem erros de tipo (mypy)

### Fase 2
- [ ] Todos os fluxos UI incompletos resolvidos
- [ ] Wellness Challenges e Interventions com views dedicadas
- [ ] Notificações nativas implementadas
- [ ] Cobertura de testes ≥ 90%
- [ ] Documentação atualizada

### Fase 3
- [ ] Signals e eventos implementados
- [ ] Seeds e migrations funcionando
- [ ] Logs estruturados + audit decorators
- [ ] Cobertura de testes ≥ 92%

### Fase 4
- [ ] Features avançadas implementadas
- [ ] UX polido (animações, transições, feedback)
- [ ] Build executável testado
- [ ] Cobertura de testes ≥ 95%

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|--------|--------------|---------|-----------|
| Complexidade de models ricos | Média | Médio | Implementar incrementalmente, manter dataclasses como base |
| PDF generation — dependências | Baixa | Médio | Usar `fpdf2` ou `reportlab`; fallback para API |
| UI refatoring — quebra de funcionalidade | Média | Alto | Testes manuais após cada mudança; manter fallback |
| Mudanças no schema web | Média | Alto | Versionar API + adapter pattern |
| Performance com models ricos | Baixa | Baixo | Cache + lazy loading |

---

## 7. Próximos Passos Imediatos

1. ✅ **Análise concluída** — gaps mapeados e documentados
2. ✅ **RBAC domain models** — `UserProfile`, `Role`, `Permission`, `AuditLog` criados em `src/ser_pleno/domain/models/auth.py`
3. ✅ **RBAC enforcement em UI** — helper `require_permission` e integração nas views `estudantes`, `agenda`, `relatorio`, `configuracoes`
4. ✅ **Exportação batch avançada** — `exportar_lote` implementado em `ServicoRelatorio` com suporte a multi-formato e ZIP
5. ✅ **Migrations versionadas SQLite** — 10 migrations + manager + comando CLI
6. ✅ **Analytics avançado** — retention, conversão, jornada, horários pico, carga psicólogos, predição falta
7. ✅ **Build spec atualizado** — `reportlab` adicionado aos hiddenimports do PyInstaller

**Próxima etapa recomendada:**
- **Build executável** — executar `python -m PyInstaller --clean --noconfirm SerPleno.spec` e validar app empacotado
- **QA funcional** — rodar `runners/run_ui_tests.py` em ambiente limpo
- **Release** — criar tag e publicar em `releases/`

---

## 8. Progresso Recente (2026-08-19)

| Tarefa | Status | Arquivo(s) |
|--------|--------|------------|
| Exportação batch avançada | ✅ Concluído | `src/ser_pleno/features/relatorio/service.py` |
| RBAC enforcement em UI | ✅ Concluído | `src/ser_pleno/ui/rbac.py`, views atualizadas |
| Migrations versionadas SQLite | ✅ Concluído | `infrastructure/local/migrations/`, `manager.py`, `run_migrations.py` |
| Analytics avançado | ✅ Concluído | `features/analytics/service.py`, `repo.py`, `ui/views/analytics.py` |
| Correção de erros residuais | ✅ Concluído | `configuracoes.py`, `relatorio.py`, `estudantes.py` |
| Build executável | ✅ Concluído | `dist/SerPleno.exe`, `releases/SerPleno-2026-08-19.exe` |
| QA funcional UI heavy | ✅ Concluído | `tests/test_qa_interacoes.py` — 79 passed |

### Detalhes da Exportação Batch
- Método `exportar_lote(tipos, filtros, formato)` adicionado a `ServicoRelatorio`
- Suporta: `students`, `appointments`, `screenings`, `interventions`
- Gera ZIP com CSVs/JSONs/XLSX individuais
- Valida filtros antes de processar
- Limite de 10k registros por exportação

### Detalhes do RBAC
- Helper `require_permission(permission_code)` criado em `ui/rbac.py`
- Funções auxiliares: `has_permission`, `can_access_screen`, `apply_rbac_to_button`, `apply_rbac_to_widget`
- Cache de permissões por usuário (`_permission_cache`)
- Integrado nas views: `estudantes`, `agenda`, `relatorio`, `configuracoes`

### Detalhes do Build
- Executável gerado: `dist/SerPleno.exe` (~55 MB)
- Copiado para `releases/SerPleno-2026-08-19.exe`
- `reportlab` adicionado aos hiddenimports do PyInstaller
- Dependências verificadas: todas as 33 dependências críticas presentes

### Detalhes das Correções Residuais
- `configuracoes.py`: import de `_ErrorModal` movido para o topo; imports locais removidos
- `relatorio.py`: variável `auth_service` não usada removida
- `estudantes.py`: variável ambígua `l` renomeada para `log_item`
- `orientacoes/service.py`: duplicação de `usar_template` removida; ruff limpo
- `local_cache.py`: alias `_ensure_tables()` mantido para compatibilidade com testes existentes

### Detalhes das Migrations SQLite
- 10 migrations versionadas em `infrastructure/local/migrations/`
- Manager com `migrate()`, `apply_migration()`, `get_applied_migrations()`
- Comando CLI `run_migrations.py` com opção `--apply`
- `LocalCache` agora usa migrations; `_ensure_tables()` mantido como alias

### Detalhes do Analytics Avançado
- `calculate_retention_rate(start_date, end_date)`
- `calculate_conversion_rate(stage_from, stage_to, date_range)`
- `get_student_journey(student_id)` — timeline de eventos
- `get_peak_hours()` — horários de maior movimento
- `get_psychologist_workload()` — carga por profissional
- `predict_no_show(appointment_id)` — probabilidade de falta
- Queries com CTE MySQL + fallback SQLite

### QA Funcional UI Heavy
- Testes atualizados para nova arquitetura de injeção via controller
- Padrão antigo (`patch("ser_pleno.ui.views.<module>.ServicoX")`) substituído por mocks injetados no controller
- Resultado: **79 passed, 1 skipped**

---

*Documento de execução gerado em 2026-08-18 pelo Consultor Sênior Orientado a Resultados.*
