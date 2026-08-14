# Relatório Fase 2.1 — Triagem (Análise)

**Data:** 2026-08-14  
**Status:** Concluído  
**Escopo:** Validar e completar a tela de Triagem do Desktop CustomTkinter SerPleno.

---

## 1. Objetivo

Garantir paridade funcional com a versão web desktop (`serpleno_web/apps/desktop/`) para a tela de Triagem, conforme planejamento em `docs/PLANEJAMENTO_IMPLEMENTACAO.md` (Fase 2.1).

---

## 2. Funcionalidades Esperadas (Planejamento)

| # | Funcionalidade | Critério de Aceite |
|---|----------------|-------------------|
| 2.1.1 | Listagem de triagens com filtros | Lista com filtros e paginação |
| 2.1.2 | Criação de triagem | Formulário dinâmico baseado em `ScreeningForm` |
| 2.1.3 | Edição de triagem | Update com dados JSON |
| 2.1.4 | Exclusão de triagem | Delete com confirmação |
| 2.1.5 | Listagem de formulários de triagem | Lista de `ScreeningForm` disponíveis |

---

## 3. Gaps Encontrados e Corrigidos

### 3.1 Criação/Edição sem `student_id` e `form_id`

**Problema:** Os modais de criação e edição enviavam apenas `student_name` (string) ao service, mas o repository e o modelo esperam `student_id` (inteiro) e `form_id`. Isso causaria `KeyError` em `repositories/triagem.py:116` (`dados['student_id']`).

**Correção:** 
- Adicionado `EstudantesController` na view para carregar lista de estudantes.
- Modais agora possuem dropdowns de seleção de estudante e formulário.
- Dados enviados ao service incluem `student_id` e `form_id` corretamente.

### 3.2 Falta de formulário dinâmico (ScreeningForm)

**Problema:** A criação/edição não renderizava as perguntas do formulário selecionado. O web desktop utiliza `ScreeningForm.questions` (JSON) para gerar campos dinamicamente.

**Correção:**
- Adicionado carregamento de `ScreeningForm` via `TriagemController.listar_formularios()`.
- Criado método `renderizar_perguntas` que lê `questions` do formulário e gera widgets conforme tipo (`text`, `textarea`, `select`).
- Respostas são coletadas em dict e serializadas como JSON para o campo `responses`.

### 3.3 Exclusão sem confirmação

**Problema:** Exclusão direta sem confirmação, divergindo do comportamento web e de boas práticas.

**Correção:**
- Adicionado `messagebox.askyesno` antes da exclusão, com mensagem clara em português.

### 3.4 Falta de listagem de formulários

**Problema:** Não havia funcionalidade para visualizar os formulários de triagem disponíveis.

**Correção:**
- Adicionado botão "Formulários" na toolbar.
- Criado modal `_modal_listar_formularios` que lista formulários ativos com nome e descrição.

### 3.5 Filtro de busca textual ausente

**Problema:** O web desktop permite busca por estudante ou formulário (`search_query`). A view CustomTkinter possuía apenas filtros de status e prioridade.

**Correção:**
- Adicionado campo de busca textual no filtro.
- Filtro aplica `busca.lower() in student.lower() or busca.lower() in form_name.lower()`.

### 3.6 KPIs não atualizavam com filtros

**Problema:** Os KPIs eram calculados apenas no `__init__` usando `data_master`. Quando filtros eram aplicados, os cards continuavam mostrando totais gerais.

**Correção:**
- Separada criação dos KPIs (`_criar_kpis`) da atualização (`_atualizar_kpis`).
- `aplicar_filtros` e `limpar_filtros` agora chamam `_atualizar_kpis` com a lista filtrada.

### 3.7 Coluna de formulário ausente na tabela

**Problema:** A tabela não exibia o nome do formulário associado à triagem.

**Correção:**
- Adicionada coluna "Formulário" em `_COL_HEADERS` e `_COL_WEIGHTS`.
- `_criar_row` agora renderiza `form_name` na coluna 1.

