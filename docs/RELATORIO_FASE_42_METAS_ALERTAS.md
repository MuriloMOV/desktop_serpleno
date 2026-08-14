# Relatório de Validação — Fase 4.2 (Metas) e Fase 4.3 (Alertas)

**Data:** 2026-08-14  
**Projeto:** Desktop CustomTkinter SerPleno  
**Escopo:** Validação e correção das telas de Metas e Alertas  
**Status:** Concluído

---

## Resumo Executivo

Ambas as telas foram validadas contra o planejamento (`docs/PLANEJAMENTO_IMPLEMENTACAO.md`). Foram identificados e corrigidos **7 gaps** (4 em Metas, 3 em Alertas). Nenhum arquivo precisou ser criado do zero — todas as correções foram aplicadas diretamente nos arquivos existentes.

**Paridade com web desktop:**  
- **Metas:** Paridade funcional alcançada. CRUD, progresso, estatísticas, destaque de atraso e filtro por estudante estão implementados.  
- **Alertas:** Paridade funcional alcançada. Listagem com filtros, destaque de críticos, marcação individual/em massa, dismiss e badge de não lidos estão implementados.

---

## Gaps Encontrados e Corrigidos — Metas (Fase 4.2)

| # | Critério | Gap Identificado | Correção Aplicada |
|---|----------|------------------|-------------------|
| 4.2.1 | CRUD de metas | Funcional, sem gaps | — |
| 4.2.2 | Registro de progresso com histórico | Funcional, sem gaps | — |
| 4.2.3 | Estatísticas (total, por status, por prioridade) | KPIs não exibiam contagem por prioridade | Adicionado 5º KPI "Urgentes" (high + urgent) e cálculo em `_atualizar_kpis()` |
| 4.2.4 | Alerta de metas atrasadas | GoalCard não distinguia visualmente metas vencidas | `GoalCard` agora detecta `target_date < hoje` e `status != completed/cancelled`, aplicando: borda vermelha (2px), chip "Atrasada" e barra de progresso em cor de aviso |
| 4.2.5 | Listagem de estudantes por meta | Ausência de filtro dropdown por estudante | Adicionado `f_estudante` (dropdown) em `_criar_filtros()` com carregamento assíncrono via `_carregar_estudantes_filtro()` |
| — | Race condition | `_carregar_estatisticas()` e `_carregar_metas_atrasadas()` atualizavam o KPI de atrasadas de forma assíncrona e concorrente | Removida chamada a `_carregar_metas_atrasadas()` de `load_data()`; contagem de atrasadas agora é unificada via `obter_estatisticas()` |
| — | Código morto | Método `_carregar_metas_atrasadas()` não era mais chamado | Removido método |

### Arquivos modificados — Metas

- `src/ser_pleno/presentation/views/metas.py`

### Detalhes técnicos

**GoalCard (linhas 60–84):**  
```python
is_overdue = (
    target_date
    and status not in ("completed", "cancelled")
    and target_date < _dt.now().strftime("%Y-%m-%d")
)
border_c = THEME["danger"] if is_overdue else THEME["border"]
super().__init__(..., border_width=2 if is_overdue else 1, border_color=border_c)
```

**Filtro por estudante (linhas 309–314, 495–512):**  
Dropdown `f_estudante` carrega lista assíncrona. O mapeamento `name → id` é armazenado em `self._student_ids` e usado em `_aplicar_filtros()`.

**KPI Urgentes (linhas 275–279, 415–418):**  
Contagem agregada de `high` + `urgent` proveniente de `by_priority` retornado por `obter_estatisticas()`.

---

## Gaps Encontrados e Corrigidos — Alertas (Fase 4.3)

