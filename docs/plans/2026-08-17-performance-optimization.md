# Plano de Otimizacao de Performance — SerPleno Desktop

**Data:** 2026-08-17  
**Status:** Em execucao  
**Objetivo:** Reduzir `login_flow_ms` de ~14.4s para < 3s e `view_init_*` de ~1.3s para < 400ms.

---

## 1. Racional Arquitetural

A analise dos logs de performance identificou **3 causas-raiz** independentes:

1. **Bloqueio sincrono no login** — `auth_ms=8565.3` domina o `login_flow_ms`. O repositorio de autenticacao usa `with_local_fallback`, que abre conexao MySQL para cada chamada. Quando MySQL tem latencia alta, cada verify de senha gera round-trip duplo.

2. **Widget creation burst nas views** — Views com > 50 widgets sao construidas inteiramente no `__init__` antes de chamar `load_data()`.

3. **Log spam de FK validation em sync_service** — `_check_fk_parents_exist` loga WARNING para IDs locais nao reconciliados (negativos), gerando centenas de linhas por ciclo.

---

## 2. Backlog Hierarquico

### 2.1 Execucao / Desenvolvimento

- [ ] Tarefa A — Login nao-bloqueante e cache-first (alvo: auth_ms < 500ms)
- [ ] Tarefa B — Lazy view init via after_idle (alvo: view_init < 400ms)
- [ ] Tarefa C — Reduzir ruido de sync_service (alvo: < 3 linhas de FK warning/ciclo)
- [ ] Tarefa D — Corrigir seed_service table mapping para screeningforms

### 2.2 Validacao/QA

- [ ] Medir login_flow_ms apos mudancas
- [ ] Medir view_init_* para todas as 10 telas
- [ ] Verificar ausencia de FK warnings repetidos
- [ ] Executar suite de testes: `pytest tests/`

---

## 3. Criterios de Aceite

| Metrica | Antes | Alvo |
|---|---|---|
| login_flow_ms | 14.377s | < 3.0s |
| auth_ms | 8.565s | < 1.0s |
| view_init_estudantes_ms | 1.316s | < 0.4s |
| view_init_relatorio_ms | 1.316s | < 0.4s |
| nav_switch_* (media) | ~900ms | < 300ms |
| Warnings FK pai ausente/ciclo | > 50 linhas | < 3 linhas |
| Seed pos-login duration | ~17s | < 8s |

---

## 4. Riscos Residuais

1. **Cache-first login:** Se SQLite dessincronizar, login pode aceitar credenciais invalidas. Mitigacao: manter fallback MySQL como segunda camada.
2. **Lazy view init:** Widgets dependendo de `winfo_width()` no __init__ podem falhar. Mitigacao: criar apenas containers pais no __init__.
3. **Sync throttle:** Atraso artificial no processamento da fila pode atrasar reconciliacao. Mitigacao: throttle so para logs, nao para processamento.
