# Relatório — Fase 2.3: Bem-Estar e Humor

**Data:** 2026-08-14  
**Projeto:** Desktop CustomTkinter SerPleno  
**Arquivo:** `src/ser_pleno/presentation/views/bem_estar.py`  
**Controller:** `src/ser_pleno/application/controllers/bem_estar.py`  
**Service:** `src/ser_pleno/application/services/bem_estar.py`  
**Repository:** `src/ser_pleno/repositories/bem_estar.py`

---

## 1. Objetivo

Validar e completar a tela de Bem-Estar do Desktop CustomTkinter SerPleno, garantindo paridade funcional com a versão web desktop, conforme Fase 2.3 do planejamento.

---

## 2. Escopo Validado

Conforme `PLANEJAMENTO_IMPLEMENTACAO.md`, Fase 2.3:

| Tarefa | Descrição | Status |
|--------|-----------|--------|
| 2.3.1 | Dashboard de bem-estar com KPIs | ✅ Implementado |
| 2.3.2 | Listagem de entradas de humor por estudante com filtros | ✅ Implementado |
| 2.3.3 | Criação de entrada de humor | ✅ Implementado |
| 2.3.4 | Médias de humor por estudante e geral | ✅ Implementado |
| 2.3.5 | Check-ins de bem-estar (listagem e criação) | ✅ Implementado |
| 2.3.6 | Wellness Challenges: CRUD, atribuir/desatribuir, completar, dashboard | ✅ Implementado |

---

## 3. Gaps Encontrados e Corrigidos

### 3.1 Controller (`application/controllers/bem_estar.py`)

**Gap:** O controller expunha apenas 3 métodos (`obter_dashboard`, `listar_checkins`, `listar_estudantes_risco`). Faltavam métodos para mood entries, check-ins, desafios e listagem de estudantes.

**Correção:** Estendido com os seguintes métodos:

- `listar_entradas_humor(student_id, date_from, date_to, mood_level)`
- `criar_entrada_humor(dados)`
- `obter_medias_humor()`
- `obter_humor_estudante(id_estudante)`
- `obter_historico_humor_estudante(id_estudante)`
- `criar_checkin(dados)`
- `obter_checkin(checkin_id)`
- `listar_desafios()`
- `criar_desafio(dados)`
- `atualizar_desafio(challenge_id, dados)`
- `deletar_desafio(challenge_id)`
- `atribuir_desafio(dados)`
- `desatribuir_desafio(assignment_id)`
- `completar_desafio(assignment_id)`
- `listar_desafios_estudante(student_id)`
- `obter_dashboard_desafios()`
- `listar_estudantes(busca)` — delega para `EstudantesController`

### 3.2 View (`presentation/views/bem_estar.py`)

**Gap:** A view possuía apenas dashboard geral (KPIs, gráfico, distribuição, risco, checkins recentes). Faltavam todas as funcionalidades de visão por estudante, criação de mood entries, CRUD de desafios, check-ins completos, filtros e modais.

**Correção:** Reescrita completamente com as seguintes adições:

#### Funcionalidades adicionadas:

1. **Toolbar superior**
   - Filtro de período (7/30/90 dias) com recarga automática
   - Botão de exportação (stub para exportação)
   - Botão "Registrar Humor" com validação de estudante selecionado

2. **Visão por Estudante** (seção completa)
   - Campo de busca com filtro em tempo real (`<KeyRelease>`)
   - Lista scrollável de estudantes com avatar, nome e curso
   - Seleção de estudante com highlight visual
   - Perfil do estudante selecionado: avatar, nome, curso, mini gráfico de humor
   - Ações rápidas: Registrar Humor, Check-in, Desafio

3. **Abas de detalhe do estudante**
   - **Histórico**: listagem de entradas de humor com emoji, nível, energia/estresse, data
   - **Check-ins**: listagem de check-ins do estudante com tipo, bem-estar, áreas de atenção, recomendações, acompanhamento
   - **Desafios**: listagem de desafios atribuídos com status, XP, categoria, ações de concluir/remover

4. **Modal de Registro de Humor** (`_MoodEntryModal`)
   - Campos: estudante (readonly), data, nível de humor (select 1–5), energia (slider 1–5), estresse (slider 1–5), qualidade do sono (slider 1–5), observações, gatilhos, atividades
   - Integrado com `criar_entrada_humor` do service

5. **Modal de Check-in** (`_CheckinModal`)
   - Campos: estudante (readonly), data, tipo (select: Semanal/Mensal/Pós-Sessão/Crise), bem-estar geral (slider 1–10), áreas de atenção, recomendações, notas do profissional, acompanhamento (switch + data)
   - Integrado com `criar_checkin` do service

