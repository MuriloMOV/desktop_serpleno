# Relatório — Vazamento de RAM nos testes de UI (`test_views.py`)

**Data:** 2026-08-19  
**Ambiente:** Windows 32, Python 3.13, CustomTkinter, 12 GB RAM física  
**Sintoma:** `pytest` chega a 10–17 GB de RAM ao rodar `tests/test_views.py` e trava o sistema.

---

## 1. Hipóteses iniciais

1. Fixture `app` criando/descartando `ctk.CTk()` repetidamente sem liberar memória.
2. Vazamento de threads do `AsyncRunner.run`.
3. Widgets CustomTkinter não sendo destruídos entre testes.
4. `WidgetBatchBuilder` criando muitos widgets reais via `after_idle`.
5. `MagicMock` sendo usado como parent de widgets, causando explosão de objetos.
6. Módulos pesados sendo importados no topo de `test_views.py`.

---

## 2. O que já foi testado

### 2.1 CTk puro
- Criar/destruir `ctk.CTk()` e `ctk.CTkFrame()` em loop: **sem vazamento** (~40 MB estáveis).

### 2.2 `MetasFrame` real (fora do pytest)
- Criar `MetasFrame(app, controller)` real e destruir: **sem vazamento** (~63 MB estáveis).

### 2.3 Fixture `app` mínima
- `tests/test_minimo_app.py` com só `assert app is not None`: **sem vazamento** (~0.4s, poucos MB).

### 2.4 Testes `test_views.py` sem os 3 últimos testes
- `test_login_view` até `test_intervencoes_salvar_sem_estudante`: **todos passam sem pico**.

### 2.5 Teste `test_metas_view` isolado
- Rodando **sozinho** via pytest: **chega a 10–17 GB de RAM**.
- Isso descarta acúmulo entre testes: o vazamento é **intrínseco ao teste/fixture no contexto do pytest**.

---

## 3. Alterações já aplicadas

### 3.1 `tests/conftest.py`
- Fixture `app` mudada para `scope="session"` e reutilizada.
- Adicionado `clear_app_widgets` para limpar filhos entre testes.
- Adicionado `mock_async_runner` para evitar threads reais.
- Adicionado `mock_widget_batch_builder` para evitar criação massiva de widgets.

### 3.2 `tests/test_views.py`
- Removidas importações de `MetasFrame`, `RelatorioFrame`, `ReportTemplateFrame` do topo.
- `test_intervencoes_view` e `test_intervencoes_salvar_sem_estudante` agora mockam:
  - `AsyncRunner.run`
  - `WidgetBatchBuilder`
  - `_criar_conteudo`, `_carregar_estudantes`, `_carregar_intervencoes`, `_build_form_lazy`, `_build_filtros_lazy`
- `test_metas_view`, `test_report_template_view`, `test_relatorio_view` agora usam `patch.object(Classe, "__init__", ...)` para evitar construção real de UI.

### 3.3 `src/ser_pleno/ui/views/report_template.py`
- Adicionado import faltante de `SkeletonLoader`.

---

## 4. Diagnóstico parcial

- **Fora do pytest**: criação/destruição de `MetasFrame` real **não vaza**.
- **Dentro do pytest**: `test_metas_view` isolado **vaza absurdamente**.
- Portanto, o vazamento é causado por algo específico do **contexto do pytest**:
  - Possível interferência dos `autouse` fixtures globais.
  - Possível problema no monkeypatch/modificação de `sys.modules`.
  - Possível interação entre `patch.object` e o `WidgetBatchBuilder` global mockado.

---

## 5. O que ainda falta testar

1. **Rodar `test_metas_view` com o `conftest.py` original** (sem mocks globais) para ver se o vazamento some.
2. **Rodar `test_metas_view` sem o fixture `app`**, criando o `ctk.CTk()` manualmente dentro do teste.
3. **Rodar `test_metas_view` sem o `mock_widget_batch_builder`** para ver se esse fixture é o culpado.
4. **Rodar `test_metas_view` sem o `mock_async_runner`** para ver se esse fixture é o culpado.
5. **Rodar `test_metas_view` usando `pytest-xdist`** (`-n 1`) para isolar em subprocesso.
6. **Rodar `test_metas_view` via `runners/run_ui_tests.py`** (subprocess isolado) para confirmar se o isolamento resolve.
7. **Inspecionar se o `MetasFrame.__init__` original, quando executado dentro do pytest, dispara algo além do esperado** (ex.: logging, imports, `after_idle`, `AsyncRunner.run`).
8. **Testar se o problema está no monkeypatch de `sys.modules`** do `mock_widget_batch_builder`.

---

## 6. Próximos passos sugeridos

1. Reverter `conftest.py` para uma versão enxuta e ir reativando fixtures um por um para isolar o culpado.
2. Se o culpado for `mock_widget_batch_builder`, remover a lógica de `sys.modules` e aplicar o mock apenas via monkeypatch padrão.
3. Se o culpado for o `app` fixture com `scope="session"`, voltar para `scope="function"` com destruição explícita.
4. Se nada disso resolver, executar `test_metas_view` via subprocess isolado (`run_ui_tests.py`) como workaround definitivo.

---

## 7. Arquivos modificados

- `desktop_serpleno/tests/conftest.py`
- `desktop_serpleno/tests/test_views.py`
- `desktop_serpleno/src/ser_pleno/ui/views/report_template.py`
- `desktop_serpleno/tests/test_minimo_app.py` (temporário)

---

## 8. Conclusão

O vazamento **não está no `MetasFrame` real**, nem no `ctk.CTk()` puro.  
O vazamento ocorre **apenas dentro do pytest**, no teste `test_metas_view`, indicando que algum fixture global ou mecanismo de mock está interferindo na liberação de memória.  
Os testes restantes (`test_login_view` até `test_intervencoes_salvar_sem_estudante`) **estão estáveis**.  
Para a próxima sessão, recomendo isolar o `conftest.py` ao máximo e reaplicar os mocks gradualmente.
