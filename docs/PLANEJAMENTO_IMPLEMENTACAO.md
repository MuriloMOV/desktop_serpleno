# Planejamento de Implementação — Desktop CustomTkinter SerPleno

> **Objetivo:** Replicar e adaptar todas as funcionalidades da versão desktop web existente (`serpleno_web/apps/desktop/`) no projeto de desktop CustomTkinter (`desktop_serpleno/`).
> **Data:** 2026-08-13
> **Status:** Em planejamento — execução sequencial por fases.

---

## 1. Contexto e Estado Atual

### 1.1 Projeto de Referência (Web Desktop)
Localizado em `serpleno_web/apps/desktop/`, contém:
- **10 páginas HTML**: Dashboard, Students, Agenda, Screening, Reports, Communication, Guidance, Wellness, Board, Settings
- **90+ endpoints REST** versionados em `/api/v1/desktop/`
- **16 modelos** Django (Student, Appointment, Screening, Report, Orientation, Wellness, Goals, Alerts, Messages, SharedClinicalData, UserProfile/RBAC, etc.)
- **20 services** com lógica de negócio
- **18 controllers** para mediação视图/serviço
- **Templates + Componentes HTML** modulares (base, sidebar, header, 11 componentes, 8 modais)
- **WebSockets** para chat em tempo real
- **Middlewares** customizados (CSRF exemption, etc.)

### 1.2 Estado Atual do Desktop CustomTkinter
Localizado em `desktop_serpleno/src/ser_pleno/`, já possui:
- **Arquitetura Clean Architecture completa**: `application/` → `domain/` → `repositories/` → `infrastructure/`
- **10 telas implementadas**: Dashboard, Estudantes, Agenda, Bem-estar, Análise/Triagem, Relatórios, Comunicação, Orientações, Avisos, Configurações
- **Navegação com sidebar** + cache de views + tema claro/escuro
- **Repositórios** com fallback MySQL → SQLite local (`@with_local_fallback`)
- **Services** completos para: estudantes, agendamentos, orientações, triagens, metas, relatórios, alertas, notificações, pedidos de ajuda, mural, compartilhamento de dados, bem-estar, wellness challenges, analytics
- **Controllers** para mediação explícita
- **API Client** com retry, health check e detecção de disponibilidade
- **WebSocket chat em grupo** implementado
- **Notificador desktop nativo Windows**
- **Modos de operação**: INDEPENDENT, HYBRID, CONNECTED, DB_PRIMARY

### 1.3 Gaps Conhecidos
Documentados em `ANALISE_ORIENTACOES.md` e análise de código:
1. **Orientações**: estatísticas, filtros de histórico, modal de detalhe, duplicar, confirmação de exclusão, gerenciamento de anexos existentes na edição
2. **Funcionalidades específicas por tela** que precisam ser validadas e completadas
3. **Paridade de UX/UI** com a versão web desktop

---

## 2. Estratégia de Implementação

### 2.1 Princípios
- **Reutilização máxima**: services, repositories e controllers existentes serão aproveitados
- **Completude funcional**: cada tela CustomTkinter deve replicar todas as ações disponíveis na versão web
- **Resiliência offline**: manter arquitetura híbrida com fallback MySQL → SQLite
- **UX consistente**: seguir o design system já estabelecido (THEME, componentes reutilizáveis)
- **Modularidade**: novas features entram como módulos independentes sem quebrar o existente

### 2.2 Ordem de Execução
A execução segue ordem de **dependência de dados** + **valor para usuário**:
1. Fase 0: Fundação e completude de serviços/APIs
2. Fase 1: Telas core (Dashboard, Estudantes, Agenda)
3. Fase 2: Telas secundárias (Triagem, Relatórios, Bem-estar)
4. Fase 3: Telas de comunicação (Comunicação, Avisos/Mural)
5. Fase 4: Telas de gestão (Orientações, Metas, Alertas)
6. Fase 5: Integrações avançadas (Analytics, Shared Data, Chat)
7. Fase 6: Polish, testes e paridade final

---

## 3. Backlog Hierárquico por Fase

### Fase 0 — Fundação e Completude de Serviços/APIs

**Objetivo:** Garantir que toda a infraestrutura de dados e serviços esteja completa e espelhando o backend web.