6. **Gerenciamento de Wellness Challenges**
   - Modal de formulário (`_ChallengeFormModal`) para criar/editar desafios
   - Campos: título, categoria (select), dificuldade, pontos, ordem, descrição
   - Ações: criar, editar, excluir, atribuir a estudante, completar, desatribuir
   - Dashboard de desafios: total assignments, completados, taxa de conclusão

7. **Componentes reutilizados**
   - `WidgetBatchBuilder` para renderização em lote de listas
   - `AsyncRunner` para operações de I/O não-bloqueantes
   - `Card`, `KPICard`, `Avatar`, `EmptyState`, `GhostButton`, `PrimaryButton`, `DangerButton`, `SearchField`, `Tabs`, `Badge`, `Pill`, `Divider`
   - `mood_emoji_from_score` para emojis de humor
   - `blend_color` para chips de mood

---

## 4. Decisões Técnicas

1. **Layout híbrido**: manteve o dashboard geral existente (KPIs, gráfico, distribuição, risco, checkins recentes) e adicionou a seção de visão por estudante com abas de detalhe. Isso preserva a funcionalidade existente enquanto adiciona a paridade com o web desktop.

2. **Modais como classes separadas**: `_MoodEntryModal`, `_CheckinModal` e `_ChallengeFormModal` seguem o padrão `BaseModal` do projeto, com `transient`, `grab_set` e centralização.

3. **Estado local**: seleção de estudante, período, desafio selecionado e cache de abas gerenciados como atributos da view.

4. **Nomenclatura semântica**: nomes de métodos como `_carregar_historico_estudante`, `_criar_row_checkin_detail`, `_salvar_mood_entry` — sem comentários no código.

5. **Tipagem forte**: uso de `dict | None` (Python 3.10+), dicionários tipados implicitamente via estrutura.

---

## 5. Validação

```bash
python -m py_compile src/ser_pleno/presentation/views/bem_estar.py
python -m py_compile src/ser_pleno/application/controllers/bem_estar.py
```

Ambos os arquivos compilam sem erros de sintaxe.

### Testes existentes

Os 4 testes falhos encontrados (`test_atualizar_senha`, `test_estudantes_view`, `test_triagem_view`, `test_triagem_create`) são **pré-existentes** e não relacionados às mudanças em `bem_estar.py`:
- `test_atualizar_senha` — repositório de autenticação
- `test_estudantes_view` — KeyError `'phone'` em `estudantes.py`
- `test_triagem_view`/`test_triagem_create` — KeyError `'list'` em `triagem.py`

---

## 6. Checklist de Paridade com Web Desktop

| Funcionalidade Web Desktop | Implementação CTk | Observação |
|----------------------------|-------------------|------------|
| Dashboard com KPIs (média, participação, alertas) | ✅ | Mantido da versão anterior |
| Gráfico de tendência 30 dias | ✅ | Mantido, com atualização dinâmica por período |
| Distribuição de humor (bom/neutro/baixo) | ✅ | Mantido |
| Visão de risco (kanban 4 colunas) | ✅ | Mantido |
| Filtro de período (7/30/90 dias) | ✅ | Novo |
| Botão exportar | ✅ | Novo (stub informativo) |
| Seleção de estudante com busca | ✅ | Novo |
| Perfil do estudante (avatar, nome, curso) | ✅ | Novo |
| Mini gráfico de humor por estudante | ✅ | Novo |
| Ações rápidas (Humor, Check-in, Desafio) | ✅ | Novo |
| Histórico de humor por estudante | ✅ | Novo |
| Check-ins por estudante | ✅ | Novo |
| Desafios por estudante (listar, concluir, remover) | ✅ | Novo |
| Modal de criação de humor | ✅ | Novo |
| Modal de check-in | ✅ | Novo |
| CRUD de desafios (criar, editar, excluir) | ✅ | Novo |
| Atribuir/desatribuir desafios | ✅ | Novo |
| Completar desafio | ✅ | Novo |
| Dashboard de desafios | ✅ | Novo |

---

## 7. Próximos Passos Recomendados

1. Conectar o botão "Exportar" ao serviço de exportação quando disponível
2. Implementar drill-down por dimensão (emocional/acadêmico) conforme `applyDrillDown` do web
3. Adicionar gráfico de autoavaliação do estudante (endpoint SerPleno)
4. Adicionar paginação nas listas de histórico e check-ins
5. Integrar com `SerPlenoService` para dados de autoavaliação
