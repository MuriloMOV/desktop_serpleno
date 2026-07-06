# Reorganização da Estrutura do Projeto — SerPleno Desktop

Data: 2026-07-06
Objetivo: organizar a estrutura de pastas e arquivos de maneira profissional, modular e escalável para facilitar manutenção futura.

---

## 1. Análise da Estrutura Atual

### Problemas identificados

| Problema | Severidade | Exemplo |
|---|---|---|
| Scripts de manutenção dentro do pacote principal | 🔴 Alta | `execute_agendamento_sql.py`, `setup_groups.py`, `test_notifications.py` |
| Testes espalhados (package + fora) | 🔴 Alta | `tests/` externo, mas também `test_dashboard.py` dentro de `ser_pleno/` |
| `__main__.py` ausente | 🟡 Média | Sem ponto de entrada `python -m ser_pleno` |
| `ui_theme.py` na raiz do pacote | 🟡 Média | Mistura UI e configurações globais |
| Falta `src/` layout | 🟡 Média | Mistura código fonte com arquivos de nível superior |
| `__init__.py` ausente em várias pastas | 🟡 Média | `repositories/`, `models/`, `components/` |
| Sem `pyproject.toml` / dependências centralizadas | 🟡 Média | Dependências só no `.venv` |
| `tkclaude/` desorganizado na raiz | 🟢 Baixa | Sem relação clara com o app principal |
| Sem `README.md` | 🟢 Baixa | Falta documento de onboarding |

### Pontos positivos
- Arquitetura em camadas funcional: `models → repositories → services → controllers → views`
- Uso consistente de `BaseController` e `BaseViewFrame`
- Separação de temas em `ui_theme.py` e `ui_theme_extensions.py`
- MySQL isolado em `config/db_config.py`
- Cliente HTTP abstraído em `services/api.py`

---

## 2. Estrutura Alvo

```
desktop_serpleno/
├── .env                        # execução local (NÃO VERSIONAR)
├── .env.example                # variáveis esperadas
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml              # metadata + dependências
├── REORGANIZACAO_PLANO.md      # este documento
├── BUILD_DESKTOP.md
│
├── src/                        # ← código fonte isolado (src layout)
│   └── ser_pleno/              # ← pacote principal
│       ├── __init__.py
│       ├── __main__.py         # entry:  python -m ser_pleno
│       ├── app.py
│       │
│       ├── domain/             # ← Entidades puras (sem dependências de UI/DB)
│       │   ├── __init__.py
│       │   ├── estudantes.py
│       │   ├── dashboard.py
│       │   ├── bem_estar.py
│       │   └── configuracoes.py
│       │
│       ├── infrastructure/     # ← Detalhes técnicos (DB, HTTP, SO)
│       │   ├── __init__.py
│       │   ├── database.py     # ← renomeado de config/db_config.py
│       │   └── api/
│       │       ├── __init__.py
│       │       ├── client.py   # ← services/api.py movido
│       │       ├── connectivity.py
│       │       ├── mural.py
│       │       └── sync_service.py
│       │
│       ├── config/             # ← Configurações gerais da aplicação
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── operation_mode.py
│       │   └── operation_config.json
│       │
│       ├── application/        # ← Casos de uso e orquestração
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── autenticacao.py
│       │   │   ├── dashboard.py
│       │   │   ├── estudantes.py
│       │   │   ├── agendamentos.py
│       │   │   ├── bem_estar.py
│       │   │   ├── configuracoes.py
│       │   │   ├── triagem.py
│       │   │   ├── comunicacao.py
│       │   │   ├── relatorios.py
│       │   │   └── orientacoes.py
│       │   └── controllers/
│       │       ├── __init__.py
│       │       ├── base.py
│       │       ├── dashboard.py
│       │       ├── estudantes.py
│       │       ├── bem_estar.py
│       │       ├── configuracoes.py
│       │       ├── analise_triagem.py
│       │       └── triagem_controller.py
│       │
│       ├── presentation/       # ← Interface com o usuário
│       │   ├── __init__.py
│       │   ├── views/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── login.py
│       │   │   ├── dashboard.py
│       │   │   ├── estudantes.py
│       │   │   ├── agenda.py
│       │   │   ├── bem_estar.py
│       │   │   ├── analise_triagem.py
│       │   │   ├── relatorio.py
│       │   │   ├── comunicacao_interna.py
│       │   │   ├── orientacoes.py
│       │   │   ├── quadro_avisos.py
│       │   │   └── configuracoes.py
│       │   └── components/
│       │       ├── __init__.py
│       │       └── ui_components.py
│       │
│       ├── ui/                 # ← Design System
│       │   ├── __init__.py
│       │   ├── theme.py
│       │   └── theme_extensions.py
│       │
│       ├── repositories/       # ← Repositórios (acesso a dados)
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── estudantes.py
│       │   ├── dashboard.py
│       │   ├── agendamentos.py
│       │   ├── triagem.py
│       │   ├── bem_estar.py
│       │   ├── comunicacao.py
│       │   └── configuracoes.py
│       │
│       ├── utils/              # ← Utilidades transversais
│       │   ├── __init__.py
│       │   ├── dates.py
│       │   ├── mappers.py
│       │   ├── chart.py
│       │   ├── mood.py
│       │   ├── avatar_utils.py
│       │   ├── logging_config.py
│       │   ├── async_runner.py
│       │   └── service_helpers.py
│       │
│       └── scripts/            # ← Scripts de manutenção (NÃO importáveis)
│           ├── __init__.py
│           ├── setup_groups.py
│           ├── execute_agendamento_sql.py
│           ├── test_notifications.py
│           └── test_dashboard.py
│
├── tests/                      # ← Fora do src (padrão moderno)
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_controllers.py
│   │   └── test_models.py
│   ├── integration/
│   │   └── test_repositories.py
│   └── ui/
│       ├── test_app.py
│       ├── test_views.py
│       └── test_components.py
│
├── build/
├── dist/
├── docs/
└── user_data/                  # dados de usuário (runtime)
```

