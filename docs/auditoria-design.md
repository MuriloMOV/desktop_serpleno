# Relatório de Auditoria de Design — SerPleno Desktop

**Data:** 2026-06-30  
**Escopo:** Aplicação desktop Python/CustomTkinter — 11 telas + design system + componentes reutilizáveis  
**Metodologia:** Análise estrutural file-by-file, cruzamento de tokens do design system contra implementação real, verificação de consistência semântica e arquitetura.

---

## 1. Análise de Viabilidade

A aplicação apresenta um **design system tecnicamente sólido** em `ui_theme.py` com tokens semânticos completos, tipografia escalonada e suporte a tema claro/escuro. A arquitetura MVC está bem separada e os componentes reutilizáveis (`ui_components.py`) demonstram maturidade. **Porém, a aderência real a esse sistema é parcial e decrescente à medida que se entra nas features específicas**, comprometendo a manutenibilidade em médio prazo.

---

## 2. Erros Críticos (Bloqueantes / Crash Risk)

| ID | Severidade | Local | Problema | Impacto |
|---|---|---|---|---|
| **E-01** | 🔴 Crítica | `views/base.py:82` | `ctk.CTkMessagebox` não existe no CustomTkinter. Deveria ser `tkinter.messagebox` ou modal customizado. | **Crash** ao clicar em qualquer ação de erro em views que herdam de `BaseViewFrame` |
| **E-02** | 🔴 Crítica | `views/login.py:530-537` | Duplicação do botão "Política de Privacidade" dentro de `_fazer_login()` sem destruir a instância anterior. | Vazamento de widgets, empilhamento visual e potencial crash ao múltiplos cliques |
| **E-03** | 🔴 Crítica | `views/agenda.py:212` | `values[0]` sem validação se `values` é vazia — `IndexError` se horários base for `[]`. | Crash ao abrir modal de agenda sem horários configurados |
| **E-04** | 🔴 Crítica | `views/estudantes.py:385-389` | `setattr(self, attr, lbl)` na linha 385 é imediatamente sobrescrito por `self.card_email = None` etc. na linha 386. | Os cards de perfil do estudante nunca são acessíveis — referências são `None` |
| **E-05** | 🔴 Crítica | `ui_theme.py:133-140, 174-180` | Duplicidade de chaves (`chart_grid`, `chart_line`, `chart_fill`, `dot_*`) no `LIGHT_THEME`. Python sobrescreve silenciosamente, gerando manutenibilidade duplicada. | Atualizações parciais quebram gráficos sem traceback |

---

## 3. Falhas de Estrutura (Manutenibilidade / Arquitetura)

### 3.1 Fragmentação do Design System (Ilhas de Tokens)

Cada view "especializada" redefine seu próprio dicionário de tokens, ignorando o design system central:

| Arquivo | Dicionário Próprio | Problema |
|---|---|---|
| `orientacoes.py` | `O = {...}` | 50+ linhas de tokens hardcoded, duplicando cores, espaçamentos e fontes |
| `quadro_avisos.py` | `Q = {...}` | Mesma situação — tokens não compartilhados |
| `comunicacao_interna.py` | `_CHAT_AVATAR_COLORS` (hardcoded) | Cores de avatar não derivam de `ui_theme.py` |
| `dashboard.py` | `_PRIORITY_COLOR` hardcoded | Cores de alerta hardcoded em vez de `THEME["critico"]` etc |

**Causa-raiz:** Ausência de um mecanismo de herança/extensão de tema para features específicas. Se a marca mudar de índigo para azul, 4 arquivos precisam ser editados separadamente.

### 3.2 Duplicação de Componentes Auxiliares

Padrão repetido em 5+ arquivos (`estudantes.py`, `bem_estar.py`, `relatorio.py`, `orientacoes.py`, `quadro_avisos.py`):

```python
def _card(parent, **kw): ...
def _avatar(parent, initials, color, size): ...
def _chip(parent, text, ...): ...
```

Cada reimplementação tem pequenas variações (raio de borda, fonte, cor), fragmentando o design system. O `ui_components.py` já exporta `Card`, `Avatar`, `Badge`/`Pill`, mas não são usados.