#### Fase 0.1 — Completude de Repositórios
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 0.1.1 | Validar todos os repositories com métodos `@with_local_fallback` | `repositories/*.py` | Todos os métodos CRUD de entidades existem com fallback |
| 0.1.2 | Garantir método `obter_estatisticas()` em orientações | `repositories/orientacoes.py` | Estatísticas por tema e por mês funcionam em ambos modos |
| 0.1.3 | Garantir seed_service completo | `infrastructure/local/seed_service.py` | Rebase incremental MySQL → SQLite para todas as tabelas |
| 0.1.4 | Garantir LocalCache com todas as tabelas | `infrastructure/local/local_cache.py` | 18 tabelas criadas automaticamente |

#### Fase 0.2 — Completude de Services
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 0.2.1 | Completar `ServicoOrientacoes` com estatísticas e anexos | `application/services/orientacoes.py` | Stats, duplicar, anexos funcionam |
| 0.2.2 | Garantir `ServicoMetas` com progresso e estatísticas | `application/services/metas.py` | CRUD + progresso + stats + metas atrasadas |
| 0.2.3 | Garantir `ServicoRelatorio` com todos os formatos de export | `application/services/relatorios.py` | PDF, Excel, CSV, JSON, bulk ops |
| 0.2.4 | Garantir `ServicoBemEstar` com dashboard, mood, checkins | `application/services/bem_estar.py` | Dashboard + entradas + médias + checkins + risco |
| 0.2.5 | Garantir `ServicoComunicacao` com mensagens 1:1 e grupo | `application/services/comunicacao.py` | Alertas, mensagens 1:1, grupo texto/arquivo, contatos |
| 0.2.6 | Garantir `ServicoCompartilhamentoDadosClinicos` completo | `application/services/compartilhamento_dados.py` | Share/unshare, bulk, histórico, relatório |
| 0.2.7 | Garantir `ServicoAnalytics` com todas as queries | `application/services/analytics.py` | Stats dashboard, tendências, performance, busca global, quick actions |
| 0.2.8 | Garantir `ServicoPedidosAjuda` com todas as ações | `application/services/pedidos_ajuda.py` | Listar, visto, iniciar, resolver, responder, pendentes |

#### Fase 0.3 — Completude de Controllers
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 0.3.1 | Validar controllers existentes | `application/controllers/*.py` | Todos os 18 controllers instanciáveis |

---

### Fase 1 — Telas Core (Dashboard, Estudantes, Agenda)

**Objetivo:** Completar as três telas mais críticas com paridade total de funcionalidades.

#### Fase 1.1 — Dashboard
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 1.1.1 | Validar KPIs do dashboard | `presentation/views/dashboard.py`, `application/controllers/dashboard.py` | Todos os KPIs do web desktop exibidos: alunos, atenção, agendamentos hoje, triagens pendentes, alertas não lidos, disponibilidade, média de humor, histórico 30 dias, dimensões bem-estar |
| 1.1.2 | Validar agendamentos do dia | `presentation/views/dashboard.py` | Lista de agendamentos de hoje com status visual |
| 1.1.3 | Validar atendimentos recentes | `presentation/views/dashboard.py` | Histórico recente de atendimentos |
| 1.1.4 | Validar quick actions | `presentation/views/dashboard.py` | Ações rápidas: novo agendamento, nova triagem, enviar mensagem, etc. |
| 1.1.5 | Validar alertas críticos no dashboard | `presentation/views/dashboard.py`, `application/services/alertas.py` | Alertas críticos destacados com contador |

#### Fase 1.2 — Estudantes
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 1.2.1 | Validar CRUD de estudantes | `presentation/views/estudantes.py`, `application/controllers/estudantes.py` | Listar, adicionar, editar, excluir aluno com todos os campos |
| 1.2.2 | Validar filtros (busca, possui_laudo, requer_atencao) | `presentation/views/estudantes.py` | Filtros aplicam corretamente |
| 1.2.3 | Validar bloqueio/desbloqueio de minigames | `presentation/views/estudantes.py` | Ações de bloqueio/unblock com log |
| 1.2.4 | Validar detecção de comportamento suspeito | `presentation/views/estudantes.py` | Check suspicious behavior com alerta |
| 1.2.5 | Validar log de bloqueio de minigames | `presentation/views/estudantes.py` | Visualização de histórico de bloqueios |
| 1.2.6 | Validar campos sensíveis filtrados por role | `presentation/views/estudantes.py` | Campos sensíveis ocultos para roles não autorizadas |

