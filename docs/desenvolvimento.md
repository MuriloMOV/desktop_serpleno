# Guia do Desenvolvedor — SerPleno Desktop

**Data:** 2026-07-15  
**Versão:** 1.0  
**Escopo:** Este guia cobre a arquitetura, convenções e padrões do projeto `ser_pleno`.

---

## 1. Arquitetura em camadas

O projeto segue uma arquitetura em camadas com separação explícita de responsabilidades:

```
Presentation (views + components)
    ↓ calls
Controllers (mediação explícita)
    ↓ calls
Services (lógica de negócio + fallback API/local)
    ↓ calls
Repositories (SQL → MySQL com fallback SQLite)
    ↓
MySQL / SQLite (local_cache)
```

### 1.1 Camada Presentation

- **Views:** Frames CustomTkinter em `src/ser_pleno/presentation/views/`
- **Components:** Componentes reutilizáveis em `src/ser_pleno/presentation/components/`
- **Base:** `BaseViewFrame` fornece header padronizado e helper `_load_async()`

### 1.2 Camada Controllers

- **Localização:** `src/ser_pleno/application/controllers/`
- **Base:** `BaseController` — recebe `service_class` no `__init__`
- **Responsabilidade:** Mediação explícita entre View e Service
- **Padrão:** `controller.get_service().metodo()`

### 1.3 Camada Services

- **Localização:** `src/ser_pleno/application/services/`
- **Responsabilidade:** Lógica de negócio, orquestração de repositórios, fallback API/local
- **Padrão de fallback:** `with_api_fallback(api_fn, fallback_fn, *args)`

### 1.4 Camada Repositories

- **Localização:** `src/ser_pleno/repositories/`
- **Responsabilidade:** Acesso a dados, SQL, fallback MySQL → SQLite
- **Decorators:** `with_local_fallback`, `write_with_fallback`

---

## 2. Como adicionar uma nova tela

### Passo 1: Criar a View

**Arquivo:** `src/ser_pleno/presentation/views/<nome>.py`

```python
from ser_pleno.presentation.views.base import BaseViewFrame

class MinhaViewFrame(BaseViewFrame):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(
            parent, controller,
            title="Minha Tela",
            subtitle="Descrição da tela",
            **kwargs
        )
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # Construir widgets aqui
        pass

    def load_data(self):
        # Carregar dados assíncronos aqui
        pass
```

### Passo 2: Criar o Controller

**Arquivo:** `src/ser_pleno/application/controllers/<nome>.py`

```python
from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.<nome> import Servico<nome>

class <Nome>Controller(BaseController):
    def __init__(self, auth_service=None):
        super().__init__(Servico<nome>, auth_service=auth_service)

    def listar(self):
        return self.get_service().listar()
```

### Passo 3: Criar o Service

**Arquivo:** `src/ser_pleno/application/services/<nome>.py`

```python
from ser_pleno.repositories.<nome> import <Nome>Repository
from ser_pleno.utils.service_helpers import with_api_fallback

class Servico<nome>:
    def __init__(self, auth_service=None):
        self.repo = <Nome>Repository()
        self._auth_service = auth_service

    def listar(self):
        # Implementar lógica de negócio
        pass
```

### Passo 4: Criar o Repository

**Arquivo:** `src/ser_pleno/repositories/<nome>.py`

```python
from ser_pleno.repositories.base import with_local_fallback

class <Nome>Repository:
    @with_local_fallback("_local_listar")
    def listar(self):
        # SQL query aqui
        pass

    def _local_listar(self):
        # Fallback SQLite
        pass
```

### Passo 5: Registrar no menu

**Arquivo:** `src/ser_pleno/presentation/navigation.py`

Adicionar em `MENU_ITEMS`:

```python
{"key": "minha_tela", "label": "Minha Tela", "icon": ICONS["..."],
 "header": ("Minha Tela", "Descrição")}
```

