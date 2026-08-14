# Análise Completa do Projeto — SerPleno Desktop

## 1. Descrição do Projeto

**SerPleno Desktop** é uma aplicação desktop de gestão escolar e bem-estar, desenvolvida em Python com CustomTkinter, voltada para o contexto de psicologia escolar. O sistema suporta operação **online** (MySQL) e **offline** (SQLite local) com sincronização bidirecional automática.

- **Objetivo:** Fornecer uma interface desktop robusta para acompanhamento acadêmico e emocional de estudantes, agendamento de atendimentos, triagens, orientações, comunicação interna e relatórios.
- **Domínio:** Gestão escolar e bem-estar estudantil (psicologia escolar).
- **Stack tecnológico principal:**
  - Linguagem: Python >= 3.11
  - UI: CustomTkinter 5.2+
  - Banco de dados: MySQL (fonte primária) + SQLite (cache/fallback offline)
  - Build: PyInstaller (executável Windows)
  - Testes: pytest
  - Qualidade: ruff, mypy

---

## 2. Funcionalidades

| Funcionalidade | Descrição | Objetivo |
|----------------|-----------|----------|
| **Autenticação** | Login local com hash Django/pbkdf2/bcrypt/argon2, fallback para API, estabelecimento de sessão Django em background. | Garantir acesso seguro ao sistema e manutenção de sessão para consumo de serviços. |
| **Dashboard** | Painel com KPIs (atendimentos hoje, vagas disponíveis, alertas, total de estudantes, humor médio), gráfico de humor dos últimos 30 dias, próximos atendimentos, estudantes em alerta, dimensões de bem-estar, notificações de ajuda e alertas. | Fornecer visão consolidada e rápida do estado operacional da instituição. |
| **Gestão de Estudantes** | CRUD de estudantes, busca, filtros (laudo médico, requer atenção), seleção com detalhes (perfil, intervenções, agenda), avatar, status bar. | Permitir cadastro, acompanhamento e edição de dados dos estudantes. |
| **Agenda de Atendimentos** | Grid de horários por dia e próxima semana, criação/edição/remoção de agendamentos, gestão de grade de horários (disponibilidade), sincronização com SerPleno Web. | Organizar e controlar a rotina de atendimentos e disponibilidades. |
| **Bem-Estar e Humor** | Registro de humor, check-ins de bem-estar, histórico, dimensões acadêmica/emocional/social, estudantes em risco. | Acompanhar o estado emocional e de bem-estar dos estudantes ao longo do tempo. |
| **Triagem** | Listagem, criação, edição e exclusão de triagens; formulários de triagem; filtros por busca, status, prioridade e estudante. | Registrar e gerenciar processos de triagem psicológica/estudantil. |
| **Orientações** | Histórico de orientações por estudante, criação/edição/duplicação/exclusão, presets de modelos rápidos (Apoio Pedagógico, Emocional, Profissional), estatísticas por tema e mês. | Documentar e organizar ações de orientação realizadas com estudantes. |
| **Quadro de Avisos (Mural)** | Publicações institucionais (criar, editar, deletar), categorias (informativo, aviso, aula, urgente, evento), pré-visualização. | Comunicar informações institucionais de forma centralizada. |
| **Comunicação Interna** | Chat privado e grupo, envio de mensagens e arquivos, contatos por papel (admin, analista, coordenador, suporte), badges de não lidas, atualização periódica. | Viabilizar comunicação rápida entre membros da equipe. |
| **Relatórios** | Listagem, geração, download, exclusão e exportação de relatórios (estudantes, agendamentos, triagens). | Permitir análise e exportação de dados operacionais. |
| **Configurações** | Preferências de usuário (avatar, tema claro/escuro, tamanho de fonte), notificações (mensagens diretas, pedidos de ajuda, feedback, efeitos sonoros), alteração de senha, encerramento de sessão. | Personalizar experiência e gerenciar conta e preferências do usuário. |

---

## 3. Estrutura do Projeto

### 3.1 Raiz