#### Fase 1.3 — Agenda
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 1.3.1 | Validar calendário mensal | `presentation/views/agenda.py` | Navegação por mês, dias com agendamentos destacados |
| 1.3.2 | Validar CRUD de agendamentos | `presentation/views/agenda.py`, `application/controllers/agenda.py` | Adicionar, editar, excluir agendamento |
| 1.3.3 | Validar CRUD de horários disponíveis | `presentation/views/agenda.py` | Gerenciar times com validação de conflito |
| 1.3.4 | Validar listagem de agendamentos do mês | `presentation/views/agenda.py` | `api_list_month_appointments` funcional |
| 1.3.5 | Validar filtros por dia | `presentation/views/agenda.py` | Filtro de agendamentos por data específica |
| 1.3.6 | Validar ação de cancelamento | `presentation/views/agenda.py` | Cancelar agendamento com confirmação |

---

### Fase 2 — Telas Secundárias (Triagem, Relatórios, Bem-estar)

**Objetivo:** Completar as telas de triagem, relatórios e bem-estar com todas as ações.

#### Fase 2.1 — Triagem (Análise)
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 2.1.1 | Validar listagem de triagens | `presentation/views/triagem.py` | Lista com filtros e paginação |
| 2.1.2 | Validar criação de triagem | `presentation/views/triagem.py` | Formulário dinâmico baseado em `ScreeningForm` |
| 2.1.3 | Validar edição de triagem | `presentation/views/triagem.py` | Update com dados JSON |
| 2.1.4 | Validar exclusão de triagem | `presentation/views/triagem.py` | Delete com confirmação |
| 2.1.5 | Validar listagem de formulários de triagem | `presentation/views/triagem.py` | Lista de `ScreeningForm` disponíveis |

#### Fase 2.2 — Relatórios
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 2.2.1 | Validar listagem de relatórios | `presentation/views/relatorio.py` | Lista com filtros e status |
| 2.2.2 | Validar geração de relatório | `presentation/views/relatorio.py` | Geração com template selection |
| 2.2.3 | Validar download PDF | `presentation/views/relatorio.py` | Download PDF estilizado |
| 2.2.4 | Validar download Excel/CSV/JSON | `presentation/views/relatorio.py` | Exportação em múltiplos formatos |
| 2.2.5 | Validar estatísticas de relatórios | `presentation/views/relatorio.py` | Stats e comparison |
| 2.2.6 | Validar CRUD de templates de relatório | `presentation/views/relatorio.py` | Criar, editar, excluir templates |
| 2.2.7 | Validar bulk operations | `presentation/views/relatorio.py` | Bulk delete e bulk download |
| 2.2.8 | Validar visualização de relatório | `presentation/views/relatorio.py` | Modal/view de detalhe do relatório |

#### Fase 2.3 — Bem-estar e Humor
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 2.3.1 | Validar dashboard de bem-estar | `presentation/views/bem_estar.py` | KPIs: média de humor, distribuição, estudantes em risco |
| 2.3.2 | Validar listagem de entradas de humor | `presentation/views/bem_estar.py` | Histórico por estudante com filtros |
| 2.3.3 | Validar criação de entrada de humor | `presentation/views/bem_estar.py` | Formulário de registro |
| 2.3.4 | Validar médias de humor | `presentation/views/bem_estar.py` | Médias por estudante e geral |
| 2.3.5 | Validar check-ins de bem-estar | `presentation/views/bem_estar.py` | Listagem e criação de check-ins |
| 2.3.6 | Validar Wellness Challenges | `presentation/views/bem_estar.py` | CRUD de desafios, atribuir/desatribuir, completar, dashboard |

---

### Fase 3 — Telas de Comunicação (Comunicação, Avisos/Mural)

**Objetivo:** Completar as telas de comunicação interna e mural de avisos.

#### Fase 3.1 — Comunicação
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 3.1.1 | Validar listagem de contatos | `presentation/views/comunicacao.py` | Contatos filtrados por role |
| 3.1.2 | Validar envio de mensagem | `presentation/views/comunicacao.py` | Envio com validação |
| 3.1.3 | Validar histórico de mensagens 1:1 | `presentation/views/comunicacao.py` | Thread de conversa |
| 3.1.4 | Validar mensagens de grupo | `presentation/views/comunicacao.py` | Grupo texto e arquivo |
| 3.1.5 | Validar marcação como lida | `presentation/views/comunicacao.py` | Ação individual e em massa |
| 3.1.6 | Validar exclusão de mensagem | `presentation/views/comunicacao.py` | Delete com confirmação |
| 3.1.7 | Validar contagem de não lidas | `presentation/views/comunicacao.py` | Badge com contador |