| # | Critério | Gap Identificado | Correção Aplicada |
|---|----------|------------------|-------------------|
| 4.3.1 | Listagem de alertas com filtros | Funcional, sem gaps | — |
| 4.3.2 | Alertas críticos com destaque visual | `critical` compartilhava a mesma cor de `error` (THEME["danger"]) sem destaque adicional | Cards de alertas `critical` agora têm: borda lateral 6px (vs 4px) e chip "CRITICO" em vermelho |
| 4.3.3 | Marcar como lido (individual e em massa) | Funcional, sem gaps | — |
| 4.3.4 | Dispensar alerta | Funcional, sem gaps | — |
| 4.3.5 | Contagem de não lidos com badge | Badge não era atualizado na abertura da view; só atualizava após carregar alertas | Adicionado `_inicializar_badge()` chamado no `__init__`, que consulta `contar_nao_lidos()` e atualiza a navegação |
| — | Consistência local | `_local_dispensar_alerta()` não atualizava `resolved_at` no cache SQLite | Corrigido para incluir `resolved_at: "now"` no `local_cache.update()` |
| — | UX da barra de status | Exibia "Mostrando X de X" mesmo sem filtros | `_atualizar_status()` agora exibe apenas a contagem quando filtrados == total |

### Arquivos modificados — Alertas

- `src/ser_pleno/presentation/views/alertas.py`
- `src/ser_pleno/repositories/alertas.py`

### Detalhes técnicos

**Destaque de críticos (linhas 315–344):**  
```python
is_critical = severity == "critical"
border_w = 6 if is_critical else 4
ctk.CTkFrame(body, width=border_w, corner_radius=0, fg_color=cor).pack(...)
if is_critical:
    critico_frame = ctk.CTkFrame(top, fg_color=THEME["danger_soft"], corner_radius=6)
    ctk.CTkLabel(critico_frame, text="CRITICO", ...).pack(...)
```

**Inicialização de badge (linhas 98, 443–456):**  
`_inicializar_badge()` é chamado antes de `carregar_alertas_async()` no `__init__`, garantindo que a navegação exiba a contagem de não lidos imediatamente.

**Repository — resolved_at (linha 149):**  
```python
local_cache.update("alerts", {"is_resolved": 1, "resolved_at": "now"}, "id", alert_id)
```

---

## Validação de Sintaxe

Todos os arquivos modificados foram validados com `py_compile`:

```
src/ser_pleno/presentation/views/metas.py       ✓
src/ser_pleno/presentation/views/alertas.py     ✓
src/ser_pleno/repositories/alertas.py           ✓
```

---

## Confirmação de Paridade

### Metas

| Requisito | Status | Observação |
|-----------|--------|------------|
| Listar metas | ✅ | Com filtros por status, prioridade, categoria, estudante e busca textual |
| Criar meta | ✅ | Modal com todos os campos |
| Editar meta | ✅ | Modal reutiliza `_modal_meta()` |
| Excluir meta | ✅ | Com confirmação |
| Registro de progresso | ✅ | Modal com slider + notas + histórico |
| Estatísticas | ✅ | Total, em andamento, concluídas, atrasadas, urgentes |
| Alerta de metas atrasadas | ✅ | Cartão com borda vermelha, chip "Atrasada" e barra de progresso em aviso |
| Listagem por estudante | ✅ | Dropdown de filtro por estudante |

### Alertas

| Requisito | Status | Observação |
|-----------|--------|------------|
| Listagem com filtros | ✅ | Tipo, severidade, leitura, resolução, data |
| Alertas críticos com destaque | ✅ | Borda 6px + chip "CRITICO" |
| Marcar como lido individual | ✅ | Botão por card |
| Marcar todos como lidos | ✅ | Ação em massa |
| Dispensar alerta | ✅ | Botão por card |
| Contagem de não lidos com badge | ✅ | Inicializada na abertura + atualizada após ações |

---

## Recomendações Futuras

1. **Metas — Animação de overdue:** Considerar pulso sutil na borda vermelha de metas atrasadas para reforçar a urgência.
2. **Alertas — Total não filtrado:** Para exibir "Mostrando X de Y" com precisão, o service `listar_alertas` deveria retornar também a contagem total pré-filtro.
3. **Testes:** Adicionar testes unitários específicos para `MetasFrame` e `AlertasFrame` (atualmente inexistentes).
