# Planejamento de Reestruturação Arquitetural — SerPleno Desktop

**Data:** 2026-06-17  
**Contexto:** Projeto `ser_pleno` — Desktop Application (CustomTkinter) com backend Django/MySQL  
**Status:** Em execução → Concluído (2026-07-15)

> **Nota:** Este documento foi sincronizado com o estado real do código em 2026-07-15.
> Itens de curto/médio prazo foram concluídos. Detalhes em `docs/desenvolvimento.md` e `docs/adr/`.

---

## 1. Diagnóstico (original)

O projeto segue um padrão **híbrido MVC/MVVM informal**, com separação de pastas parcialmente implementada:
- Views: Implementadas (CustomTkinter Frames)
- Controllers: **Stubados/vazios** — apenas `triagem_controller.py` tem implementação
- Services: Implementados com lógica de negócio e acesso a dados
- Models: Dataclasses simples, não utilizados como entidades de domínio

### Problemas principais:
1. Controllers vazios — Views falam diretamente com Services
2. SQL espalhado em Services — sem camada Repository
3. Duplicação removida: apenas `services/estudantes.py` segue como serviço de estudantes consolidado (`services/students.py` foi removido)
4. Models desatualizados em relação ao schema real do banco
5. `operation_config.json` na raiz do projeto (deveria estar em `config/`)

---

## 2. Objetivos

- **Curto prazo:** Implementar controllers stubados; consolidar duplicações; reorganizar configurações
- **Médio prazo:** Introduzir camada Repository; refinar Models como entidades; extrair componentes reutilizáveis
- **Longo prazo:** Adotar tipagem stricter (mypy); considerar SQLAlchemy para type-safety (reavaliar futuramente)

---

## 3. Backlog Hierárquico

### 3.1 Curto Prazo (ganhos rápidos)

#### T1: Implementar controllers stubados
- [x] `controllers/dashboard.py`
- [x] `controllers/estudantes.py`
- [x] `controllers/bem_estar.py`
- [x] `controllers/configuracoes.py`
- [x] `controllers/analise_triagem.py`

#### T2: Consolidar services duplicados
- [x] Remover `services/students.py` (StudentService wrapper legado)

#### T3: Reorganizar configurações
- [x] Mover `operation_config.json` para `config/operation_config.json`
- [x] Atualizar imports em `config/operation_mode.py`

### 3.2 Médio Prazo

#### T4: Atualizar models para refletir schema real
- [x] `models/estudantes.py` — manter `Estudante` (já está ok)
- [x] `models/dashboard.py` — atualizar campos para refletir tabela `agendamento`
- [x] `models/bem_estar.py` — validar campos contra `desktop_wellnesscheckin`
- [x] `models/configuracoes.py` — revisar

#### T5: Introduzir pasta `repositories/`
- [x] `repositories/base.py` — conexão compartilhada + fallbacks
- [x] `repositories/estudantes.py` — EstudanteRepository
- [x] `repositories/dashboard.py` — DashboardRepository
- [x] `repositories/agendamentos.py` — AgendamentoRepository
- [x] `repositories/bem_estar.py` — BemEstarRepository
- [x] `repositories/comunicacao.py` — ComunicacaoRepository
- [x] `repositories/orientacoes.py` — OrientacoesRepository
- [x] `repositories/relatorios.py` — RelatoriosRepository
- [x] `repositories/triagem.py` — TriagemRepository
- [x] `repositories/configuracoes.py` — ConfiguracoesRepository
- [x] `repositories/autenticacao.py` — AutenticacaoRepository

#### T6: Refatorar `services/` para usar repositories
- [x] `services/estudantes.py` → depende de `EstudanteRepository`
- [x] `services/dashboard.py` → depende de `DashboardRepository`
- [x] `services/agendamentos.py` → depende de `AgendamentoRepository`
- [x] `services/bem_estar.py` → depende de `BemEstarRepository`
- [x] `services/comunicacao.py` → depende de `ComunicacaoRepository`
- [x] `services/orientacoes.py` → depende de `OrientacoesRepository`
- [x] `services/relatorios.py` → depende de `RelatoriosRepository`
- [x] `services/triagem.py` → depende de `TriagemRepository`
- [x] `services/configuracoes.py` → depende de `ConfiguracoesRepository`
- [x] `services/autenticacao.py` → depende de `AutenticacaoRepository`