#### Fase 3.2 — Avisos (Mural)
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 3.2.1 | Validar listagem de posts do mural | `presentation/views/avisos.py` | Lista com filtros |
| 3.2.2 | Validar criação de post (admin apenas) | `presentation/views/avisos.py` | CRUD com permissão |
| 3.2.3 | Validar edição de post | `presentation/views/avisos.py` | Update com validação |
| 3.2.4 | Validar exclusão de post | `presentation/views/avisos.py` | Delete admin apenas |

---

### Fase 4 — Telas de Gestão (Orientações, Metas, Alertas)

**Objetivo:** Completar as telas de orientações, metas e alertas com paridade total.

#### Fase 4.1 — Orientações
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 4.1.1 | Validar CRUD de orientações | `presentation/views/orientacoes.py` | Listar, criar, editar, excluir |
| 4.1.2 | Validar seletor de tema | `presentation/views/orientacoes.py` | Temas: Geral, Acadêmico, Emocional, Social, Familiar, Vocacional |
| 4.1.3 | Validar templates reutilizáveis | `presentation/views/orientacoes.py` | Lista de templates + usar template |
| 4.1.4 | Validar duplicar orientação | `presentation/views/orientacoes.py` | Duplicar com confirmação |
| 4.1.5 | Implementar estatísticas | `presentation/views/orientacoes.py` | Tab de estatísticas por tema e por mês |
| 4.1.6 | Implementar filtros de histórico | `presentation/views/orientacoes.py` | Filtros por tema, data, aluno |
| 4.1.7 | Implementar modal de detalhe | `presentation/views/orientacoes.py` | Visualização detalhada da orientação |
| 4.1.8 | Implementar confirmação de exclusão | `presentation/views/orientacoes.py` | Modal de confirmação antes de deletar |
| 4.1.9 | Implementar gerenciamento de anexos na edição | `presentation/views/orientacoes.py` | Listar, adicionar, deletar anexos existentes |
| 4.1.10 | Implementar plano de ação interativo | `presentation/views/orientacoes.py` | Plano de ação dinâmico (não apenas estático) |

#### Fase 4.2 — Metas
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 4.2.1 | Implementar CRUD de metas | `presentation/views/metas.py` | Listar, criar, editar, excluir meta |
| 4.2.2 | Implementar registro de progresso | `presentation/views/metas.py` | Registrar progresso com histórico |
| 4.2.3 | Implementar estatísticas de metas | `presentation/views/metas.py` | Stats: total, por status, por prioridade |
| 4.2.4 | Implementar alerta de metas atrasadas | `presentation/views/metas.py` | Destaque para metas vencidas |
| 4.2.5 | Implementar listagem de estudantes por meta | `presentation/views/metas.py` | Filtro de estudantes vinculados |

#### Fase 4.3 — Alertas
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 4.3.1 | Implementar listagem de alertas | `presentation/views/alertas.py` | Lista com filtros por tipo e status |
| 4.3.2 | Implementar alertas críticos | `presentation/views/alertas.py` | Filtro crítico com destaque visual |
| 4.3.3 | Implementar marcar como lido | `presentation/views/alertas.py` | Ação individual e em massa |
| 4.3.4 | Implementar dispensar alerta | `presentation/views/alertas.py` | Ação de dismiss |
| 4.3.5 | Implementar contagem de não lidos | `presentation/views/alertas.py` | Badge com contador |

---

### Fase 5 — Integrações Avançadas (Analytics, Shared Data, Chat, Pedidos de Ajuda)

**Objetivo:** Completar as integrações com SerPleno e funcionalidades avançadas.

#### Fase 5.1 — Analytics
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 5.1.1 | Implementar stats do dashboard | `presentation/views/analytics.py` | Estatísticas agregadas |
| 5.1.2 | Implementar tendências | `presentation/views/analytics.py` | Gráficos de tendência |
| 5.1.3 | Implementar performance | `presentation/views/analytics.py` | Métricas de performance |
| 5.1.4 | Implementar busca global | `presentation/views/analytics.py` | Search unificado |
| 5.1.5 | Implementar quick actions | `presentation/views/analytics.py` | Ações rápidas contextuais |

