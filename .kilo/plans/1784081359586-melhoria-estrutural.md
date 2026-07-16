# Plano de Melhoria Estrutural — SerPleno Desktop

**Data:** 2026-07-14  
**Status:** Pronto para implementação  
**Arquivo:** `1784081359586-melhoria-estrutural.md`

---

## 1. Diagnóstico Técnico Atual

### 1.1 Estado Real do Código (validado por inspeção)

O projeto já possui uma arquitetura em camadas **substancialmente implementada**. O documento `docs/arquitetura-planejamento.md` está desatualizado: a maioria dos itens de médio prazo já foi concluída.

| Item do planejamento original | Status real |
|-------------------------------|-------------|
| Controllers stubados | ✅ Todos implementados |
| SQL extraído para repositories | ✅ Concluído |
| Models atualizados | ✅ Concluído |
| `repositories/` criada | ✅ `base.py` + 10 repositórios |
| Services usam repositories | ✅ Todos os services usam repositories |
| Config organizada | ✅ Concluído |

**Camada atual:**
```
Presentation → Controllers → Services → Repositories → MySQL/SQLite
```

### 1.2 Problemas Reais (ordenados por impacto)

| # | Problema | Severidade | Evidência |
|---|----------|------------|-----------|
| 1 | Estado global de auth (`_auth_service`) — acoplamento oculto entre módulos | Alta | `api.py:15`, `services/agendamentos.py:9`, `login.py:746-747` |
| 2 | `app.py` God Object (516 linhas) — mistura navegação, tema, login, lifecycle | Alta | `app.py` |
| 3 | Helpers UI duplicados em 6+ views (`_card`, `_avatar`, `AV_COLORS`) | Média | `views/estudantes.py`, `views/dashboard.py`, `views/orientacoes.py`, `views/bem_estar.py`, `views/analise_triagem.py`, `views/relatorio.py`, `views/quadro_avisos.py` |
| 4 | Testes unitários ausentes para services/repositories | Alta | `tests/` — apenas smoke/integration tests |
| 5 | `print()` em código de produção | Baixa | `services/dashboard.py:30` |
| 6 | Documentação técnica ausente | Média | Nenhum guia para desenvolvedores |

### 1.3 O que NÃO é problema (e não precisa de "solução")

- **Instanciação manual de services/controllers** — para um desktop app com ~10 telas, um DI container seria over-engineering. O `BaseController` já fornece o desacoplamento necessário.
- **Views acessando `self.controller.usuario_logado`** — isso é correto. O controller é a interface da view para o estado da aplicação.
- **Event Bus** — não há fluxos de eventos complexos que justifiquem essa camada adicional.

---

## 2. Objetivos

1. **Eliminar acoplamento oculto** — remover estado global de auth
2. **Reduzir `app.py`** — extrair responsabilidades em classes dedicadas
3. **Eliminar duplicação UI** — centralizar helpers em `ui_components.py`
4. **Aumentar testabilidade** — unit tests para services e repositories
5. **Documentar** — guia do desenvolvedor + ADRs

---

## 3. Plano de Implementação

### Fase 1: Eliminar acoplamento oculto de auth (1 dia)

#### T1.1: Remover `_auth_service` global de `api.py`
**Arquivos:** `src/ser_pleno/infrastructure/api/api.py`, `src/ser_pleno/infrastructure/api/mural.py`

- Remover `_auth_service`, `set_auth_service()`, `get_auth_service()`
- `ClienteAPI._get_session()` recebe `auth_service` via `__init__`
- `mural.py` segue o mesmo padrão

#### T1.2: Remover `_auth_service` global de `services/agendamentos.py`
**Arquivo:** `src/ser_pleno/application/services/agendamentos.py`

- Remover `_auth_service`, `set_auth_service()`, `get_auth_service()`
- `ServicoAgendamento.__init__` recebe `auth_service` opcional
- Remover import e chamada de `set_auth_service` em `views/login.py:746`

#### T1.3: Propagar auth via controller
**Arquivo:** `src/ser_pleno/application/controllers/autenticacao.py`

- Adicionar propriedade `auth_service` no `AutenticacaoController`
- `App.iniciar_sistema()` injeta `auth_service` nos services que precisam

**Validação:** Login funciona; API calls usam sessão autenticada

---

### Fase 2: Decompor `app.py` (1 dia)

#### T2.1: Extrair `NavigationManager`
**Novo arquivo:** `src/ser_pleno/presentation/navigation.py`

Mover de `app.py`:
- `MENU_ITEMS`, `_MENU_BY_KEY`
- `criar_sidebar()`, `_criar_marca()`, `_criar_menu()`, `_criar_rodape_sidebar()`
- `criar_area_conteudo()`, `_mostrar_por_key()`
- `limpar_tela()`

`NavigationManager` recebe `app` no `__init__` e expõe `show(key)`.

#### T2.2: Extrair `ThemeManager`
**Novo arquivo:** `src/ser_pleno/presentation/theme_manager.py`

Mover de `app.py`:
- `alternar_tema()`
- `_on_theme_changed()`
- Lógica de reconstrução de UI

`ThemeManager` recebe `app` no `__init__` e expõe `toggle()`.

#### T2.3: Reduzir `app.py`
Resultado esperado (~80 linhas):

```python
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self.navigation = NavigationManager(self)
        self.theme_manager = ThemeManager(self)
        self._setup_sync()
        self.mostrar_login()
```

**Validação:** Navegação e tema funcionam; login/logout intactos

---

### Fase 3: Deduplicar helpers UI (1 dia)

#### T3.1: Mover helpers comuns para `ui_components.py`
**Arquivos afetados:** 6 views + `ui_components.py`