```
F:\Projetos\mobile-web-desk\desktop_serpleno\
├── .env.example
├── .env
├── .gitignore
├── .coverage
├── README.md
├── pyproject.toml
├── BUILD_DESKTOP.md
├── SerPleno.spec
├── requirements-build.txt
├── fluxos-incompletos.md
├── .github/workflows/ci.yml
├── build/
├── dist/
├── config/
│   └── ser_pleno_local.db
├── docs/
│   ├── desenvolvimento.md
│   ├── arquitetura-planejamento.md
│   ├── build_executavel.md
│   ├── auditoria-design.md
│   ├── auditoria-performance-responsividade.md
│   ├── analise-modularizacao-nomenclatura.md
│   ├── relatorio-melhorias.md
│   ├── adr/
│   │   ├── ADR-001-repository-pattern-fallback.md
│   │   └── ADR-002-auth-injection-via-controller.md
│   └── sql/
│       ├── execute_agendamento_sql.py
│       └── setup_groups.py
├── scripts/
│   └── benchmarks/
│       └── perf_bench.py
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_config.py
│   ├── test_services.py
│   ├── test_repositories.py
│   ├── test_views.py
│   ├── test_perf.py
│   ├── test_smoke_perf.py
│   ├── test_login_perf.py
│   ├── test_local_integration.py
│   ├── test_local_fallback.py
│   └── test_qa_interacoes.py
└── src/
    └── ser_pleno/
        ├── app.py
        ├── __main__.py
        ├── __init__.py
        ├── config/
        ├── application/
        ├── infrastructure/
        ├── repositories/
        ├── domain/
        ├── presentation/
        ├── ui/
        ├── utils/
        ├── sql/
        ├── assets/
        ├── logs/
        └── docs/
```

### 3.2 `src/ser_pleno/` — Pacote principal

#### 3.2.1 `config/`

- `config.py`: Configurações de API (URLs, tokens).
- `db_config.py`: Pool de conexões MySQL.
- `operation_mode.py`: Modos de operação (`independent`, `hybrid`, `connected`, `db_primary`).
- `operation_config.json`: Configurações persistentes de modo de operação.
- `fallback_metrics.json`: Métricas de queda/recuperação de conexão.

#### 3.2.2 `application/controllers/`

- `base.py`: `BaseController` com infraestrutura comum.
- `autenticacao.py`: Controller de login/logout/alteração de senha.
- `dashboard.py`: Controller do painel principal e KPIs.
- `estudantes.py`: Controller de gestão de estudantes.
- `agenda.py`: Controller de agenda e agendamentos.
- `bem_estar.py`: Controller de bem-estar e humor.
- `triagem.py`: Controller de triagens.
- `relatorio.py`: Controller de relatórios.
- `comunicacao.py`: Controller de chat, mensagens, ajuda e contatos.
- `orientacoes.py`: Controller de orientações.
- `avisos.py`: Controller de quadro de avisos/mural.
- `configuracoes.py`: Controller de configurações do usuário.

#### 3.2.3 `application/services/`

- `autenticacao.py`: Lógica de login, hash, alteração de senha, sessão HTTP.
- `dashboard.py`: Orquestração de KPIs, alertas e notificações.
- `estudantes.py`: Regras de negócio para estudantes.
- `agendamentos.py`: Regras de negócio para agendamentos e disponibilidade.
- `bem_estar.py`: Regras de check-ins, humor, estudantes em risco.
- `triagem.py`: Regras de criação/edição/listagem de triagens.
- `relatorios.py`: Regras de geração/exportação de relatórios.
- `comunicacao.py`: Regras de mensagens, contatos e pedidos de ajuda.
- `orientacoes.py`: Regras de orientações, presets e estatísticas.
- `mural.py`: Regras de publicações do mural.
- `configuracoes.py`: Regras de preferências e perfil.
- `bootstrap.py`: Seed pós-login de entidades críticas (MySQL → SQLite).

#### 3.2.4 `infrastructure/`

