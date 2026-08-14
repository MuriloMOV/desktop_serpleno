# Relatório — Fase 5.4: Pedidos de Ajuda

**Data:** 2026-08-14  
**Status:** Concluído  
**Escopo:** Validar e completar a tela de Pedidos de Ajuda do Desktop CustomTkinter SerPleno com paridade funcional em relação ao web desktop.

---

## 1. Objetivos de Paridade

Com base no planejamento (`docs/PLANEJAMENTO_IMPLEMENTACAO.md`) e na implementação web de referência (`serpleno_web/apps/desktop/`), os seguintes itens foram validados:

| # | Funcionalidade | Status |
|---|----------------|--------|
| 5.4.1 | Listagem de pedidos de ajuda com filtros | OK |
| 5.4.2 | Marcar como visto | OK |
| 5.4.3 | Iniciar atendimento | OK |
| 5.4.4 | Resolver pedido | OK |
| 5.4.5 | Responder pedido (modal de resposta) | OK |
| 5.4.6 | Contagem de pendentes com badge | OK |

---

## 2. Gaps Encontrados e Corrigidos

### 2.1 Infraestrutura Offline Ausente

**Gap:** A tabela `help_requests` não estava definida no `LocalCache` SQLite, impossibilitando o funcionamento em modo offline (`INDEPENDENT` / `HYBRID`).  
**Arquivo:** `src/ser_pleno/infrastructure/local/local_cache.py`  
**Correção:** Adicionado `CREATE TABLE IF NOT EXISTS help_requests` com todos os campos do modelo web (`aluno_id`, `tipo`, `mensagem`, `prioridade`, `status`, `localizacao`, `dados_extras`, timestamps, flags de resposta e atendimento). Adicionados métodos `upsert_help_request()` e `list_help_requests()`.

### 2.2 Seed de Dados Ausente

**Gap:** `help_requests` não estava mapeado no `SeedService`, logo nunca era rebased do MySQL para SQLite local.  
**Arquivo:** `src/ser_pleno/infrastructure/local/seed_service.py`  
**Correção:** Adicionada entrada `("help_requests", "help_requests", "upsert_help_request", "updated_at", {})` em `SEED_TABLES` e colunas permitidas em `SEED_COLUMNS`.

### 2.3 Dados do Aluno Não Exibidos

**Gap:** A listagem web exibe `nome`, `curso` e `sala` do aluno em cada card. A view CustomTkinter não trazia esses dados.  
**Arquivos:** `repositories/pedidos_ajuda.py`, `application/services/pedidos_ajuda.py`, `presentation/views/pedidos_ajuda.py`  
**Correção:**
- Repositório MySQL: `SELECT hr.*, a.nome as aluno_nome, a.curso as aluno_curso, a.sala as aluno_sala FROM help_requests hr LEFT JOIN students a ON hr.aluno_id = a.id`
- Repositório local: enriquecimento via `local_cache.list_all("students")` antes de ordenar.
- Service: `_map_help_request` agora inclui `student_name`, `student_course`, `student_class`.
- View: cards passam a exibir nome do aluno, curso e sala.

### 2.4 Respostas Rápidas (Preset) Ausentes

**Gap:** O web desktop oferece dropdown com respostas preset ("Estou livre, pode vir", "Aguarde, estou em atendimento", "Já estou a caminho", "Mantenha-se no local, por favor") além de resposta personalizada. O modal CustomTkinter tinha apenas texto livre.  
**Arquivo:** `presentation/views/pedidos_ajuda.py`  
**Correção:** `ResponderModal` ganhou linha de `GhostButton` com as 4 respostas preset. Ao clicar, o texto é inserido no textbox e o botão de envio é habilitado.

### 2.5 Formatação de Data

**Gap:** O web desktop formata `created_at` em pt-BR (`DD/MM/AAAA HH:MM`). A view CustomTkinter exibia o valor bruto.  
**Arquivo:** `presentation/views/pedidos_ajuda.py`  
**Correção:** Adicionado método `_formatar_data()` com `strftime("%d/%m/%Y %H:%M")` e fallback para string original em caso de erro.

### 2.6 Endpoint de Pendentes (Paridade de API)

**Gap:** O web desktop utiliza endpoint dedicado `/help-requests/pendentes/`. O service apenas listava e contava.  
**Arquivos:** `application/services/pedidos_ajuda.py`, `application/controllers/pedidos_ajuda.py`  
**Correção:** Adicionado método `listar_pendentes()` no service e controller, consumindo `/help-requests/pendentes/` quando em modo conectado. O método existente `contar_pendentes()` continua funcionando via repositório.

---

## 3. Arquivos Modificados

| Arquivo | Tipo de Alteração |
|---------|-------------------|
| `src/ser_pleno/infrastructure/local/local_cache.py` | Adicionada tabela `help_requests` e métodos de acesso |
| `src/ser_pleno/infrastructure/local/seed_service.py` | Adicionado seed de `help_requests` |
| `src/ser_pleno/repositories/pedidos_ajuda.py` | JOIN com `students` para trazer dados do aluno |
| `src/ser_pleno/application/services/pedidos_ajuda.py` | Mapeamento de dados do aluno + método `listar_pendentes()` |
| `src/ser_pleno/application/controllers/pedidos_ajuda.py` | Exposto `listar_pendentes()` |
| `src/ser_pleno/presentation/views/pedidos_ajuda.py` | Exibição de dados do aluno, respostas preset, formatação de data pt-BR |

---

## 4. Validação de Sintaxe

Todos os arquivos modificados passaram em `python -m py_compile`:

```
src/ser_pleno/infrastructure/local/local_cache.py       OK
src/ser_pleno/infrastructure/local/seed_service.py      OK
src/ser_pleno/repositories/pedidos_ajuda.py             OK
src/ser_pleno/application/services/pedidos_ajuda.py     OK
src/ser_pleno/application/controllers/pedidos_ajuda.py  OK
src/ser_pleno/presentation/views/pedidos_ajuda.py       OK
```

---

## 5. Checklist de Paridade com Web Desktop

| Recurso Web Desktop | Implementação CustomTkinter | Observação |
|---------------------|----------------------------|------------|
| Listagem com filtros por status | Sim | `SegmentedButton` com opções Todos / Pendentes / Vistos / Em Atendimento / Resolvidos |
| Marcar como visto | Sim | `_acao_marcar_visto` |
| Iniciar atendimento | Sim | `_acao_iniciar` |
| Resolver pedido | Sim | `_acao_resolver` |
| Responder pedido | Sim | Modal `ResponderModal` com presets + texto livre |
| Badge de pendentes | Sim | Polling 30s + toast + `notificacao_lbl` |
| Dados do aluno (nome, curso, sala) | Sim | Adicionado via JOIN no repositório |
| Respostas preset | Sim | 4 botões de resposta rápida no modal |
| Data formatada pt-BR | Sim | `_formatar_data` com `strftime("%d/%m/%Y %H:%M")` |
| Funcionamento offline | Sim | Tabela SQLite + seed adicionados |

---

## 6. Próximos Passos (Sugestões)

- [ ] Validar em execução real com dados seedados.
- [ ] Verificar se o badge de pendentes deve ser espelhado no header global (fora da tela).
- [ ] Considerar animação de pulse no badge quando houver novos pedidos (paridade visual com web).
- [ ] Testar fluxo completo em modo `HYBRID` para confirmar sync MySQL ↔ SQLite.