Helpers a consolidar:
- `_card(parent, **kw)` → `Card` já existe, mas algumas views usam função `_card` customizada. Padronizar para usar `Card` do `ui_components.py`.
- `_avatar(parent, initials, color, size)` → mover para `ui_components.py` como `Avatar.create()`
- `AV_COLORS` → mover para `utils/avatar_utils.py` (já existe `get_avatar_color()`)

#### T3.2: Limpar tokens por view
- Remover `DASH_TOKENS`, `EST_TOKENS` — usar apenas `THEME` + `SPACING`/`RADIUS` diretamente
- `extend_theme()` apenas para tokens verdadeiramente específicos da tela

**Validação:** Visual — telas mantêm aparência idêntica

---

### Fase 4: Testes unitários (2 dias)

#### T4.1: Testes de services
**Padrão:** `tests/test_services.py` (novo)

Cada service recebe mock do repository:

```python
def test_servico_estudante_listar(mock_repo):
    service = ServicoEstudante()
    service.repo = mock_repo
    result = service.listar_estudantes()
    assert result["success"] is True
```

**Cobertura alvo:** Services principais (estudantes, dashboard, agendamentos, autenticacao)

#### T4.2: Testes de repositories
**Padrão:** `tests/test_repositories.py` (novo)

```python
def test_estudante_repository_listar(mysql_conn):
    repo = EstudanteRepository()
    result = repo.listar()
    assert isinstance(result, list)

def test_estudante_repository_fallback(local_cache):
    repo = EstudanteRepository()
    result = repo._local_listar()
    assert isinstance(result, list)
```

**Validação:** `pytest -v --tb=short` + coverage report

---

### Fase 5: Documentação (1 dia)

#### T5.1: Guia do desenvolvedor
**Novo arquivo:** `docs/desenvolvimento.md`

Conteúdo:
- Arquitetura em camadas (diagrama ASCII)
- Como adicionar uma nova tela (view → controller → service → repository)
- Convenções de código (naming, type hints, logging)
- Padrões existentes (fallback decorators, async loading)

#### T5.2: Atualizar `docs/arquitetura-planejamento.md`
- Marcar todos os itens concluídos como `[x]`
- Remover itens obsoletos (DI container, Event Bus)
- Adicionar seção "Estado atual" refletindo a realidade

#### T5.3: ADRs
**Diretório:** `docs/adr/`

Mínimo: 2 ADRs
- ADR-001: Repository Pattern + fallback MySQL→SQLite
- ADR-002: Injeção de auth via controller (Fase 1)

---

## 4. Estrutura Final (diferenças em relação à atual)

```
src/ser_pleno/
├── app.py                          # ~80 linhas (reduzido de 516)
├── presentation/
│   ├── navigation.py               # NOVO — gerenciador de navegação
│   ├── theme_manager.py            # NOVO — gerenciador de tema
│   ├── components/
│   │   ├── ui_components.py        # + helpers consolidados (_card, _avatar)
│   │   └── icons.py
│   └── views/
│       ├── base.py
│       ├── login.py                # - set_auth_service calls
│       └── ... (outras views — _card/_avatar removidos)
├── infrastructure/
│   └── api/
│       ├── api.py                  # - _auth_service global
│       └── mural.py                # - _auth_service global
├── application/
│   ├── controllers/
│   │   └── autenticacao.py         # + auth_service property
│   └── services/
│       └── agendamentos.py         # - _auth_service global
├── utils/
│   └── avatar_utils.py             # + get_avatar_color() (consolidado)
└── ...
```

**Nenhuma pasta nova** além de `docs/adr/` e os dois arquivos de apresentação (`navigation.py`, `theme_manager.py`).

---

## 5. Padronização (já existente, apenas reforçar)

| Elemento | Padrão |
|----------|--------|
| Classes | PascalCase |
| Métodos | snake_case |
| Privados | Prefixo `_` |
| Logging | `logger.{debug,info,warning,error}` — nunca `print()` |
| Type hints | Obrigatórios em métodos públicos |
| Docstrings | Google-style em classes públicas |

---

## 6. Riscos e Mitigações

| Risco | Mitigação |
|--------|-----------|
| Quebra de auth propagation | Testar login + API calls em modo conectado |
| Regressão visual na UI | Comparar screenshots antes/depois das mudanças em `ui_components.py` |
| `app.py` refatorado quebra navegação | Validar todas as 10 telas após extração |
| Testes mocking inadequado | Usar `unittest.mock` com `spec=RepositoryClass` |

---

## 7. Checklist de Validação

- [ ] `pytest -v --tb=short` passa
- [ ] `ruff check src/` sem erros
- [ ] Login + navegação + tema funcionam
- [ ] Nenhum `print()` em `src/ser_pleno/`
- [ ] Nenhuma referência a `_auth_service`, `set_auth_service`, `get_auth_service`
- [ ] `_card` e `_avatar` definidos apenas em `ui_components.py`
- [ ] Cobertura de tests > 60% para services

---

## 8. Decisões Excluídas (fora de escopo)

| Item | Razão |
|-------|-------|
| DI Container | Over-engineering para escala atual (~10 telas) |
| Event Bus | Nenhum fluxo de eventos complexo identificado |
| Enriquecimento de domain models | CRUD desktop app não se beneficia de entidades ricas |
| SQLAlchemy migration | SQL raw funciona; migração traria risco sem ganho claro |
| `core/` package separado | A estrutura atual já tem separação adequada |

---

## 9. Próximos Passos

1. Executar **Fase 1** (auth coupling) — maior risco, maior valor
2. Executar **Fase 2** (app.py decomposition)
3. Executar **Fase 3** (UI dedup)
4. Executar **Fase 4** (tests)
5. Executar **Fase 5** (docs)
