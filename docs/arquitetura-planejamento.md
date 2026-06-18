# Planejamento de Reestruturação Arquitetural — SerPleno Desktop

**Data:** 2026-06-17  
**Contexto:** Projeto `ser_pleno` — Desktop Application (CustomTkinter) com backend Django/MySQL  
**Status:** Em execução

---

## 1. Diagnóstico

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
- **Longo prazo:** Adotar DI simples; Event Bus; considerar SQLAlchemy para type-safety

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
- [ ] `repositories/base.py` — conexão compartilhada
- [ ] `repositories/estudantes.py` — EstudanteRepository
- [ ] `repositories/dashboard.py` — DashboardRepository
- [ ] `repositories/agendamentos.py` — AgendamentoRepository

#### T6: Refatorar `services/` para usar repositories
- [ ] `services/estudantes.py` → depende de `EstudanteRepository`
- [ ] `services/dashboard.py` → depende de `DashboardRepository`
- [ ] `services/agendamentos.py` → depende de `AgendamentoRepository`

#### T7: Extrair lógica de UI das Views para componentes
- [ ] Mover modal de `views/estudantes.py` para `components/modals/EstudanteFormModal.py`

#### T8: Atualizar App para usar controllers
- [ ] `app.py` injeta controllers nas views

### 3.3 Longo Prazo

#### T9: Adotar tipagem stricter (mypy)
- [ ] Adicionar `mypy.ini`
- [ ] Implementar gradualmente tipos em serviços críticos

#### T10: Considerar SQLAlchemy 2.0
- [ ] Avaliar viabilidade de migração

---

## 4. Critérios de Sucesso

| Item | Métrica |
|---|---|
| Controllers implementados | 100% dos controllers stubados possuem implementação funcional |
| Services consolidados | 0 imports de `services.students` legados |
| Configuração organizada | `operation_config.json` reside em `config/` |
| Repository layer | Toda query SQL em services moveu-se para repositories |
| Models atualizados | Todos os models refletem colunas reais das tabelas |
| Views desacopladas | Nenhuma view instancia diretamente `ServicoX` |

---

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Quebra de funcionalidade existente | Testes manuais após cada etapa; manter fallback API→DB |
| Complexidade crescente | Documentar interfaces entre camadas |
| Custo de migração gradual | Implementar changesets pequenos e versionados |

---

*Documento de planejamento gerado pela análise arquitetural.*
