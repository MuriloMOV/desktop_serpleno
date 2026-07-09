# Análise Completa - Página de Orientações (SerPleno Web -> Desktop CustomTkinter)

## 1. Visão Geral da Funcionalidade

A página de **Orientações** é um módulo central do SerPleno que permite aos psicólogos criarem, gerenciarem e acompanharem orientações personalizadas para estudantes.

---

## 2. Estrutura de Dados (Modelo Backend)

### 2.1 Modelo `Orientation`
```python
# Campos principais:
- id: int (PK)
- student: ForeignKey -> Student (obrigatório)
- title: str (max 255) - Título da orientação
- theme: str (max 120) - Tema/Categoria (ex: Organização, Ansiedade)
- session_date: date - Data da sessão
- content: text - Conteúdo em Markdown ou Rich Text
- is_markdown: bool - Indica se o conteúdo é Markdown
- motivational_message: text - Mensagem destacada de apoio
- psychologist: ForeignKey -> User (autora da orientação)
- action_plan: JSONField - Lista de tarefas [{'text': str, 'done': bool}]
- created_at: datetime
- updated_at: datetime
```

### 2.2 Modelo `OrientationAttachment`
```python
# Anexos de orientações:
- id: int (PK)
- orientation: ForeignKey -> Orientation
- uploaded_by: ForeignKey -> User
- file: FileField - Arquivo físico
- file_name: str - Nome do arquivo
- mime_type: str - Tipo MIME
- created_at: datetime
```

---

## 3. Endpoints da API (Backend)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/desktop/orientations/` | Lista orientações com filtros e paginação |
| GET | `/api/v1/desktop/orientations/{id}/` | Detalhes de uma orientação específica |
| POST | `/api/v1/desktop/orientations/create/` | Criar nova orientação |
| PUT | `/api/v1/desktop/orientations/{id}/update/` | Atualizar orientação existente |
| DELETE | `/api/v1/desktop/orientations/{id}/delete/` | Deletar orientação |
| POST | `/api/v1/desktop/orientations/{id}/duplicate/` | Duplicar orientação |
| DELETE | `/api/v1/desktop/orientations/attachments/{id}/delete/` | Remover anexo |
| GET | `/api/v1/desktop/orientations/stats/` | Estatísticas de orientações |

### 3.1 Filtros Disponíveis (GET /orientations/)
- `student_id` - Filtra por ID do estudante
- `theme` - Busca por tema (icontains)
- `title` - Busca por título (icontains)
- `psychologist_id` - Filtra por psicólogo
- `date_from` / `date_to` - Filtro por período
- `search` - Busca geral (título, tema ou conteúdo)
- `page` - Paginação

---

## 4. Funcionalidades Identificadas

### 4.1 Funcionalidades Principais

#### A. Seleção de Estudante
- Lista de estudantes com busca/filtro
- Card com avatar (iniciais), nome e curso
- Seleção visual destacada
- Atualização do contexto ao selecionar

#### B. Criação de Nova Orientação
- **Campos do formulário:**
  - Título da Orientação (obrigatório)
  - Data da Sessão (padrão: data atual)
  - Tema/Categoria (ex: Organização, Ansiedade, Rotina)
  - Mensagem Motivacional (destaque)
  - Conteúdo Principal (texto livre)
  - Checkbox "Usar Markdown"

#### C. Modelos Rápidos (Presets)
```python
PRESETS = {
    'study_routine': {
        'label': 'Rotina de Estudo',
        'components': [
            {'id': 'p1', 'type': 'text', 'label': 'Objetivo da Sessão'},
            {'id': 'p2', 'type': 'textarea', 'label': 'Passos/Recomendações'},
            {'id': 'p3', 'type': 'date', 'label': 'Data para Revisão'}
        ]
    },
    'emotional_support': {
        'label': 'Apoio Emocional',
        'components': [
            {'id': 'p4', 'type': 'text', 'label': 'Sintomas/Observações'},
            {'id': 'p5', 'type': 'checkbox', 'label': 'Encaminhar para Atendimento'},
            {'id': 'p6', 'type': 'textarea', 'label': 'Sugestões de Autocuidado'}
        ]
    },
    'follow_up': {
        'label': 'Plano de Acompanhamento',
        'components': [
            {'id': 'p7', 'type': 'text', 'label': 'Meta'},
            {'id': 'p8', 'type': 'date', 'label': 'Prazo'},
            {'id': 'p9', 'type': 'textarea', 'label': 'Responsáveis/Notas'}
        ]
    }
}
```

