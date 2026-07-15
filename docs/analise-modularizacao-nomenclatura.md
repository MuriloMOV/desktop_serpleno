# Análise de Modularização e Nomenclatura
## Projeto `desktop_serpleno` — `src/ser_pleno/`

**Data:** 2026-07-15  
**Tipo:** Análise estrutural e de nomenclatura  
**Status:** Concluída

---

## 1. Estrutura Atual Resumida

```
src/ser_pleno/
├── app.py                              # Entry point, classe App(ctk.CTk)
├── application/
│   ├── controllers/                    # 10 controllers + base.py
│   └── services/                       # 10 services
├── config/
│   ├── config.py                       # URLs e tokens da API
│   ├── db_config.py
│   └── operation_mode.py
├── domain/models/                      # 5 entidades de domínio
├── infrastructure/
│   ├── api/                            # ClienteAPI, sync_service, connectivity, mural
│   └── local/                          # SQLite fallback, cache, seed
├── presentation/
│   ├── components/
│   │   ├── icons.py                    # ⚠️ Re-export de ui/components/icons.py
│   │   └── ui_components.py            # Biblioteca de widgets reutilizáveis
│   ├── views/                          # 10 views + base + login
│   ├── navigation.py                   # NavigationManager (roteador + factory)
│   └── theme_manager.py                # ThemeManager
├── repositories/                       # 10 repositories + base.py
├── ui/
│   ├── theme.py                        # Fonte única do tema (~500 linhas)
│   ├── theme_extensions.py             # Helpers de tema
│   └── components/icons.py             # Fonte única dos ícones
└── utils/
    ├── mappers.py                      # Mapeadores DB → dict (nomes em pt-br)
    ├── service_helpers.py              # with_api_fallback
    └── async_runner.py
```

---

## 2. Problemas de Nomenclatura Encontrados

### 2.1 Inconsistência pt-br vs inglês

| Local | Problema | Exemplo |
|---|---|---|
| `utils/mappers.py` | Funções em pt-br em arquivo de utils | `mapear_alerta()`, `mapear_pedido()`, `mapear_contato()`, `mapear_mensagem()` |
| `presentation/navigation.py` | Variáveis misturadas | `titulo`, `subtitulo` (pt-br) vs `key`, `label`, `MENU_ITEMS` (inglês) no mesmo arquivo |
| `repositories/base.py` | Parâmetros/documentação em pt-br | `local_fn_name`, docstrings em pt-br |

### 2.2 Nomes de arquivo de view inconsistentes

Alguns usam underscore em nomes compostos, outros não:
- `analise_triagem.py`
- `comunicacao_interna.py`
- `quadro_avisos.py`

Compare com `dashboard.py`, `estudantes.py`, `orientacoes.py`, `relatorio.py`, `configuracoes.py` — todos com termo principal único.

### 2.3 Ambiguidade entre `ui/` e `presentation/components/`

Ambas contêm código de UI/componentes visuais, sem demarcação clara de qual é a pasta "canônica".

---

## 3. Problemas de Modularização/Coesão

### 3.1 Duplicação de ícones — **ALTA**

`presentation/components/icons.py` re-exporta todo o conteúdo de `ui/components/icons.py` e adiciona apenas uma classe legado (`IconLabel` como `CTkFrame`). Qualquer alteração no dicionário `ICONS` precisa ser feita em `ui/components/icons.py`, mas o re-export em `presentation/` cria uma segunda superfície de importação. Views podem importar de qualquer um dos dois caminhos, gerando confusão.

**Caminhos conflitantes:**
```python
from ser_pleno.presentation.components.icons import ICONS
from ser_pleno.ui.components.icons import ICONS
```

### 3.2 `repositories/base.py` com múltiplas responsabilidades — **ALTA**

Um único arquivo (~130 linhas) concentra:
- Classe `BaseRepository` + helpers de ID local (`generate_local_id`, `is_local_id`)
- Decorator factory `with_local_fallback()` — lógica de resiliência
- Função `write_with_fallback()` — lógica de sync queue
- Funções SQL genéricas: `execute_query`, `fetch_all`, `fetch_one`, `execute_non_query`

A função `execute_query` não é um padrão repository — é acesso direto ao banco, e sua presença aqui viola a camada. O decorator `with_local_fallback` mistura preocupações de resiliência com estrutura de repositório.

### 3.3 `NavigationManager` acumula múltiplos papéis — **ALTA**

Em `presentation/navigation.py`, a classe faz:
1. Criação da sidebar
2. Criação da área de conteúdo
3. Factory de views (instancia `DashboardFrame`, `EstudantesFrame`, etc.)
4. Gestão de estado de navegação
5. Atualização de header

O arquivo também tem importações diretas de todas as 10 views, criando acoplamento forte. Qualquer nova tela exige edição deste arquivo.