- `api/api.py`: `ClienteAPI` centralizado (GET/POST/PUT/DELETE), sessão HTTP, retry, timeout.
- `api/connectivity.py`: Health check da API e atualização assíncrona de disponibilidade.
- `api/mural.py`: Serviço específico de integração com mural via API.
- `api/sync_service.py`: `SyncService` (background thread) e `SyncQueue` (fila em SQLite) para sincronização MySQL ↔ SQLite ↔ API e reconciliação de IDs locais.
- `local/local_cache.py`: `LocalCache` (SQLite WAL) com tabelas locais para estudantes, agendamentos, orientações, triagens, mural, wellness, alerts, messages, reports, user_preferences e sync_queue.
- `local/seed_service.py`: `sync_critical_entities()` para rebase de entidades críticas.
- `local/fallback_metrics.py`: Métricas de ocorrência de fallback.

#### 3.2.5 `repositories/`

- `base.py`: Helpers compartilhados (`fetch_all`, `fetch_one`, `execute_non_query`, `generate_local_id`, `local_cache`).
- `fallback.py`: Decorators `with_local_fallback` e `write_with_fallback`, com detecção de erros de conexão MySQL.
- `autenticacao.py`: Acesso a `auth_user`.
- `dashboard.py`: KPIs consolidados, alertas, humor e bem-estar.
- `estudantes.py`: Acesso a `aluno` + `auth_user`.
- `agendamentos.py`: Acesso a `agendamento` e `disponibilidade`.
- `bem_estar.py`: Acesso a `desktop_moodentry` e `desktop_wellnesscheckin`.
- `comunicacao.py`: Acesso a `desktop_alert`, `desktop_message`, `desktop_help_request`.
- `configuracoes.py`: Acesso a preferências e dados de usuário.
- `orientacoes.py`: Acesso a `desktop_orientation`.
- `relatorios.py`: Acesso a `desktop_report`.
- `triagem.py`: Acesso a `desktop_screening`.

#### 3.2.6 `domain/models/`

- `estudantes.py`: Modelos de domínio relacionados a estudantes.
- `dashboard.py`: Modelos de domínio relacionados a KPIs e indicadores.
- `configuracoes.py`: Modelos de domínio de configurações e preferências.
- `bem_estar.py`: Modelos de domínio de humor e bem-estar.

#### 3.2.7 `presentation/`

- `navigation.py`: `NavigationManager` (sidebar, menu, cache de views, pré-criação).
- `theme_manager.py`: `ThemeManager` (toggle claro/escuro, reconstrução de UI).
- `view_factory.py`: `ViewFactory` para instanciação de views por chave de navegação.
- `components/ui_components.py`: Componentes reutilizáveis (`Card`, `KPICard`, `PrimaryButton`, `SecondaryButton`, `GhostButton`, `Badge`, `EmptyState`, `Divider`, `SkeletonLoader`, `Tooltip`, `Avatar`, `BaseModal`, `PageHeader`, `SectionHeader`, `Pill`, `Tabs`, `ClickableFrame`).
- `components/icons.py`: Ícones e constantes de emoji.
- `views/base.py`: `BaseViewFrame`.
- `views/login.py`: Tela de login com gradiente animado, bolhas, validação e toggle de música.
- `views/dashboard.py`: Painel principal com KPIs, gráficos, alertas, notificações e atalhos.
- `views/estudantes.py`: Lista, busca, filtros, detalhes laterais e CRUD.
- `views/agenda.py`: Grid de horários, modal de agendamento e gestão de disponibilidade.
- `views/bem_estar.py`: Dashboard de bem-estar, check-ins e histórico de humor.
- `views/triagem.py`: Lista, criação, edição e filtros de triagens.
- `views/relatorio.py`: Lista de relatórios e ações de download/exclusão/exportação.
- `views/comunicacao.py`: Chat privado/grupo, sidebar de contatos, envio de mensagens e arquivos.
- `views/orientacoes.py`: Histórico de orientações, formulário e presets.
- `views/avisos.py`: Quadro de avisos com categorias e ações de publicação.
- `views/configuracoes.py`: Cartão pessoal, central de avisos, aparência e segurança.

#### 3.2.8 `ui/`

- `theme_extensions.py`: `extend_theme()` e `spacing()`.
- `theme/__init__.py`: Estado de tema ativo, listeners, `toggle_mode()`, `apply_global_style()`.
- `theme/palette.py`: `LIGHT_THEME`, `DARK_THEME`.
- `theme/typography.py`: Família de fontes, escala tipográfica, `font()`, `themed_font()`, `mono_font()`.
- `theme/spacing.py`: Espaçamentos, raios e elevações.
- `theme/colors.py`: Utilitários de cor e constantes semânticas.
- `components/icons.py`: Dicionário de ícones, `IconLabel`, `IconButton`.