#### D. Conteúdo Dinâmico
- Adicionar campos customizados:
  - Texto Curto
  - Texto Longo
  - Tarefa/Checkbox
  - Data
- Preview em tempo real
- Remover campos individuais
- Exportar como JSON

#### E. Plano de Ação (Action Plan)
- Lista de tarefas com checkbox
- Cada tarefa: `{'text': str, 'done': bool}`
- Persistido como JSON no backend

#### F. Anexos
- Upload de arquivos (PDF, imagens, documentos)
- Exibição dos arquivos selecionados
- Remoção de anexos

#### G. Histórico de Orientações
- Lista cronológica por estudante
- Card com:
  - Data (círculo com dia)
  - Título
  - Tema
  - Botões: Editar, Apagar
- Estado vazio quando não há orientações

#### H. Edição de Orientação
- Carregar dados existentes no formulário
- Atualizar botão para "Atualizar Orientação"
- Estado de edição controlado

#### I. Exclusão de Orientação
- Confirmação implícita (botão direto)
- Remoção de anexos associados
- Feedback de sucesso/erro

---

## 5. Interface Visual (Layout)

### 5.1 Estrutura da Tela
```
+------------------------------------------------------------------+
|  [Header] Orientações                    [Salvar Orientação]  bell |
+------------------------------------------------------------------+
|  [Banner] Orientações e Acompanhamento                            |
|           Selecione um estudante ao lado para iniciar             |
+------------------------------------------------------------------+
|  +----------------+  +----------------------------------------+  |
|  | Estudantes     |  | [Nova Orientação] [Histórico]          |  |
|  | [Buscar...]    |  +----------------------------------------+  |
|  | +------------+ |  | Título: [________________]             |  |
|  | | JS João S. | |  | Data: [___]  Tema: [______________]    |  |
|  | | Curso X    | |  |                                        |  |
|  | +------------+ |  | Modelos Rápidos: [Rotina] [Apoio] ...  |  |
|  | | MS Maria   | |  |                                        |  |
|  | | Curso Y    | |  | Mensagem Motivacional:                 |  |
|  | +------------+ |  | [________________________________]     |  |
|  | ...            |  |                                        |  |
|  +----------------+  | --- Conteúdo Dinâmico ---               |  |
|                      | [Preview dos campos dinâmicos]          |  |
|                      |                                        |  |
|                      | Tipo: [____] Label: [____] [Adicionar]  |  |
|                      |                                        |  |
|                      | Conteúdo Principal:                    |  |
|                      | [________________________________]     |  |
|                      | [x] Usar Markdown                      |  |
|                      |                                        |  |
|                      | [Anexos - Área Roxa]                   |  |
|                      | [Escolher Arquivos]                    |  |
|                      |                                        |  |
|                      | [Salvar Orientação] [Resetar]          |  |
|                      +----------------------------------------+  |
+------------------------------------------------------------------+
```