---

## 3. Por que essa estrutura?

| Camada | Responsabilidade | Por que separar? |
|---|---|---|
| `domain/` | Entidades puras e regras de negócio | Não depende de UI/DB/HTTP. Fácil testar. |
| `infrastructure/` | HTTP, MySQL, SO | Trocável (troca API/DB sem tocar regras de negócio) |
| `application/` | Casos de uso (services + controllers) | Orquestra `domain` com `infrastructure` |
| `presentation/` | Views + Components | CustomTkinter é um detalhe específico desta camada |
| `config/` | Configurações gerais | Inclui modos de operação e URLs |
| `ui/` | Design System (theme) | Reutilizável por toda a UI sem vazar para regras |
| `utils/` | Funções puras reutilizáveis | Sem dependências de camadas superiores |
| `repositories/` | Acesso a dados | Isola SQL/ORM da lógica de negócio |
| `scripts/` | Scripts pontuais | Não faz parte do app; não importável |
| `tests/` | Testes | Unidade + Integração + UI; fora do `src/` |

Padrões referência:
- Clean Architecture / DDD simplificado
- `src layout` usado por projetos como FastAPI, Pallets, Django REST Framework
- `cookiecutter-pypackage`

---

## 4. Mapa de Movimentação de Arquivos

| Origem | Destino |
|---|---|
| `ser_pleno/config/config.py` | `src/ser_pleno/config/config.py` |
| `ser_pleno/config/db_config.py` | `src/ser_pleno/infrastructure/database.py` |
| `ser_pleno/config/operation_mode.py` | `src/ser_pleno/config/operation_mode.py` |
| `ser_pleno/ui_theme.py` | `src/ser_pleno/ui/theme.py` |
| `ser_pleno/ui_theme_extensions.py` | `src/ser_pleno/ui/theme_extensions.py` |
| `ser_pleno/models/*.py` | `src/ser_pleno/domain/*.py` |
| `ser_pleno/repositories/*.py` | `src/ser_pleno/repositories/*.py` |
| `ser_pleno/services/api.py` | `src/ser_pleno/infrastructure/api/client.py` |
| `ser_pleno/services/connectivity.py` | `src/ser_pleno/infrastructure/api/connectivity.py` |
| `ser_pleno/services/mural.py` | `src/ser_pleno/infrastructure/api/mural.py` |
| `ser_pleno/services/sync_service.py` | `src/ser_pleno/infrastructure/api/sync_service.py` |
| `ser_pleno/services/autenticacao.py` | `src/ser_pleno/application/services/autenticacao.py` |
| `ser_pleno/services/dashboard.py` | `src/ser_pleno/application/services/dashboard.py` |
| `ser_pleno/services/estudantes.py` | `src/ser_pleno/application/services/estudantes.py` |
| `ser_pleno/services/agendamentos.py` | `src/ser_pleno/application/services/agendamentos.py` |
| `ser_pleno/services/bem_estar.py` | `src/ser_pleno/application/services/bem_estar.py` |
| `ser_pleno/services/configuracoes.py` | `src/ser_pleno/application/services/configuracoes.py` |
| `ser_pleno/services/triagem.py` | `src/ser_pleno/application/services/triagem.py` |
| `ser_pleno/services/comunicacao.py` | `src/ser_pleno/application/services/comunicacao.py` |
| `ser_pleno/services/relatorios.py` | `src/ser_pleno/application/services/relatorios.py` |
| `ser_pleno/services/orientacoes.py` | `src/ser_pleno/application/services/orientacoes.py` |
| `ser_pleno/controllers/*.py` | `src/ser_pleno/application/controllers/*.py` |
| `ser_pleno/views/*.py` | `src/ser_pleno/presentation/views/*.py` |
| `ser_pleno/components/ui_components.py` | `src/ser_pleno/presentation/components/ui_components.py` |
| `ser_pleno/utils/*.py` | `src/ser_pleno/utils/*.py` |
| `ser_pleno/app.py` | `src/ser_pleno/app.py` |
| `ser_pleno/user_profile.json` | `src/ser_pleno/user_profile.json` |
| `ser_pleno/setup_groups.py` | `src/ser_pleno/scripts/setup_groups.py` |
| `ser_pleno/execute_agendamento_sql.py` | `src/ser_pleno/scripts/execute_agendamento_sql.py` |
| `ser_pleno/test_notifications.py` | `src/ser_pleno/scripts/test_notifications.py` |
| `ser_pleno/test_dashboard.py` | `src/ser_pleno/scripts/test_dashboard.py` |
| `tests/*.py` | `tests/unit/*.py` e `tests/ui/*.py` |