#### 3.2.9 `utils/`

- `async_runner.py`: `AsyncRunner.run()` para execução em background com callback na UI.
- `widget_batch.py`: `WidgetBatchBuilder` para renderização em lote.
- `service_helpers.py`: `with_api_fallback()`.
- `mappers.py`: Mapeamento entre modelos de API, domínio e repositório.
- `dates.py`: Helpers de data.
- `chart.py`: Integração com gráficos.
- `cache.py`: `NotificationCache` (TTL).
- `mood.py`: Helpers de humor/bem-estar.
- `avatar_utils.py`: Utilitários de avatar.
- `logging_config.py`: Configuração de logging.

#### 3.2.10 `sql/`

- `ser_pleno.sql`: Schema MySQL completo.
- `add_file_fields.sql` / `add_file_fields.py`: Migração para campos de arquivo.
- `add_agendamento_modificado.sql`: Migração de agendamento.

#### 3.2.11 `assets/`

- `avatars/`: Imagens de avatar.
- `icons/`: Ícones de tela.
- `Music/background_music.mp3`: Música de fundo do login (Windows).

#### 3.2.12 `logs/`

- `ser_pleno_desktop.log`: Arquivo de logs da aplicação.

#### 3.2.13 `docs/` (interno)

- `resumo_implementacao_chat_grupo.md`
- `MODO_INDEPENDENTE.md`
- `chat_grupo_implementado.md`
- `ANALISE_ORIENTACOES.md`
- `ALTERACOES_COMUNICACAO.md`

---

## 4. Tecnologias e Dependências Principais

### 4.1 Runtime

- `customtkinter` >= 5.2.2
- `mysql-connector-python` >= 9.5.0
- `requests` >= 2.32.5
- `passlib` >= 1.7.4
- `pillow` >= 12.1.0
- `python-dateutil` >= 2.9.0
- `darkdetect` >= 0.8.0
- `matplotlib` >= 3.10.8
- `numpy` >= 2.4.1

### 4.2 Build / Dev

- `pytest`, `pytest-cov`
- `ruff`, `mypy`
- `pyinstaller`, `setuptools`, `wheel`

### 4.3 Bancos

- MySQL como fonte primária.
- SQLite como cache local e fallback offline (`ser_pleno_local.db`).

---

## 5. Padrões Arquiteturais

### 5.1 Camadas

- **Presentation:** Views + componentes reutilizáveis.
- **Controllers:** Mediação entre UI e regras de negócio.
- **Services:** Orquestração e fallback API/local.
- **Repositories:** Acesso a dados com fallback MySQL → SQLite.
- **Infrastructure:** API, conectividade, sincronização e cache local.

### 5.2 Repository Pattern com fallback offline-first

Decisão formal em `docs/adr/ADR-001-repository-pattern-fallback.md`. O acesso a dados sempre passa por repositórios; decorators interceptam erros de conexão MySQL e redirecionam para SQLite.

### 5.3 Fallback API → Local

Helper `with_api_fallback()` em `utils/service_helpers.py`. Services tentam a API primeiro e, em caso de indisponibilidade, usam repositório local.

### 5.4 Injeção de dependência explícita (auth_service)

Decisão formal em `docs/adr/ADR-002-auth-injection-via-controller.md`. `auth_service` é injetado via construtor, removendo estado global.

### 5.5 Navegação e tema

- `ViewFactory` + `NavigationManager` + `ThemeManager`.
- Cache de views (LRU com `VIEW_CACHE_MAXSIZE=8`), pré-criação e reloaders.

### 5.6 Design system modular

Pasta `ui/theme/` dividida em paleta, tipografia, espaçamento e cores, com `extend_theme()` para paletas locais.

### 5.7 Concorrência e renderização

- `AsyncRunner`: threads daemon + callbacks na thread principal.
- `WidgetBatchBuilder`: renderização em lotes para reduzir flickering.