### 3.8 Campos de observação não pré-carregados na edição

**Problema:** No modal de edição, o campo de observações não era preenchido com o valor existente.

**Correção:**
- Campo `en_obs` agora insere `item.get("observations")` quando presente.

### 3.9 Falta de carregamento de dados auxiliares

**Problema:** A view não carregava estudantes e formulários, impossibilitando a seleção nos modais.

**Correção:**
- Adicionados métodos assíncronos `_carregar_estudantes` e `_carregar_formularios`.
- Chamados no `__init__` via `AsyncRunner` para não bloquear a UI.

---

## 4. Arquivos Modificados

| Arquivo | Tipo de Mudança |
|---------|-----------------|
| `src/ser_pleno/presentation/views/triagem.py` | Reescrever view com funcionalidades completas |

---

## 5. Detalhes da Implementação

### 5.1 Arquitetura

A view continua seguindo o padrão `ViewFrame` + `Controller` + `AsyncRunner` + `WidgetBatchBuilder`.

### 5.2 Novos Métodos

| Método | Responsabilidade |
|--------|------------------|
| `_carregar_estudantes` | Carrega lista de estudantes via `EstudantesController` |
| `_carregar_formularios` | Carrega lista de `ScreeningForm` via `TriagemController` |
| `_atualizar_kpis` | Atualiza valores dos KPICards com dados filtrados ou completos |
| `renderizar_perguntas` | Renderiza campos dinâmicos baseados em `questions` do formulário |
| `_modal_listar_formularios` | Modal de listagem de formulários disponíveis |

### 5.3 Estrutura de Dados das Perguntas

O formato esperado de `questions` em `ScreeningForm`:

```json
[
  {
    "id": "1",
    "text": "Como você está se sentindo?",
    "type": "select",
    "options": ["Bem", "Regular", "Mal"]
  },
  {
    "id": "2",
    "text": "Descreva sua semana:",
    "type": "textarea"
  }
]
```

Tipos suportados: `text`, `textarea`, `select`.

### 5.4 Fluxo de Criação

1. Usuário clica em "Nova Triagem".
2. Seleciona estudante e formulário.
3. Ao selecionar formulário, as perguntas são renderizadas dinamicamente.
4. Usuário preenche data, prioridade, status, respostas e observações.
5. View envia `student_id`, `form_id`, `responses` (JSON), `priority`, `status`, `scheduled_date`, `observations`.
6. `TriagemController.criar_triagem` → `ServicoTriagem.criar_triagem` → `TriagemRepository.criar`.

---

## 6. Validação

- **Sintaxe:** `python -m py_compile` executado com sucesso.
- **Padrões:** Mantido design system (THEME, componentes reutilizáveis, WidgetBatchBuilder, AsyncRunner).
- **Tipagem:** Mantida tipagem forte e nomenclatura semântica.
- **Sem comentários explicativos:** Código autossuficiente via nomenclatura.

---

## 7. Confirmação de Paridade com Web Desktop

| Funcionalidade Web | Implementação CustomTkinter | Status |
|--------------------|-----------------------------|--------|
| Listagem de triagens | `_carregar_triagens` + `renderizar_tabela` | ✅ |
| Filtros (status, prioridade, busca) | `_criar_filtros` + `aplicar_filtros` | ✅ |
| Criação com formulário dinâmico | `abrir_nova_triagem` + `renderizar_perguntas` | ✅ |
| Edição com dados JSON | `_modal_editar_triagem` + pré-carregamento | ✅ |
| Exclusão com confirmação | `_excluir_triagem` + `askyesno` | ✅ |
| Listagem de formulários | `_modal_listar_formularios` | ✅ |
| KPIs atualizáveis | `_atualizar_kpis` | ✅ |

---

## 8. Próximos Passos

1. Validar integração com modo offline (fallback MySQL → SQLite).
2. Adicionar paginação real (atualmente lista tudo em memória).
3. Implementar máscara de data nos campos `_DateField`.
4. Adicionar validação de datas (inicial <= final).