**Nota:** Views devem usar nomes de arquivo curtos e consistentes:
- ✅ `triagem.py`, `comunicacao.py`, `avisos.py`
- ❌ `analise_triagem.py`, `comunicacao_interna.py`, `quadro_avisos.py`

Controllers seguem a mesma regra:
- ✅ `controllers/triagem.py`, `controllers/avisos.py`

---

## 3. Convenções de código

| Elemento | Padrão | Exemplo |
|----------|--------|---------|
| Classes | PascalCase | `ServicoEstudante`, `BaseViewFrame`, `NavigationManager` |
| Métodos/funções | snake_case (inglês) | `create_sidebar()`, `update_menu()`, `_build_ui()` |
| Privados | Prefixo `_` | `_load_async()`, `_local_listar()` |
| Constantes | UPPER_SNAKE_CASE | `MENU_ITEMS`, `API_BASE_URL` |
| Logging | `logger.{debug,info,warning,error}` | `logger.info("Estudantes carregados")` |
| Type hints | Obrigatórios em métodos públicos | `def listar(self, id: int) -> dict:` |
| Docstrings | Google-style em classes públicas | Ver exemplo abaixo |

### Nomenclatura — NavigationManager

Métodos devem usar inglês:

| Antes (pt-br) | Depois (inglês) |
|---------------|-----------------|
| `criar_sidebar()` | `create_sidebar()` |
| `criar_area_conteudo()` | `create_content_area()` |
| `atualizar_menu(key)` | `update_menu(key)` |
| `atualizar_header(title, subtitle)` | `update_header(title, subtitle)` |
| `limpar_tela()` | `clear_screen()` |
| `_criar_marca()` | `_create_brand()` |
| `_criar_rodape_sidebar()` | `_create_sidebar_footer()` |
| `_criar_menu()` | `_create_menu()` |
| `_criar_botao_menu()` | `_create_menu_button()` |
| `_aplicar_estilo_botao_menu()` | `_apply_menu_button_style()` |

### Nomenclatura — Views e Controllers

Usar nomes curtos e consistentes:

| Padrão correto | Incorreto |
|----------------|-----------|
| `views/triagem.py` + `TriagemFrame` | `views/analise_triagem.py` + `AnaliseTriagemFrame` |
| `views/comunicacao.py` + `ComunicacaoFrame` | `views/comunicacao_interna.py` + `ComunicacaoInternaFrame` |
| `views/avisos.py` + `AvisosFrame` | `views/quadro_avisos.py` + `QuadroAvisosFrame` |
| `controllers/triagem.py` + `TriagemController` | `controllers/analise_triagem.py` + `AnaliseTriagemController` |
| `controllers/avisos.py` + `AvisosController` | `controllers/quadro_avisos.py` + `QuadroAvisosController` |

### Exemplo de docstring

```python
class ServicoEstudante:
    """Serviço para gerenciar estudantes.
    
    Funciona de forma independente com sincronização opcional
    com a API do SerPleno Web.
    """

    def listar_estudantes(self, busca: str = "") -> dict:
        """Lista estudantes com filtros opcionais.
        
        Args:
            busca: Termo de busca para filtrar por nome.
            
        Returns:
            Dict com chaves `success`, `data`, `pagination`.
        """
```

---

## 4. Padrões existentes

### 4.1 Fallback API → Local

```python
from ser_pleno.utils.service_helpers import with_api_fallback

def listar_estudantes(self, busca: str = "") -> dict:
    def _api_call():
        resp = self._api.get("students/", params={"search": busca})
        if resp and resp.get("success") is not False:
            return resp
        return None

    return with_api_fallback(
        _api_call,
        self._listar_estudantes_local,
        busca,
    )
```

### 4.2 Fallback MySQL → SQLite (Repository)