#### Fase 5.2 — Compartilhamento de Dados Clínicos
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 5.2.1 | Implementar listagem de compartilhamentos | `presentation/views/compartilhamento.py` | Lista com filtros |
| 5.2.2 | Implementar compartilhar dados | `presentation/views/compartilhamento.py` | Modal de seleção de usuário/role |
| 5.2.3 | Implementar descompartilhar | `presentation/views/compartilhamento.py` | Ação de unshare |
| 5.2.4 | Implementar bulk share/unshare | `presentation/views/compartilhamento.py` | Operações em lote |
| 5.2.5 | Implementar histórico de compartilhamento | `presentation/views/compartilhamento.py` | Timeline por estudante |
| 5.2.6 | Implementar relatório de compartilhamento | `presentation/views/compartilhamento.py` | Exportação de relatório |
| 5.2.7 | Implementar estudantes compartilhados | `presentation/views/compartilhamento.py` | Lista de estudantes com acesso compartilhado |
| 5.2.8 | Implementar notificações de compartilhamento | `presentation/views/compartilhamento.py` | Notificações de acesso concedido/revogado |

#### Fase 5.3 — Chat em Tempo Real
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 5.3.1 | Validar conexão WebSocket | `infrastructure/api/websocket_client.py` | Conexão com reconexão exponencial |
| 5.3.2 | Validar interface de chat | `presentation/views/comunicacao.py` | Chat 1:1 e grupo com mensagens em tempo real |
| 5.3.3 | Validar envio de mensagem em tempo real | `presentation/views/comunicacao.py` | Envio sem refresh |
| 5.3.4 | Validar recebimento de mensagem | `presentation/views/comunicacao.py` | Mensagens aparecem automaticamente |
| 5.3.5 | Validar upload de arquivo no chat | `presentation/views/comunicacao.py` | Envio de arquivo no chat de grupo |

#### Fase 5.4 — Pedidos de Ajuda
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 5.4.1 | Implementar listagem de pedidos de ajuda | `presentation/views/pedidos_ajuda.py` | Lista com filtros |
| 5.4.2 | Implementar marcar como visto | `presentation/views/pedidos_ajuda.py` | Ação de visto |
| 5.4.3 | Implementar iniciar atendimento | `presentation/views/pedidos_ajuda.py` | Transição para em atendimento |
| 5.4.4 | Implementar resolver pedido | `presentation/views/pedidos_ajuda.py` | Fechar como resolvido |
| 5.4.5 | Implementar responder pedido | `presentation/views/pedidos_ajuda.py` | Modal de resposta |
| 5.4.6 | Implementar contagem de pendentes | `presentation/views/pedidos_ajuda.py` | Badge de pendentes |

---

### Fase 6 — Polish, Testes e Paridade Final

**Objetivo:** Garantir paridade total, estabilidade e experiência de uso equivalente.

#### Fase 6.1 — Integração SerPleno ↔ Desktop
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 6.1.1 | Validar timeline de humor | Integração SerPleno | Timeline exibida corretamente |
| 6.1.2 | Validar distribuição de bem-estar | Integração SerPleno | Gráficos de distribuição |
| 6.1.3 | Validar overview de risco | Integração SerPleno | Indicadores de risco por estudante |
| 6.1.4 | Validar dados do estudante | Integração SerPleno | Dados agregados do SerPleno |
| 6.1.5 | Validar stats de engajamento | Integração SerPleno | Métricas de engajamento |

#### Fase 6.2 — UX/UI Polish
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 6.2.1 | Revisar consistência visual | Todos os `presentation/views/*.py` | Seguem o THEME e componentes reutilizáveis |
| 6.2.2 | Revisar feedbacks visuais | Todos os `presentation/views/*.py` | Toasts, skeletons, estados de loading |
| 6.2.3 | Revisar acessibilidade | Todos os `presentation/views/*.py` | Navegação por teclado, contraste |
| 6.2.4 | Revisar mensagens de erro | Todos os `presentation/views/*.py` | Mensagens claras em português |

#### Fase 6.3 — Testes e Validação
| # | Tarefa | Arquivo(s) Envolvido(s) | Critério de Aceite |
|---|--------|------------------------|-------------------|
| 6.3.1 | Executar testes existentes | `tests/` | Todos os testes passam |
| 6.3.2 | Smoke test de todas as telas | Todos os `presentation/views/*.py` | Navegação completa sem erros |
| 6.3.3 | Validar modo offline | Arquitetura completa | App funciona sem API |
| 6.3.4 | Validar modo híbrido | Arquitetura completa | Sync MySQL ↔ SQLite funciona |
| 6.3.5 | Validar modo conectado | Arquitetura completa | Todas as APIs consumidas corretamente |

---

## 4. Arquitetura e Padrões