### 3.3 Hardcoding de Fonte

`orientacoes.py`, `quadro_avisos.py` e `comunicacao_interna.py` usam `ctk.CTkFont("Segoe UI", ...)` diretamente. O `ui_theme.py` define `FONT_FAMILY` dinamicamente por plataforma (Windows → Segoe UI, macOS → Helvetica Neue, Linux → Inter), mas o hardcoding quebra essa adaptabilidade. Em macOS, a app usaria Segoe UI (não disponível) ao invés do fallback correto.

---

## 4. Inconsistências de Design (UI/UX)

### 4.1 KPI Cards — Falta de Padronização

Existem **5 implementações diferentes** de KPI Card:

| Arquivo | Classe | Diferenças Visuais |
|---|---|---|
| `ui_components.py` | `KPICard` | Ícone com fundo blend, valor h1, barra de progresso opcional |
| `dashboard.py` | `_KPICard` | Ícone em círculo, valor h2, barra de acento na base |
| `bem_estar.py` | `_KPICard` | Ícone em quadrado, valor grande, barra inferior |
| `relatorio.py` | `_KPICard` | Ícone em quadrado, valor h2, sem barra |
| `analise_triagem.py` | `_KPICard` | Ícone quadrado menor, valor display (36px) |

**Impacto:** Mesmo conceito visual com 5 aparências diferentes. Usuário não estabelece padrão cognitivo.

### 4.2 Espaçamentos Inconsistentes

| View | Padrão Used | Observação |
|---|---|---|
| `app.py` content_body | `padx=24, pady=(0, 24)` | Hardcoded |
| `base.py` header | `SPACING["page_x"]=32, SPACING["page_y"]=28` | Usa tokens |
| `orientacoes.py` header | `padx=28, pady=(20, 4)` | Hardcoded — foge do grid system |
| `quadro_avisos.py` modal | `padx=20, pady=12` | Hardcoded em vários pontos |

### 4.3 Cores Hardcoded Subtraem do Tema

- `comunicacao_interna.py` linha 160: `fg_color="#F3F4F6"` ao invés de `THEME["bg_alt"]`
- `comunicacao_interna.py` linha 192: `scrollbar_button_color="#D1D5DB"` ao invés de `THEME["border_strong"]`
- `login.py` hardcoded `#1E1B4B`, `#312E81`, `#4338CA`, `#6D5CE8` (justificável como gradiente de marca, mas sem fallback para dark mode)

### 4.4 Estados de Hover/Foco Inconsistentes

- `GhostButton` (componente) não define `border_width` padrão. A sidebar `app.py` precisa adicionar manualmente `border_width=1` quando ativo. Se outra view usar `GhostButton` esperando borda, terá comportamento invisível.
- `estudantes.py` botões "Editar" usam `PrimaryButton` com `fg_color=THEME["primary_soft"]` e `text_color=THEME["primary"]` — visual de botão outline, mas Tipologia é de botão primário. Confuso semanticamente.
- Foco por teclado: `comunicacao_interna.py` e `quadro_avisos.py` usam `cursor="hand2"` em frames clicáveis, mas não respondem a `<Tab>` nem `<Return>` — acessibilidade prejudicada.

### 4.5 Toggle de Tema Não Propaga Completamente

`app.py:atualizar_tema_widgets()` percorre `self.winfo_children()` e chama `configure()` cegamente. Views com componentes filhos profundos (ex.: `NotificationPanel`, `ProfileModal`, `AppointmentModal`) não são atualizadas porque são `CTkToplevel` não-filhas diretas da janela principal.

---

## 5. Riscos de Performance

| ID | Problema | Local | Impacto |
|---|---|---|---|
| **P-01** | Gradiente do login redesenhado pixel por pixel em cada `<Configure>` | `login.py:213-253` | `1080` retângulos criados por frame → freeze em redimensionamento |
| **P-02** | Animação de bolhas com `after(22)` infinito | `login.py:297-328` | CPU ociosa em ~3-4% constante durante tela de login |
| **P-03** | Gráficos canvas redesenhados sem throttle | `dashboard.py:653`, `bem_estar.py:275`, `relatorio.py:314` | Múltiplos binds `<Configure>` sem debounce — possível cascade de redraws |
| **P-04** | `blend_color()` chamada repetidamente em loops de render | `dashboard.py`, `agenda.py` | Função pura Python com conversão hex→rgb→hex; em listas de 500 itens, impacto acumulado |