### 5.2 Cores e Tema
- **Primário:** Roxo (#7c3aed ou similar)
- **Card:** Branco (#ffffff)
- **Background:** Cinza claro (#f8fafc)
- **Texto:** Escuro (#1e293b)
- **Texto secundário:** Cinza (#64748b)
- **Destaque:** Roxo claro para avatares e badges
- **Bordas:** Cinza claro (#e2e8f0)

---

## 6. Estado da Aplicação

### 6.1 Variáveis de Estado
```python
# Seleção
selected_student: Optional[Dict] = None
selected_student_id: Optional[int] = None

# Tabs
current_tab: str = "new"  # "new" ou "history"

# Formulário
dynamic_components: List[Dict] = []
action_plan: List[Dict] = []

# Edição
editing_orientation_id: Optional[int] = None
is_editing: bool = False

# Dados
_students_list: List[Dict] = []
orientacoes_history: List[Dict] = []
_selected_files: List[str] = []
```

---

## 7. Fluxos de Usuário

### 7.1 Fluxo de Criação
1. Usuário seleciona estudante na lista esquerda
2. Preenche título, data, tema
3. (Opcional) Seleciona modelo rápido
4. (Opcional) Adiciona campos dinâmicos
5. Escreve mensagem motivacional
6. Escreve conteúdo principal
7. (Opcional) Marca "Usar Markdown"
8. (Opcional) Anexa arquivos
9. Clica em "Salvar Orientação"
10. Sistema valida e envia para API
11. Toast de sucesso/erro é exibido
12. Formulário é resetado

### 7.2 Fluxo de Edição
1. Usuário acessa tab "Histórico"
2. Seleciona estudante (se não selecionado)
3. Visualiza lista de orientações
4. Clica em "Editar" em uma orientação
5. Sistema carrega dados no formulário
6. Sistema muda para tab "Nova Orientação"
7. Botão muda para "Atualizar Orientação"
8. Usuário modifica campos desejados
9. Clica em "Atualizar Orientação"
10. Sistema envia atualização para API
11. Toast de sucesso/erro é exibido
12. Formulário é resetado

### 7.3 Fluxo de Exclusão
1. Usuário acessa tab "Histórico"
2. Clica em "Apagar" em uma orientação
3. Sistema envia requisição de exclusão
4. Toast de sucesso/erro é exibido
5. Lista é atualizada

---

## 8. Validações

### 8.1 Frontend
- Estudante deve ser selecionado antes de salvar
- Título é obrigatório (ou gera automaticamente)

### 8.2 Backend
- `student_id`: Obrigatório para criação
- `title`: Obrigatório, máximo 255 caracteres
- `theme`: Máximo 100 caracteres
- `session_date`: Formato YYYY-MM-DD, não pode ser no futuro
- Permissão: Apenas a autora (psychologist) ou staff pode editar/deletar

---

## 9. Melhorias Propostas para CustomTkinter

### 9.1 Funcionalidades Faltantes

1. **Duplicar Orientação**
   - Adicionar botão "Duplicar" no card do histórico
   - Endpoint já existe: `POST /orientations/{id}/duplicate/`

2. **Estatísticas**
   - Adicionar tab "Estatísticas" com gráficos
   - Total de orientações, por tema, por mês

3. **Visualização Detalhada**
   - Modal ou painel expandível para ver orientação completa
   - Atualmente só mostra preview no histórico

4. **Gerenciamento de Anexos**
   - Lista de anexos existentes na edição
   - Preview de arquivos (imagens)
   - Download de anexos

5. **Busca no Histórico**
   - Campo de busca para filtrar orientações
   - Filtros por tema, período

6. **Confirmação de Exclusão**
   - Dialog de confirmação antes de deletar

7. **Indicador de Carregamento**
   - Loading states durante operações assíncronas

### 9.2 Melhorias de UX

1. **Atalhos de Teclado**
   - Ctrl+S para salvar
   - Ctrl+N para nova orientação
   - Escape para cancelar edição

2. **Auto-save**
   - Rascunho automático em localStorage

3. **Toasts Melhorados**
   - Diferentes cores para sucesso/erro/info
   - Fila de notificações
   - Progresso de operações longas

4. **Preview Markdown**
   - Renderização em tempo real do conteúdo Markdown

5. **Drag & Drop**
   - Reordenar campos dinâmicos
   - Arrastar arquivos para anexar

### 9.3 Melhorias Técnicas

1. **Separação de Responsabilidades**
   - Controller para lógica de negócio
   - View para renderização
   - Model para estado

2. **Componentes Reutilizáveis**
   - StudentCard
   - OrientationCard
   - DynamicField
   - Toast

3. **Tratamento de Erros**
   - Retry automático para falhas de rede
   - Mensagens de erro mais descritivas

4. **Testes**
   - Testes unitários para serviços
   - Testes de integração para views

---

## 10. Código de Referência

### 10.1 Estrutura Atual
```
desktop_serpleno/ser_pleno/
+-- views/
|   +-- orientacoes.py (969 linhas) - View principal
+-- services/
|   +-- orientacoes.py (356 linhas) - Serviço de API
+-- docs/
    +-- ANALISE_ORIENTACOES.md - Este documento
```

### 10.2 Dependências
- `customtkinter` - UI framework
- `requests` - HTTP client
- `threading` - Operações assíncronas
- `json` - Serialização
- `datetime` - Manipulação de datas

---

## 11. Análise Comparativa: Desktop Web vs CustomTkinter

### 11.1 Funcionalidades FALTANTES no CustomTkinter

#### A. Tab de Estatísticas (CRÍTICO)
**Web:** Tem uma tab completa com:
- Total de orientações (card com gradiente)
- Gráfico por tema (top 5)
- Gráfico por mês (últimos 6)

**CustomTkinter:** Não implementado

#### B. Filtros no Histórico (CRÍTICO)
**Web:** Possui:
- Campo de busca (título, tema, conteúdo)
- Filtro por data início
- Filtro por data fim
- Botões Filtrar e Limpar
- Contador de resultados

**CustomTkinter:** Não tem filtros, apenas lista simples

#### C. Modal de Visualização Completa (CRÍTICO)
**Web:** Modal com:
- Título, tema, data
- Info do estudante
- Mensagem motivacional em destaque
- Conteúdo completo
- Plano de ação com checkboxes
- Lista de anexos com links
- Botão Editar integrado

**CustomTkinter:** Não tem visualização detalhada

#### D. Duplicar Orientação (IMPORTANTE)
**Web:** Botão "Duplicar" em cada card do histórico
**CustomTkinter:** Não implementado

#### E. Modal de Confirmação de Exclusão (IMPORTANTE)
**Web:** Modal de confirmação antes de excluir
**CustomTkinter:** Exclui diretamente sem confirmação

#### F. Badge do Estudante Selecionado (IMPORTANTE)
**Web:** Badge com avatar, nome, curso e botão para limpar seleção
**CustomTkinter:** Apenas texto no subtítulo

#### G. Gerenciamento de Anexos Existentes (IMPORTANTE)
**Web:** Ao editar:
- Lista de anexos existentes
- Botão remover individual
- Contador de anexos
- Tracking de anexos removidos

**CustomTkinter:** Não gerencia anexos existentes

#### H. Plano de Ação Interativo (IMPORTANTE)
**Web:** 
- Checkboxes editáveis
- Campo de texto editável
- Botão remover tarefa
- Sincronização em tempo real

**CustomTkinter:** Apenas visualização estática

#### I. Contador de Caracteres do Título (MENOR)
**Web:** "X/255 caracteres"
**CustomTkinter:** Não tem

#### J. Botão Limpar Formulário (MENOR)
**Web:** Botão dedicado com ícone de borracha
**CustomTkinter:** Tem "Resetar" mas menos visível

#### K. Botão Salvar Rascunho Local (MENOR)
**Web:** Botão "Rascunho" para salvar localmente
**CustomTkinter:** Não tem

#### L. Sugestões de Tema (MENOR)
**Web:** Datalist com sugestões: Organização, Ansiedade, Gestão do Tempo, etc.
**CustomTkinter:** Não tem

#### M. Tipos de Campo Adicionais (MENOR)
**Web:** Além de texto, textarea, checkbox, data, tem:
- Número
- Seleção (select com opções)

**CustomTkinter:** Apenas 4 tipos

#### N. Toasts com Cores Diferentes (MENOR)
**Web:** success (verde), error (vermelho), warning (âmbar), info (azul)
**CustomTkinter:** Apenas um tipo

#### O. Estado Vazio no Histórico (MENOR)
**Web:** 
- Ícone e mensagem quando não há estudante selecionado
- Ícone e mensagem quando não há orientações
- Orientação para criar primeira orientação

**CustomTkinter:** Mensagem genérica

### 11.2 Resumo de Prioridades

| Prioridade | Funcionalidade | Impacto |
|------------|----------------|---------|
| CRÍTICO | Tab de Estatísticas | Alta |
| CRÍTICO | Filtros no Histórico | Alta |
| CRÍTICO | Modal de Visualização | Alta |
| IMPORTANTE | Duplicar Orientação | Média |
| IMPORTANTE | Confirmação de Exclusão | Média |
| IMPORTANTE | Badge do Estudante | Média |
| IMPORTANTE | Gerenciar Anexos | Média |
| IMPORTANTE | Plano de Ação Interativo | Média |
| MENOR | Contador de caracteres | Baixa |
| MENOR | Botão Limpar | Baixa |
| MENOR | Rascunho Local | Baixa |
| MENOR | Sugestões de Tema | Baixa |
| MENOR | Tipos de Campo Extras | Baixa |
| MENOR | Toasts Coloridos | Baixa |
| MENOR | Estado Vazio Melhorado | Baixa |

---

## 12. Conclusão

A página de Orientações no CustomTkinter possui uma implementação base funcional, mas está **significativamente incompleta** em comparação com o Desktop Web. As principais lacunas são:

1. **Tab de Estatísticas** - Totalmente ausente
2. **Filtros no Histórico** - Ausente, dificulta encontrar orientações
3. **Modal de Visualização** - Ausente, não é possível ver detalhes completos
4. **Duplicar Orientação** - Endpoint existe, UI não implementada
5. **Confirmação de Exclusão** - UX problemática
6. **Gerenciamento de Anexos** - Não funciona na edição
7. **Plano de Ação** - Não é interativo

### Próximos Passos Recomendados

1. Implementar Tab de Estatísticas
2. Adicionar filtros no histórico (busca, data início, data fim)
3. Criar modal de visualização detalhada
4. Implementar botão duplicar
5. Adicionar modal de confirmação antes de excluir
6. Melhorar gerenciamento de anexos na edição
7. Tornar plano de ação interativo