### 4.1 Camadas (Mantidas)
```
presentation/
  ├── views/           # Frames CustomTkinter (UI)
  ├── controllers/     # Mediação视图 → services
  └── components/      # Componentes reutilizáveis

application/
  ├── controllers/     # Controllers de negócio
  └── services/        # Lógica de negócio

domain/
  └── models/          # Dataclasses de domínio

repositories/
  ├── base.py          # Fallback decorators
  └── *.py             # Acesso a dados (MySQL + SQLite)

infrastructure/
  ├── api/             # Cliente HTTP + WebSocket
  └── local/           # SQLite local + cache + seed

ui/
  ├── theme.py         # Design system
  ├── theme_extensions.py
  └── components/      # Componentes visuais

utils/
  └── *.py             # Helpers diversos
```

### 4.2 Padrões de Código
- **ViewFrame**: Toda tela herda de `BaseViewFrame` (ctk.CTkFrame)
- **Controller pattern**: Services instanciados explicitamente nos controllers
- **Fallback decorator**: `@with_local_fallback` para leituras, `write_with_fallback` para escritas
- **AsyncRunner**: Operações de I/O em thread separada para não bloquear UI
- **WidgetBatchBuilder**: Construção otimizada de widgets em lote
- **NotificationCache**: Cache TTL para notificações e alertas
- **Toast**: Feedback visual de ações

### 4.3 Nenhum Comentário no Código
Conforme diretrizes de engenharia, o código deve ser autossuficiente via:
- Nomenclatura semântica de variáveis e funções
- Tipagem forte
- Estrutura de arquivos autoexplicativa
- Documentação externa (este plano, docs/ANALISE_*.md)

---

## 5. Dependências entre Fases

```
Fase 0 (Fundação)
    ↓
Fase 1 (Core: Dashboard, Estudantes, Agenda)
    ↓
Fase 2 (Secundárias: Triagem, Relatórios, Bem-estar)
    ↓
Fase 3 (Comunicação: Comunicação, Avisos)
    ↓
Fase 4 (Gestão: Orientações, Metas, Alertas)
    ↓
Fase 5 (Integrações: Analytics, Shared Data, Chat, Pedidos de Ajuda)
    ↓
Fase 6 (Polish, Testes, Paridade)
```

**Dependências críticas:**
- Fase 0 é bloqueante para todas as outras
- Fase 1 é bloqueante para Fase 2 (dashboard usa dados de estudantes e agenda)
- Fase 3 depende de Fase 1 (comunicação usa dados de estudantes)
- Fase 4 depende de Fase 2 (orientações usam dados de estudantes e triagens)
- Fase 5 depende de Fases 1-4 (analytics agrega dados de todas as telas)
- Fase 6 é dependente de todas as fases anteriores

---

## 6. Critérios de Aceite Globais

1. **Paridade funcional**: Toda ação disponível na versão web desktop está disponível na versão CustomTkinter
2. **Resiliência offline**: App funciona em modo INDEPENDENT com dados locais
3. **Sync bidirecional**: Modo HYBRID sincroniza MySQL ↔ SQLite
4. **UX consistente**: Segue o design system (THEME, componentes, spacing)
5. **Performance**: Navegação entre telas < 300ms
6. **Estabilidade**: Sem crashes em fluxos comuns (CRUD, navegação, sync)
7. **Código limpo**: Sem comentários explicativos, tipagem forte, DRY aplicado

---

## 7. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|--------|---------------|---------|-----------|
| API web desktop indisponível durante desenvolvimento | Alta | Médio | Modo INDEPENDENT com dados seedados localmente |
| Complexidade de sync bidirecional | Média | Alto | Implementar gradualmente com conflict detection |
| Performance com muitas widgets CustomTkinter | Média | Médio | Usar WidgetBatchBuilder + cache de views |
| Divergência de schema entre web e desktop | Baixa | Alto | Manter `sql/ser_pleno.sql` como fonte de verdade |
| Falta de paridade de UX | Média | Médio | Checklist rigoroso por tela + inspeção visual |

---

## 8. Próximos Passos Imediatos

1. Iniciar **Fase 0.1** — validar todos os repositories com métodos `@with_local_fallback`
2. Em paralelo, preparar ambiente com seed de dados para desenvolvimento offline
3. Após Fase 0, iniciar **Fase 1.1** — Dashboard com validação de todos os KPIs
4. Sequenciar Fase 1.2 → Fase 1.3 → Fase 2... até Fase 6

---

*Documento gerado em modo autônomo. Execução sequencial por fases com prioridades claras.*