---

## 5. Mapa de Atualização de Imports

| Antes | Depois |
|---|---|
| `from config.config import X` | `from ser_pleno.config.config import X` |
| `from ui_theme import THEME` | `from ser_pleno.ui.theme import THEME` |
| `from services.connectivity import X` | `from ser_pleno.infrastructure.api.connectivity import X` |
| `from views.base import BaseViewFrame` | `from ser_pleno.presentation.views.base import BaseViewFrame` |
| `from components.ui_components import X` | `from ser_pleno.presentation.components.ui_components import X` |
| `from controllers.dashboard import X` | `from ser_pleno.application.controllers.dashboard import X` |
| `from repositories.base import X` | `from ser_pleno.repositories.base import X` |
| `from models.estudantes import X` | `from ser_pleno.domain.estudantes import X` |
| `from utils.async_runner import X` | `from ser_pleno.utils.async_runner import X` |

---

## 6. Comandos de Execução

### Pré-requisito
- Backup ou commit do estado atual
- PowerShell 5.1+
- Python 3.13+

### Passos
1. Criar estrutura de diretórios
2. Mover arquivos existentes
3. Criar arquivos `__init__.py` e `__main__.py`
4. Criar `pyproject.toml`
5. Atualizar imports em `app.py` e `views/base.py`
6. Executar `pip install -e .`
7. Validar com `python -m ser_pleno --help`
8. Executar testes com `pytest tests/`
