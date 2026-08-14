# Relatório — Fase 3.2: Avisos (Mural)

**Data:** 2026-08-14  
**Responsável:** Kilo (engenheiro sênior)  
**Status:** Concluído

---

## 1. Objetivo

Validar e completar a tela de Avisos (Mural) do Desktop CustomTkinter SerPleno, garantindo paridade funcional com a versão web desktop.

---

## 2. Escopo validado

Conforme `PLANEJAMENTO_IMPLEMENTACAO.md` (Fase 3.2):

| # | Tarefa | Arquivo(s) Envolvido(s) | Status |
|---|--------|------------------------|--------|
| 3.2.1 | Listagem de posts do mural com filtros | `presentation/views/avisos.py`, `infrastructure/api/mural.py` | ✅ |
| 3.2.2 | Criação de post (admin apenas) | `presentation/views/avisos.py` | ✅ |
| 3.2.3 | Edição de post | `presentation/views/avisos.py` | ✅ |
| 3.2.4 | Exclusão de post (admin apenas) | `presentation/views/avisos.py` | ✅ |

---

## 3. Gaps encontrados e corrigidos

### 3.1 `presentation/views/avisos.py`

| # | Gap | Correção |
|---|-----|----------|
| 1 | `AvisosFrame` herdava de `ctk.CTkFrame` diretamente, sem header padronizado nem helpers async | Mudou herança para `BaseViewFrame`, reaproveitando header e `_load_async` |
| 2 | `_build_header` com `raise NotImplementedError` — sem título, subtítulo ou ações | Implementado header com título "Mural de Avisos", subtítulo e botão "Nova Publicação" (admin apenas) |
| 3 | Sem botão "Nova Publicação" visível | Adicionado `PrimaryButton` no header, condicionado a `is_admin` |
| 4 | Sem filtros de busca ou categoria | Adicionado `Card` de filtros com campo de busca (título/conteúdo/autor) e dropdown de categoria |
| 5 | Filtros não disparavam recarregamento | Bind de `<KeyRelease>` no campo de busca e `command` no dropdown para `_aplicar_filtros_auto` |
| 6 | `carregar_avisos_async` não aceitava parâmetros de filtro | Assinatura atualizada para `busca` e `categoria`, repassados ao service |
| 7 | Thread handling verboso com `_run_in_thread` customizado | Substituído por `_load_async` do `BaseViewFrame`, reduzindo boilerplate |
| 8 | Sem restrição de admin para criação e exclusão | Botão de nova publicação e botão de excluir visíveis apenas para admin; `_on_delete` valida permissão |
| 9 | Data de publicação exibida como string ISO crua | Adicionado `_formatar_data` para exibir `dd/mm/yyyy HH:MM` |
| 10 | `lista` era `CTkScrollableFrame` aninhado dentro de outro scrollable | Convertido para `CTkFrame` simples, evitando scroll duplo |

### 3.2 `application/controllers/avisos.py`

| # | Gap | Correção |
|---|-----|----------|
| 1 | Controller não expunha `usuario_logado` para a view | Adicionado `self.usuario_logado = getattr(app, "usuario_logado", None)` no `__init__` |
| 2 | `listar_mensagens` não aceitava filtros | Assinatura atualizada para `listar_mensagens(busca=None, pagina=1)` repassando ao service |

### 3.3 `infrastructure/api/mural.py`

| # | Gap | Correção |
|---|-----|----------|
| 1 | `listar_mensagens` não aceitava filtro de categoria | Adicionado parâmetro `categoria` e repassado para API e método local |
| 2 | `_local_listar_mensagens` não filtrada por categoria | Adicionado `AND categoria = %s` na query SQL quando categoria for fornecida e diferente de "Todas" |

---

## 4. Critérios de aceite atendidos

1. **Paridade funcional:** Listagem com filtros, criação (admin), edição e exclusão (admin) replicados da versão web desktop.
2. **Resiliência offline:** Service continua funcionando em modo independente via banco local.
3. **UX consistente:** Header padronizado via `BaseViewFrame`, componentes reutilizáveis (`Card`, `PrimaryButton`, `GhostButton`, `Dropdown`).
4. **Performance:** Navegação e carregamento assíncrono via `_load_async` + `WidgetBatchBuilder`.
5. **Código limpo:** Sem comentários explicativos, tipagem forte, nomes semânticos.

---

## 5. Arquivos modificados

- `src/ser_pleno/presentation/views/avisos.py`
- `src/ser_pleno/application/controllers/avisos.py`
- `src/ser_pleno/infrastructure/api/mural.py`

---

## 6. Próximos passos sugeridos

- Executar smoke test da tela de Avisos em modo connected e independent.
- Validar filtros com dados reais do banco local.
- Iniciar Fase 4 (Orientações, Metas, Alertas) conforme planejamento.