---

## 6. Plano de Ação Priorizado

### Sprint 1 — Estabilidade (Críticos) — 2-3 dias

1. **E-01**: Substituir `ctk.CTkMessagebox` por `tkinter.messagebox.showerror` ou wrapper customizado compatível com tema.
2. **E-02**: Corrigir duplicação do botão "Política de Privacidade" no login — mover para `_criar_card_login()` e apenas referenciar no `_fazer_login()`.
3. **E-03**: Adicionar validação `if not values: return` em `agenda.py:_campo_combo()`.
4. **E-04**: Remover linhas 386-389 em `estudantes.py` que sobrescrevem os `setattr` corretos.
5. **E-05**: Remover bloco duplicado de chaves `chart_*` em `ui_theme.py` (linhas 133-140).

### Sprint 2 — Consolidação de Design System — 3-4 dias

1. **DS-01**: Criar `theme_extensions.py` ou pattern de "feature tokens" que herdam de `THEME` e sobrescrevem apenas o necessário. Migrar `O`, `Q`, `_LOGIN_PALETTE`, `_CHAT_AVATAR_COLORS` para esse padrão.
2. **DS-02**: Reutilizar `KPICard` de `ui_components.py` em todas as views, parametrizando tamanhos (criar variantes `sm`, `md`, `lg` no componente base).
3. **DS-03**: Unificar helpers `_card()`, `_avatar()`, `_chip()` em `ui_components.py` ou criar `ui_helpers.py` centralizado.
4. **DS-04**: Substituir todos os `ctk.CTkFont("Segoe UI", ...)` por `themed_font()` ou `font()` do `ui_theme.py`.

### Sprint 3 — Acessibilidade e UX — 2-3 dias

1. **AX-01**: Adicionar `text` em todos os botões de ícone-only (ex.: `GhostButton(text="Visualizar", icon="👁")`).
2. **AX-02**: Implementar navegação por teclado em frames clicáveis (`bind("<Return>", ...)` e `bind("<space>", ...)`).
3. **AX-03**: Adicionar `Tooltip` em ícones decorativos (🧠, 🔒, 👁, ✏) para usuários de leitor de tela.
4. **UX-01**: Padronizar header spacing: criar `PAGE_HEADER_HEIGHT` token e usar em todas as views.

### Sprint 4 — Performance — 2-3 dias

1. **PF-01**: Otimizar gradiente do login: pré-renderizar em `PhotoImage` ou reduzir passos para 20-40 retângulos (blocos de 27px em 1080p).
2. **PF-02**: Throttle/Debounce nos binds `<Configure>` de canvas de gráficos (300ms).
3. **PF-03**: Cachear resultados de `blend_color()` em dicionário local se usado em loops grandes.

---

## 7. Riscos Residuais

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Resistência a refatoração de componentes locais | Média | Envolver Tech Lead na decisão de unificar KPICards; manter compatibilidade até Sprint 5 |
| Regressão visual em tema dark após centralizar tokens | Média | Testar todas as 11 views em dark mode antes/deploy |
| Performance de animação do login em hardware legacy | Baixa | Benchmark em máquina com 4GB RAM antes de otimizar |

---

## 8. Próximos Passos Recomendados

1. **Curto prazo (1 semana):** Executar Sprint 1 (críticos) + Sprint 2 itens DS-01/DS-04 (foundation).
2. **Médio prazo (2-3 semanas):** Sprints 2 restantes + Sprint 3 (acessibilidade).
3. **Longo prazo (1 mês):** Sprint 4 (performance) + implementação de testes de UI snapshot (comparar renders antes/depois de mudanças de tema).
4. **Contínuo:** Adotar linting rule customizado para proibir `ctk.CTkFont("Segoe UI", ...)` e garantir que todo estilo passe por `ui_theme.py`.