### 5.8 Sincronização

`SyncService` em background gerencia fila offline, reconciliação de IDs locais negativos e sincronização MySQL ↔ SQLite ↔ API.

### 5.9 Modos de operação

- `INDEPENDENT`: apenas SQLite.
- `HYBRID`: independente com sincronização opcional.
- `CONNECTED`: requer conexão com SerPleno Web.
- `DB_PRIMARY`: MySQL como primário, API como fallback (padrão).

---

## 6. Fluxos Principais

### 6.1 Login

1. `App.__init__()` exibe `LoginFrame`.
2. Validação de campos e chamada a `AutenticacaoController.login()`.
3. `ServicoAutenticacao.login()` consulta MySQL via repositório e valida hash com `passlib`.
4. Em sucesso, estabelece sessão Django em background.
5. `App.iniciar_sistema()` cria sidebar, área de conteúdo, pré-carrega dashboard e executa seed pós-login.

### 6.2 CRUD de Estudantes

1. View carrega dados via `AsyncRunner`.
2. Service verifica disponibilidade de API; se indisponível, cai para MySQL; se MySQL indisponível, cai para SQLite.
3. Escrita usa `write_with_fallback()`: grava no MySQL, aplica no SQLite e enfileira sync; se falhar, grava apenas no SQLite.

### 6.3 Agenda

1. Grid do dia e próxima semana é carregado por serviço, com fallback MySQL → API → SQLite.
2. Criação/atualização/deleção seguem o padrão de escrita com fallback e sync com SerPleno Web em background.

### 6.4 Sincronização

1. `SyncService` executa ciclos periódicos.
2. Aplica fila offline no MySQL quando ele volta.
3. Puxa atualizações MySQL → SQLite.
4. Processa fila na API quando disponível.
5. Reconcilia IDs locais com IDs do servidor.

### 6.5 Comunicação

1. Contatos são carregados por papel.
2. Mensagens são atualizadas periodicamente (privado e grupo).
3. Suporte a envio de arquivos com categorias.

### 6.6 Notificações (Dashboard)

1. Notificações de ajuda vêm da API.
2. Notificações de alertas vêm do repositório local.
3. `NotificationCache` gerencia TTL para evitar consultas repetidas.

---

## 7. Pontos de Atenção para Documentação e Operação

### 7.1 Regras e constraints relevantes

- `psychologist_id` em `desktop_orientation` aceita `INT NULL`; valores não numéricos devem ser convertidos para `NULL`.
- `aluno.professor_responsavel` é `VARCHAR(200) NOT NULL` sem default; inserts devem fornecer valor ou usar `'Não informado'`.
- É proibido usar dados mock/hardcoded em controllers, services ou APIs.

### 7.2 Decisões arquiteturais relevantes

- ADR-001: Repository Pattern com fallback offline-first.
- ADR-002: Injeção de `auth_service` via controller.
- Rejeições registradas: DI Container, Event Bus, SQLAlchemy, `core/` package e domain model enrichment.

### 7.3 Build e empacotamento

- Comando: `python -m PyInstaller --clean --noconfirm SerPleno.spec`.
- Dependências de build em `requirements-build.txt`.
- Distribuição da pasta `dist\SerPleno\` completa.
- Em modo onefile, arquivos graváveis em runtime devem usar diretório alternativo fora `_MEI`, pois `_MEI` não inclui `ser_pleno/config/`.

### 7.4 Performance

- Target: operações abaixo de 500ms.
- Problemas conhecidos mapeados em `project.md`: badge de notificações com queries extras, lag em filtros de estudantes, freeze em navegação de agenda por `refresh_all()` síncrono e queries duplicadas.

### 7.5 Perfis e grupos

- Perfis relevantes: `admin`, `analista`, `coordenador`, `suporte`.
- Suporte a chat de grupo e mural de avisos institucionais.

### 7.6 Testes

- 166 testes informados no README.
- Cobertura configurada em `pyproject.toml`.
- Fixtures usam `mock_network` para evitar chamadas reais em testes automatizados.

### 7.7 Execução

- Rodar aplicação: `python app.py` a partir de `src\ser_pleno`.
- Testes: `pytest -v --tb=short`.
