# Fluxos Incompletos — Desktop SerPleno CustomTkinter

**Data:** 2026-08-17  
**Escopo:** `src/ser_pleno` (apresentação, controllers, services, repositories, infrastructure)  
**Objetivo:** Mapear funcionalidades que não têm entrada de dados, fluxos órfãos backend↔frontend e gaps de navegação.  
**Status:** Documento de acompanhamento — atualizado após análise comparativa com web desktop.

---

## 1. Navegação Mapeada

`src/ser_pleno/ui/navigation.py` define 10 rotas visíveis.  
`src/ser_pleno/ui/view_factory.py` mapeia 19 views:

- `dashboard`
- `estudantes`
- `agenda`
- `bem_estar`
- `analise` → `TriagemFrame`
- `relatorios`
- `comunicacao`
- `orientacoes`
- `avisos`
- `configuracoes`
- `metas`
- `alertas`
- `analytics`
- `audit_logs`
- `compartilhamento`
- `pedidos_ajuda`
- `login`
- `report_template`
- `notificacoes`

---

## 2. Funcionalidades com Backend Exposto, mas sem Fluxo de Entrada na UI

### 2.1 Configurações do sistema sem persistência
- `ConfiguracoesController` expõe:
  - `obter_configuracoes()`
  - `atualizar_configuracoes(dados)`
- `src/ser_pleno/ui/views/configuracoes.py` **não consome esses métodos**.
- A tela funciona em modo local/estático:
  - avatar salvo apenas em `user_profile.json`
  - toggles de tema/fonte alteram `customtkinter` em memória
  - toggles de notificação só registram `logger.info`
- **Efeito:** não há como persistir preferências do sistema nem sincronizá-las com API/backend.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade CRÍTICA

### 2.2 Agenda — modal de grade ainda dependente de sync manual
- `AgendaController` expõe:
  - `adicionar_horario_disponibilidade(horario)`
  - `remover_horario_disponibilidade(horario)`
- `src/ser_pleno/ui/views/agenda.py` abre `GradeManagementModal`, mas `_render_lista()` chama `listar_horarios_base()` de forma bloqueante/síncrona.
- Alterações na grade não recarregam o grid principal automaticamente; o modal depende só de `on_refresh`, o que favorece estados dessincronizados.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade ALTA

### 2.3 Bem-Estar — sem formulário de check-in
- `BemEstarController` expõe `listar_checkins()` e `listar_estudantes_risco()`.
- `bem_estar.py` renderiza lista de check-ins e visão de risco, mas não há botão, modal ou fluxo para “Registrar check-in”.
- Não há ação de follow-up/encaminhamento por estudante em risco diretamente na tela.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade CRÍTICA

### 2.4 Triagem — `listar_formularios()` não consumida pela UI
- `TriagemController.listar_formularios()` existe, mas `triagem.py` não o chama em lugar algum.
- O modal “Nova Triagem” usa campos hardcoded (nome, data, prioridade, status) sem usar formulários pré-cadastrados.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade MÉDIA

### 2.5 Help Requests — ações incompletas
- `PedidosAjudaController` lista pedidos de ajuda, mas não implementa ações de `update` ou `respond`.
- A UI exibe lista mas não permite marcar como visto, iniciar atendimento ou responder.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade ALTA

### 2.6 Notificações nativas — não consumidas
- Desktop expõe view `notificacoes.py`, mas não há controller/serviço associado.
- API de notificações (`/notifications/`) não é consumida.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade ALTO

---

## 3. Ações Expostas no Controller/View, mas sem Dados Confiáveis ou com Fluxo Truncado

### 3.1 Exportações de relatórios sem parametrização
- `RelatorioController` expõe:
  - `exportar_estudantes()`
  - `exportar_agendamentos()`
  - `exportar_triagens()`
- `relatorio.py` botam essas ações como “Exportar CSV” direto, sem:
  - seleção de período
  - filtro adicional
  - confirmação de caminho/destino
- O retorno do service define destino, mas a UI não trata fallback amigável de forma consistente.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade MÉDIA

### 3.2 Envio de mensagem/arquivo sem validação de arquivo
- `ComunicacaoController` expõe:
  - `enviar_mensagem_grupo_arquivo(usuario_id, nome, caminho, categoria)`
  - `enviar_mensagem(usuario_id, destinatario_id, texto)`
- `comunicacao.py` envia arquivos selecionados do disco sem validar:
  - existência antes do payload
  - tamanho
  - tipo realmente suportado pelo backend
- Também há ausência de feedback de envio além do reload imediato de mensagens.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade MÉDIA

### 3.3 Duplicar orientação — botão com handler sem implementação
- `orientacoes.py`: `OrientationHistoryCard` cria botão `Duplicar` com callback `self._on_duplicate(self._o.get("id"))`.
- `OrientacoesFrame._duplicar_orientacao` só executa:
  - `logger.info("Duplicar orientação %s", oid)`
- **Efeito:** usuário vê e clica em ação que não executa nada.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade ALTA