```python
from ser_pleno.repositories.base import with_local_fallback

class EstudanteRepository:
    @with_local_fallback("_local_listar")
    def listar(self, busca: str = "") -> list:
        # SQL query no MySQL
        pass

    def _local_listar(self, busca: str = "") -> list:
        # Fallback SQLite
        pass
```

### 4.3 Write com fallback + sync queue

```python
from ser_pleno.repositories.base import write_with_fallback

def criar(self, dados: dict) -> int:
    def mysql_fn():
        # INSERT no MySQL
        pass

    def local_fn(mysql_result):
        # INSERT no SQLite
        pass

    return write_with_fallback(
        mysql_fn, local_fn,
        operation="create",
        entity="estudante",
        entity_id=dados.get("id"),
    )
```

### 4.4 Async loading na View

```python
from ser_pleno.utils.async_runner import AsyncRunner

def load_data(self):
    self._load_async(
        fetch_fn=self._fetch_data,
        on_success=self._on_data_loaded,
        on_error=self._on_error,
    )

def _load_async(self, fetch_fn, on_success, on_error=None):
    AsyncRunner.run(
        task=fetch_fn,
        on_success=on_success,
        on_error=on_error,
        widget_ref=self,
    )
```

### 4.5 Injeção de auth

```python
# Controller
class AutenticacaoController(BaseController):
    def __init__(self, auth_service=None):
        super().__init__(ServicoAutenticacao, auth_service=auth_service)

# App
def iniciar_sistema(self, user_data, auth_service=None):
    self.auth_service = auth_service
    # Controllers recebem auth_service via __init__
```

### 4.6 Theme tokens por view

```python
from ser_pleno.ui.theme_extensions import extend_theme, spacing

Q = extend_theme(THEME, {
    "input_border": "#E5E7EB",
    "text_light": "#9CA3AF",
})

# Uso:
spacing("sm")  # ao invés de SPACING["item_gap"]
Q["input_border"]  # ao invés de THEME["input_border"]
```

### 4.7 Listeners de tema

```python
from ser_pleno.ui.theme import on_theme_change

def _on_theme_changed(self, mode: str) -> None:
    # Reconstruir UI com novas cores
    pass

on_theme_change(self._on_theme_changed)
```

### 4.8 Estrutura modular do tema

O design system foi dividido em módulos especializados dentro de `ser_pleno/ui/theme/`:

```python
# Import de ponto único (mantém compatibilidade)
from ser_pleno.ui.theme import (
    THEME, SPACING, RADIUS, ELEVATION,
    LIGHT_THEME, DARK_THEME,
    font, themed_font, mono_font,
    blend_color, darken, lighten, shift_hue, readable_text_color,
    get_theme, current, get_mode,
    on_theme_change, off_theme_change, set_mode, toggle_mode, apply_global_style,
)

# Imports diretos de módulos específicos (opcional)
from ser_pleno.ui.theme.palette import LIGHT_THEME, DARK_THEME
from ser_pleno.ui.theme.typography import FONT_FAMILY, TYPO, font, themed_font
from ser_pleno.ui.theme.spacing import SPACING, RADIUS, ELEVATION
from ser_pleno.ui.theme.colors import SEMANTIC_COLORS, STATUS_COLORS, blend_color
```

**Arquitetura:**
- `palette.py` — Paletas de cor light/dark
- `typography.py` — Famílias de fonte, escala tipográfica, helpers de fonte
- `spacing.py` — Espaçamento, raio, elevação
- `colors.py` — Utilitários de manipulação de cor + constantes semânticas
- `__init__.py` — Estado do tema ativo, listeners, re-exports

---

## 5. Estrutura do projeto

