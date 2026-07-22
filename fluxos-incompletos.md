# Auditoria de fluxos incompletos — desktop SerPleno

**Data:** 2026-07-22  
**Escopo:** `src/ser_pleno` (apresentação, controllers, services, repositories, infrastructure)  
**Objetivo:** mapear funcionalidades que não têm entrada de dados, fluxos órfãos backend↔frontend e gaps de navegação.

---

## 1. Navegação mapeada

`src/ser_pleno/presentation/navigation.py` define 10 rotas.  
`src/ser_pleno/presentation/view_factory.py` mapeia cada rota para view e controller:

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

Nenhuma rota está morta: todas possuem tela associada.  
Os problemas concentram-se em conexões incompletas entre backend e UI, e em ações expostas sem fluxo de entrada confiável.

---

## 2. Funcionalidades com backend exposto, mas sem fluxo de entrada na UI

### 2.1 Configurações do sistema sem persistência
- `ConfiguracoesController` expõe:
  - `obter_configuracoes()`
  - `atualizar_configuracoes(dados)`
- `src/ser_pleno/presentation/views/configuracoes.py` **não consome esses métodos**.
- A tela funciona em modo local/estático:
  - avatar salvo apenas em `user_profile.json`
  - toggles de tema/fonte alteram `customtkinter` em memória
  - toggles de notificação só registram `logger.info`
- **Efeito:** não há como persistir preferências do sistema nem sincronizá-las com API/backend.

### 2.2 Agenda — modal de grade ainda dependente de sync manual
- `AgendaController` expõe:
  - `adicionar_horario_disponibilidade(horario)`
  - `remover_horario_disponibilidade(horario)`
- `src/ser_pleno/presentation/views/agenda.py` abre `GradeManagementModal`, mas `_render_lista()` chama `listar_horarios_base()` de forma bloqueante/síncrona.
- Alterações na grade não recarregam o grid principal automaticamente; o modal depende só de `on_refresh`, o que favorece estados dessincronizados.

### 2.3 Bem-Estar — sem formulário de check-in
- `BemEstarController` expõe `listar_checkins()` e `listar_estudantes_risco()`.
- `bem_estar.py` renderiza lista de check-ins e visão de risco, mas não há botão, modal ou fluxo para “Registrar check-in”.
- Não há ação de follow-up/encaminhamento por estudante em risco diretamente na tela.

### 2.4 Triagem — `listar_formularios()` não consumida pela UI
- `TriagemController.listar_formularios()` existe, mas `triagem.py` não o chama em lugar algum.
- O modal “Nova Triagem” usa campos hardcoded (nome, data, prioridade, status) sem usar formulários pré-cadastrados.

---

## 3. Ações expostas no controller/view, mas sem dados confiáveis ou com fluxo truncado

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

### 3.2 Envio de mensagem/arquivo sem validação de arquivo
- `ComunicacaoController` expõe:
  - `enviar_mensagem_grupo_arquivo(usuario_id, nome, caminho, categoria)`
  - `enviar_mensagem(usuario_id, destinatario_id, texto)`
- `comunicacao.py` envia arquivos selecionados do disco sem validar:
  - existência antes do payload
  - tamanho
  - tipo realmente suportado pelo backend
- Também há ausência de feedback de envio além do reload imediato de mensagens.

### 3.3 Duplicar orientação — botão com handler sem implementação
- `orientacoes.py`: `OrientationHistoryCard` cria botão `Duplicar` com callback `self._on_duplicate(self._o.get("id"))`.
- `OrientacoesFrame._duplicar_orientacao` só executa:
  - `logger.info("Duplicar orientação %s", oid)`
- **Efeito:** usuário vê e clica em ação que não executa nada.

### 3.4 Alterar senha sem reautenticação forte
- `dashboard.py`: modal `_editar_perfil` usa `AutenticacaoController.alterar_senha(senha_atual, nova_senha)`.
- `configuracoes.py`: `_salvar_senha` também usa `alterar_senha`.
- Em ambos os pontos:
  - `senha_atual` é apenas um campo digitado pelo usuário
  - não há etapa adicional de confirmação/reauth forte além do próprio campo
  - validação de identidade é essencialmente front-end

---

## 4. Telas de leitura sem criação/edição associada ou com fluxo truncado

### 4.1 Quadro de avisos — sem filtros avançados
- `AvisosFrame` lista publicações com CRUD via `PublicacaoModal`.
- Porém:
  - não há filtro por categoria/data
  - não há contador/status bar
  - falhas de carregamento mostram texto solto dentro do scroll, sem container de erro estruturado

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

### 4.3 Triagem — campos de data sem validação/normalização
- `_DateField` e os campos de edição usam texto livre `dd/mm/aaaa`.
- Backend/serviço pode esperar ISO (`YYYY-MM-DD` ou datetime); a view não normaliza antes de salvar.

---

## 5. Inconsistências e padrões perigosos

1. `dashboard.py` instancia `DashboardController` duas vezes: uma pelo `view_factory` e outra internamente. Isso pode dessincronizar estado/auth.
2. `estudantes.py` cria `EstudantesController()` internamente em vez de reutilizar a instância injetada.
3. `agenda.py` instancia `AgendamentoRepository()` diretamente e não o usa posteriormente; é código morto local.
4. Várias views leem `usuario_logado_id` do controller injetado, mas controllers como `EstudantesController` e `TriagemController` não armazenam `auth_service`/`usuario_logado`; se services exigirem usuário por request, operações de escrita podem falhar.
5. `bem_estar.py` e `orientacoes.py` usam `extend_theme(...)` no escopo do módulo, criando objetos de tema na importação; alterações dinâmicas em `THEME` após importação podem não se refletir.

---

## 6. Recomendações

1. **Configurações:** ligar `obter_configuracoes`/`atualizar_configuracoes` à UI e persistir alterações via service, eliminando apenas escrita local em JSON.
2. **Bem-Estar:** adicionar modal de “Novo check-in” com seleção de estudante, humor, observação e saving no service.
3. **Orientações:** implementar `_duplicar_orientacao` ou remover o botão da UI para não expor ação morta.
4. **Agenda:** tornar carregamento de grade assíncrono/callback-aware e recarregar automaticamente após add/remove horário.
5. **Relatórios:** criar modal/tela de geração com filtros, ao invés de hardcodar PDF geral.
6. **Triagem:** normalizar dados antes de enviar ao service e usar `listar_formularios()` para modal “Nova Triagem”.
7. **Comunicação:** adicionar validação de arquivo e feedback de envio antes do reload de mensagens.
8. **Controllers instanciados em dobro:** usar sempre a instância injetada pela factory; remover instanciações internas redundantes.