### 3.4 Views recebendo `app` diretamente — **MÉDIA**

`BaseViewFrame.__init__` recebe `controller`, mas em `navigation.py`:
```python
# QuadroAvisosFrame não tem controller dedicado:
frame = frame_cls(self.app.content_body, app=self.app)
# Outras views recebem self.app como controller:
frame = frame_cls(self.app.content_body, self.app)
```

Isso quebra o padrão controller-view: views devem receber apenas o controller, nunca o `App` completo.

### 3.5 `ThemeManager` acessa atributos privados de `NavigationManager` — **MÉDIA**

```python
tela_anterior = self.app.navigation._menu_ativo or "dashboard"
```

Acesso direto a `_menu_ativo` (atributo privado com prefixo `_`). Quebra encapsulamento. Deve haver um método público como `get_active_screen()`.

### 3.6 Instância singleton `api` em módulo — **MÉDIA**

```python
api = ClienteAPI()
```

Criada sem `auth_service`, é inconsistente com a Fase 1 já concluída. Controllers recebem `auth_service` injetado, mas `api` global não.

### 3.7 `app.py` com responsabilidades excessivas — **MÉDIA**

A classe `App`:
- Gerencia janela, login, navegação, tema
- Conhece detalhes de `infrastructure/api/sync_service`
- Conhece detalhes de `infrastructure/local/seed_service`
- Cria threads inline para seed pós-login (`_run_post_login_seed`)
- Mistura atributos de performance (`_t_boot`, `_t_boot_fim`, `_t_login_fim`, etc.) com lógica de negócio

A lógica de seed e sync deveria ser delegada a um serviço de inicialização/bootstrapper.

### 3.8 `ui/theme.py` muito grande (~500 linhas) — **MÉDIA**

Contém em um único arquivo:
- Paletas LIGHT_THEME e DARK_THEME completas
- Tipografia
- Sistema de listeners de tema
- Helpers de cor
- Constantes semânticas
- Espaçamento, raio, elevação, animação

Dificulta manutenção e navegação.

### 3.9 `utils/mappers.py` com funções em pt-br — **MÉDIA**

`mapear_alerta`, `mapear_pedido`, `mapear_contato`, `mapear_mensagem` estão em pt-br, quebrando convenção do restante do projeto. Adicionalmente, estes mappers são específicos de domínio (comunicação) e estão em `utils/` — localização incorreta.

### 3.10 Nomes de variáveis em pt-br dentro de código em inglês

```python
titulo, subtitulo = item["header"]
self._menu_ativo = active_key
```

Inconsistência intra-arquivo.

---

## 4. Sugestões de Refatoração Priorizadas

### Alta Prioridade

| # | Problema | Sugestão |
|---|---|---|
| 1 | Duplicação `icons.py` | Unificar em `ui/components/icons.py`. Remover re-export de `presentation/components/icons.py`. Atualizar todas as views. |
| 2 | `NavigationManager` com múltiplos papéis | Separar em `NavigationManager` puro + `ViewFactory`/`Router`. |
| 3 | Views recebendo `app` como controller | Garantir que toda view receba um controller. |

### Média Prioridade

| # | Problema | Sugestão |
|---|---|---|
| 4 | `repositories/base.py` com múltiplas responsabilidades | Dividir em `repositories/base.py`, `repositories/fallback.py`, `infrastructure/db/query_helpers.py`. |
| 5 | Acesso a `_menu_ativo` | Adicionar método público `get_active_screen()`. |
| 6 | Instância singleton `api = ClienteAPI()` | Remover a instância global. |
| 7 | `app.py` com lógica de seed e sync | Mover para `BootstrapService`. |
| 8 | Nomes pt-br em `utils/mappers.py` | Renomear e mover para localização de domínio. |
| 9 | Inconsistência de nomes de view | Padronizar nomes. |

### Baixa Prioridade

| # | Problema | Sugestão |
|---|---|---|
| 10 | `ui/theme.py` muito grande | Dividir em módulos menores. |
| 11 | Variáveis pt-br em `navigation.py` | Renomear para inglês. |
| 12 | `utils/service_helpers.py` genérico | Mover para localização mais específica. |
| 13 | Ambiguidade `ui/` vs `presentation/components/` | Definir papéis claros. |

---

## 5. Observações Positivas

- Arquitetura em camadas bem definida
- Padrão BaseController/BaseViewFrame bem aplicado
- Sistema de tema robusto
- Resiliência offline bem implementada
- Documentação abundante
- Type hints consistentes
- Componentes UI reutilizáveis bem construídos
- AsyncRunner para operações não-bloqueantes
- Métricas de performance instrumentadas
- Fase 1 de refatoração já concluída

---

*Documento gerado automaticamente pela análise estrutural do projeto.*