#### T7: Extrair lógica de UI das Views para componentes
- [x] `ui_components.py` consolidado com `Card`, `KPICard`, `Avatar`, `PageHeader`, `Divider`, `PrimaryButton`, `SecondaryButton`, `GhostButton`, `Badge`, `EmptyState`, `SkeletonLoader`, `Tooltip`, `BaseModal`
- [x] `icons.py` consolidado com ícones por categoria

#### T8: Atualizar App para usar controllers
- [x] `app.py` injeta controllers nas views via `navigation.show()`
- [x] `navigation.py` gerencia sidebar, menu, área de conteúdo
- [x] `theme_manager.py` gerencia toggle e reconstrução de UI
- [x] `app.py` reduzido para ~130 linhas

---

## 4. Estado atual (2026-07-15)

Camada completa implementada:  
**Presentation → Controllers → Services → Repositories → MySQL/SQLite**

- Fase 1 (auth coupling) concluída — remoção de `set_auth_service`/`get_auth_service`
- Fase 2 (app.py decomposition) concluída — `navigation.py` + `theme_manager.py` extraídos
- `app.py` reduzido para ~130 linhas
- `navigation.py` gerencia sidebar, menu, área de conteúdo
- `theme_manager.py` gerencia toggle e reconstrução de UI
- Fallback decorators: `with_local_fallback`, `write_with_fallback`, `with_api_fallback`
- Async loading: `AsyncRunner` + `BaseViewFrame._load_async`
- **10 controllers** implementados
- **11 repositories** implementados
- **10 services** implementados
- `ui_components.py` com componentes reutilizáveis (Card, KPICard, Avatar, etc.)
- `docs/adr/` criado (2 ADRs)
- **Design System modular:** `ui/theme/` dividido em `palette.py`, `typography.py`, `spacing.py`, `colors.py` e `__init__.py`, mantendo 100% compatibilidade de imports
- **Nomenclatura padronizada:** views renomeadas para termos principais (`triagem.py`, `comunicacao.py`, `avisos.py`); métodos de `NavigationManager` renomeados para inglês
- **Controllers desacoplados:** `DashboardController` e `ConfiguracoesController` não dependem mais de `app`; `QuadroAvisosController` também desacoplado

---

## 5. Critérios de Sucesso (alcançados)

| Item | Métrica | Status |
|---|---|---|
| Controllers implementados | 100% dos controllers possuem implementação funcional | ✅ |
| Services consolidados | 0 imports de `services.students` legados | ✅ |
| Configuração organizada | `operation_config.json` reside em `config/` | ✅ |
| Repository layer | Toda query SQL em services moveu-se para repositories | ✅ |
| Models atualizados | Todos os models refletem colunas reais das tabelas | ✅ |
| Views desacopladas | Nenhuma view instancia diretamente `ServicoX` | ✅ |

---

## 6. Riscos (mitigados)

| Risco | Mitigação | Status |
|---|---|---|
| Quebra de funcionalidade existente | Testes manuais após cada etapa; manter fallback API→DB | ✅ |
| Complexidade crescente | Documentar interfaces entre camadas | ✅ |
| Custo de migração gradual | Implementar changesets pequenos e versionados | ✅ |

---

## 7. Futuro (não planejamento ativo)

- **mypy:** Adotar tipagem stricter gradualmente (ver `docs/desenvolvimento.md`)
- **SQLAlchemy 2.0:** Reavaliar se o projeto crescer além do escopo atual (decisão atual: SQL raw funciona)
- **Controllers com navegação:** Avaliar introduzir `NavigationService` para substituir chamadas diretas a `app.mostrar_login()` (atualmente resolvido via `winfo_toplevel()` nas views)
- **Testes de navegação:** Adicionar testes unitários para `NavigationManager` cobrindo `show()`, `update_menu()`, `update_header()` e transições de tema

---

*Documento de planejamento gerado pela análise arquitetural. Sincronizado em 2026-07-15.*

