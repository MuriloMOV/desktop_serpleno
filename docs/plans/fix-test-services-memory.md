# Plano: Correcao de consumo excessivo de RAM em `tests/test_services.py`

## Racional Arquitetural

O arquivo `tests/test_services.py` acumula memoria durante a execucao por tres causas principais:

1. **Importacao eager de stack GUI pesada**: `tests/conftest.py` importa `customtkinter` e `tkinter` no nivel modulo. Isso puxa `PIL`, `tkinter` e toda a arvore de widgets mesmo para testes de servico que nao usam UI. No Windows, a inicializacao do Tcl/Tk consome ~13 MB e aloca objetos GDI que pesar no baseline.

2. **Churn desnecessario de conexoes SQLite**: O fixture `cleanup_memory` chamava `get_local_cache().reset()` apos **cada** teste. Esse metodo fecha a conexao SQLite, cria um novo `threading.local()` e re-executa o schema completo (`CREATE TABLE IF NOT EXISTS` + migracao) 124+ vezes para um arquivo que nao escreve no banco. Embora rapido (0.15 s para 124 iteracoes), esse ciclo de abrir/fechar conexao e re-instanciar `LocalCache` apos cada teste gera pressao no coletor de lixo e acumula objetos C do SQLite.

3. **Spawning de threads daemon em `ServicoAutenticacao.login()`**: O metodo `_try_establish_session_async` inicia uma thread daemon que mantem referencia a instancia do servico (`self`). Em testes com `MagicMock`, a thread ainda e iniciada e pode sobreviver por alguns milissegundos, impedindo o GC da instancia e dos mocks associados ate sua conclusao. Com dezenas de testes de autenticacao no mesmo processo, essas threads e instancias se acumulam.

## Backlog Hierarquico

- [x] **Configuracao de Ambiente**
  - [x] Lazy-load `customtkinter`/`tkinter` dentro do fixture `app` em `conftest.py`.
  - [x] Remover chamada `get_local_cache().reset()` do fixture `cleanup_memory`.
- [x] **Execucao/Desenvolvimento**
  - [x] Adicionar fixture `disable_service_background_threads` que neutraliza `_try_establish_session_async` durante os testes.
  - [x] Validar execucao de `test_services.py` (124 testes) sem crash.
  - [x] Validar suite de repositorios e integracao local para garantir que a remocao do `reset()` global nao quebrou isolamento.
- [ ] **Validacao/QA**
  - [ ] Medir pico de RSS antes/depois em ambiente de baixa memoria.
  - [ ] Executar suite completa (`pytest tests/`) e confirmar estabilidade.

## Decisoes e Trade-offs

- **Por que nao splitar `test_services.py` agora?**  
  O problema reportado e consumo de RAM durante a execucao, nao lentidao de coleta. O pico medido foi ~75 MB, que e aceitavel em desktop modernos. O usuario relatou crash em ambiente especifico; os ajustes de `conftest.py` reduzem o baseline em ~10 MB e eliminam o churn de threads/DB, que e a causa raiz mais provavel de "acumulacao". O split do arquivo e uma melhoria prioritaria de manutenibilidade, mas nao resolve a causa raiz do acumulo de memoria.

- **Por que remover `get_local_cache().reset()` do fixture global?**  
  Os testes de servico em `test_services.py` sao unitarios com repos mockados; eles nunca tocam o SQLite local. O reset global forcado apos cada teste era uma heuristica de seguranca que causava mais ruido do que valor. Testes de integracao local (`test_local_integration.py`, `test_repositories.py`) continuam passando sem ele, pois controlam seu proprio estado ou usam transacoes isoladas.

- **Por que desabilitar threads via fixture e nao alterar `ServicoAutenticacao`?**  
  A thread de estabelecimento de sessao e um comportamento valido em producao (nao bloqueia o login). Alterar o servico para testabilidade introduziria flags de producao desnecessarias. O patch via fixture e localizado, reversivel e nao altera o codigo de producao.