```
src/ser_pleno/
├── app.py                          # Entry point, ~130 linhas
├── presentation/
│   ├── navigation.py               # NavigationManager — sidebar, menu, conteúdo
│   ├── theme_manager.py            # ThemeManager — toggle e reconstrução de UI
│   ├── view_factory.py             # ViewFactory — instancia views por chave
│   ├── components/
│   │   ├── ui_components.py        # Componentes reutilizáveis (Card, KPICard, Avatar...)
│   │   └── icons.py                # Ícones e constantes de emoji
│   └── views/
│       ├── base.py                 # BaseViewFrame — header + async loading
│       ├── login.py
│       ├── dashboard.py
│       ├── estudantes.py
│       ├── agenda.py
│       ├── bem_estar.py
│       ├── triagem.py              # Antiga: analise_triagem.py
│       ├── relatorios.py
│       ├── comunicacao.py          # Antiga: comunicacao_interna.py
│       ├── orientacoes.py
│       ├── avisos.py               # Antiga: quadro_avisos.py
│       └── configuracoes.py
├── application/
│   ├── controllers/
│   │   ├── base.py                 # BaseController
│   │   ├── autenticacao.py
│   │   ├── dashboard.py
│   │   ├── estudantes.py
│   │   ├── agenda.py
│   │   ├── bem_estar.py
│   │   ├── triagem.py              # Antiga: analise_triagem.py
│   │   ├── relatorio.py
│   │   ├── comunicacao.py
│   │   ├── orientacoes.py
│   │   ├── avisos.py               # Antiga: quadro_avisos.py
│   │   └── configuracoes.py
│   ├── services/
│   │   └── ... (10 services)
│   └── bootstrap.py                # BootstrapService — seed pós-login
├── infrastructure/
│   ├── api/
│   │   ├── api.py                  # ClienteAPI — HTTP client centralizado
│   │   ├── mural.py                # ServicoMural — mural de avisos
│   │   ├── sync_service.py         # Fila de sincronização
│   │   └── connectivity.py         # Health check da API
│   └── local/
│       ├── local_cache.py          # SQLite fallback
│       ├── fallback_metrics.py     # Métricas de fallback
│       └── seed_service.py         # Seed de dados locais
├── repositories/
│   ├── base.py                     # BaseRepository + helpers de ID local
│   ├── fallback.py                 # Decorators: with_local_fallback, write_with_fallback
│   └── ... (10 repositories)
├── domain/
│   └── models/                     # Dataclasses (opcional, não obrigatório)
├── config/
│   ├── config.py                   # Configurações gerais
│   ├── db_config.py                # Conexão MySQL
│   └── operation_mode.py           # Modo de operação (independent/hybrid/connected)
├── ui/
│   ├── theme/                      # Design system modular
│   │   ├── __init__.py             # Ponto de entrada: THEME, toggle_mode, listeners
│   │   ├── palette.py              # LIGHT_THEME, DARK_THEME
│   │   ├── typography.py           # FONT_FAMILY, TYPO, font(), themed_font()
│   │   ├── spacing.py              # SPACING, RADIUS, ELEVATION
│   │   └── colors.py               # Utilitários de cor + constantes semânticas
│   ├── theme_extensions.py         # extend_theme() + spacing()
│   └── components/
│       └── icons.py                # Ícones (ICONS, IconLabel, IconBadge, IconButton)
└── utils/
    ├── async_runner.py             # AsyncRunner — threading seguro para UI
    ├── service_helpers.py          # with_api_fallback()
    ├── mappers.py                  # Utilitários de mapeamento genéricos
    └── ...
```

---

## 6. Comandos úteis

```bash
# Executar aplicação
python app.py

# Rodar testes
pytest -v --tb=short

# Coverage
pytest --cov=src/ser_pleno --cov-report=html

# Lint
ruff check src/
```

---

## 7. Decisões arquiteturais

Consultar `docs/adr/` para decisões formais:
- ADR-001: Repository Pattern + fallback MySQL → SQLite
- ADR-002: Injeção de auth via controller (Fase 1)

Decisões excluídas do escopo atual:
- DI Container: over-engineering para ~10 telas
- Event Bus: nenhum fluxo complexo identificado
- SQLAlchemy: SQL raw funciona, migração traria risco sem ganho claro