### 3.4 Alterar senha sem reautenticação forte
- `dashboard.py`: modal `_editar_perfil` usa `AutenticacaoController.alterar_senha(senha_atual, nova_senha)`.
- `configuracoes.py`: `_salvar_senha` também usa `alterar_senha`.
- Em ambos os pontos:
  - `senha_atual` é apenas um campo digitado pelo usuário
  - não há etapa adicional de confirmação/reauth forte além do próprio campo
  - validação de identidade é essencialmente front-end
- **Status:** ❌ NÃO RESOLVIDO — Prioridade BAIXA

---

## 4. Telas de Leitura sem Criação/Edição Associada ou com Fluxo Truncado

### 4.1 Quadro de avisos — sem filtros avançados
- `AvisosFrame` lista publicações com CRUD via `PublicacaoModal`.
- Porém:
  - não há filtro por categoria/data
  - não há contador/status bar
  - falhas de carregamento mostram texto solto dentro do scroll, sem container de erro estruturado
- **Status:** ❌ NÃO RESOLVIDO — Prioridade BAIXA

### 4.2 Relatórios — botão de PDF hardcoded
- Exportação “Relatório PDF” usa `self._exportar_pdf`, que chama `gerar_relatorio` com payload fixo:
  - `name`: "Relatório Geral PDF"
  - `report_type`: "geral"
  - `format`: "pdf"
  - `generated_by_id`: 1
- Não há fluxo para o usuário escolher:
  - tipo de relatório
  - período
  - formato preferido
  - destinatário
- **Status:** ❌ NÃO RESOLVIDO — Prioridade MÉDIA

### 4.3 Triagem — campos de data sem validação/normalização
- `_DateField` e os campos de edição usam texto livre `dd/mm/aaaa`.
- Backend/serviço pode esperar ISO (`YYYY-MM-DD` ou datetime); a view não normaliza antes de salvar.
- **Status:** ❌ NÃO RESOLVIDO — Prioridade BAIXA

---

## 5. Inconsistências e Padrões Perigosos

1. `dashboard.py` instancia `DashboardController` duas vezes: uma pelo `view_factory` e outra internamente. Isso pode dessincronizar estado/auth.
   - **Status:** ❌ NÃO RESOLVIDO

2. `estudantes.py` cria `EstudantesController()` internamente em vez de reutilizar a instância injetada.
   - **Status:** ❌ NÃO RESOLVIDO

3. `agenda.py` instancia `AgendamentoRepository()` diretamente e não o usa posteriormente; é código morto local.
   - **Status:** ❌ NÃO RESOLVIDO

4. Várias views leem `usuario_logado_id` do controller injetado, mas controllers como `EstudantesController` e `TriagemController` não armazenam `auth_service`/`usuario_logado`; se services exigirem usuário por request, operações de escrita podem falhar.
   - **Status:** ❌ NÃO RESOLVIDO

5. `bem_estar.py` e `orientacoes.py` usam `extend_theme(...)` no escopo do módulo, criando objetos de tema na importação; alterações dinâmicas em `THEME` após importação podem não se refletir.
   - **Status:** ❌ NÃO RESOLVIDO

---

## 6. Features Completamente Ausentes no Desktop

| Feature | Web View | Desktop Status | Prioridade |
|---------|----------|----------------|------------|
| Wellness Challenges | `views/wellness_challenges.py` | ❌ AUSENTE | CRÍTICO |
| Interventions (dedicada) | `views/interventions.py` | ❌ AUSENTE | CRÍTICO |
| Notifications nativa | `views/notifications.py` | ⚠️ VIEW SEM CONTROLLER | ALTO |
| Orientation Templates | API only | ❌ AUSENTE | MÉDIO |
| Orientation Themes | API only | ❌ AUSENTE | MÉDIO |

---

## 7. Recomendações

1. **Configurações:** ligar `obter_configuracoes`/`atualizar_configuracoes` à UI e persistir alterações via service, eliminando apenas escrita local em JSON.
2. **Bem-Estar:** adicionar modal de “Novo check-in” com seleção de estudante, humor, observação e saving no service.
3. **Orientações:** implementar `_duplicar_orientacao` ou remover o botão da UI para não expor ação morta.
4. **Agenda:** tornar carregamento de grade assíncrono/callback-aware e recarregar automaticamente após add/remove horário.
5. **Relatórios:** criar modal/tela de geração com filtros, ao invés de hardcodar PDF geral.
6. **Triagem:** normalizar dados antes de enviar ao service e usar `listar_formularios()` para modal “Nova Triagem”.
7. **Comunicação:** adicionar validação de arquivo e feedback de envio antes do reload de mensagens.
8. **Controllers instanciados em dobro:** usar sempre a instância injetada pela factory; remover instanciações internas redundantes.
9. **Wellness Challenges:** implementar feature completa com view dedicada.
10. **Interventions:** implementar view dedicada ou expandir tab em estudantes.
11. **Notificações:** implementar controller/serviço e conectar à API nativa.

---

*Documento gerado em 2026-08-17 pelo Consultor Sênior Orientado a Resultados.*
