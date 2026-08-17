# Plano de Redução de Complexidade — SerPleno Desktop

## Objetivo

Reduzir complexidade desnecessária em ~15-20% sem sacrificar funcionalidade, mantendo a arquitetura offline-first e a camada de UI.

## Escopo

- **Inclui:** Remoção de controllers ceremoniais, remoção de domain models mortos, simplificação do padrão de fallback, refatoração do ViewFactory.
- **Não inclui:** Alterações em repositories, services de negócio, infrastructure API/sync, ou UI components.

## Decisões

### 1. Controllers: manter apenas orquestradores, remover pass-through

**Critério:** Um controller só é mantido se chama **2+ services diferentes** ou tem lógica de orquestração real.

| Controller | Services usados | Decisão |
|------------|-----------------|---------|
| `dashboard.py` | `ServicoDashboard` + `ServicoAnalytics` | **MANTER** |
| `configuracoes.py` | `ServicoConfiguracoes` + `ServicoAutenticacao` | **MANTER** |
| `relatorio.py` | `ServicoRelatorio` + `ServicoReportTemplate` | **MANTER** |
| `autenticacao.py` | 1 service | **REMOVER** |
| `estudantes.py` | 1 service | **REMOVER** |
| `agenda.py` | 1 service | **REMOVER** |
| `bem_estar.py` | 1 service | **REMOVER** |
| `triagem.py` | 1 service | **REMOVER** |
| `comunicacao.py` | 1 service | **REMOVER** |
| `orientacoes.py` | 1 service | **REMOVER** |
| `avisos.py` | 1 service | **REMOVER** |
| `notificacoes.py` | 1 service | **REMOVER** |
| `metas.py` | 1 service | **REMOVER** |
| `alertas.py` | 1 service | **REMOVER** |
| `analytics.py` | 1 service | **REMOVER** |
| `audit_logs.py` | 1 service | **REMOVER** |
| `compartilhamento_dados.py` | 1 service | **REMOVER** |
| `pedidos_ajuda.py` | 1 service | **REMOVER** |
| `report_template.py` | 1 service | **REMOVER** |

**Ação:** Remover 16 arquivos de controller. Views passarão a instanciar services diretamente.

### 2. Domain Models: remover código morto

**Critério:** Remover arquivos que não são importados em nenhum lugar do código fonte.

| Arquivo | Status | Ação |
|---------|--------|-------|
| `domain/models/dashboard.py` | Não importado | **DELETAR** |
| `domain/models/bem_estar.py` | Não importado | **DELETAR** |
| `domain/models/configuracoes.py` | Não importado | **DELETAR** |
| `domain/models/estudantes.py` | Não importado | **DELETAR** |
| `domain/models/__init__.py` | Se ficar vazio | **DELETAR** |
| `domain/models/notificacoes.py` | `map_notification()` é usada em `repositories/notificacoes.py` | **MANTER** |

**Ação:** Deletar 4 arquivos. Manter `notificacoes.py` como utility/mapper.

### 3. Padrão API fallback: criar decorator

Criar `utils/api_fallback.py` com decorator `@api_fallback(fallback_fn_name)` que encapsula o padrão repetitivo.

**Antes:**
```python
def metodo(self, ...):
    def _api_call():
        ...
    return with_api_fallback(_api_call, self._fallback_metodo, ...)
```

**Depois:**
```python
@api_fallback("_fallback_metodo")
def metodo(self, ...):
    ...
```

**Escopo:** Aplicar em todos os services que usam `with_api_fallback`. Estimativa: ~20 métodos em ~8 services.

### 4. ViewFactory: registration por decorator

**Antes:** Dois dicionários hardcoded com 18+ entradas.

**Depois:** Decorator `@register_view("key")` nas classes de view, eliminando os dicionários centrais.

**Ação:** 
- Criar `presentation/registry.py` com `_VIEWS = {}` e `register_view(key)`.
- Aplicar decorator em cada view class.
- ViewFactory consulta o registry ao invés de dicionários internos.

## Passos de Implementação

1. **Deletar domain models mortos** (4 arquivos) — sem impacto em testes.
2. **Remover controllers pass-through** (16 arquivos):
   - Deletar arquivos de controller.
   - Atualizar views para instanciar services diretamente.
   - Atualizar `ViewFactory` para remover mapeamento de controllers.
   - Atualizar testes que mockam controllers removidos.
3. **Criar decorator `@api_fallback`** e aplicar nos services.
4. **Implementar decorator-based view registry** e migrar ViewFactory.

## Validação

- Rodar `pytest -v --tb=short` após cada passo.
- Garantir que `166 testes` continuam passando.
- Verificar que não há imports quebrados com `python -c "import ser_pleno"`.

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Views dependem de métodos específicos de controllers | Verificar imports em cada view antes de remover controller |
| Testes mockam controllers específicos | Atualizar mocks para services correspondentes |
| ViewFactory._controllers não é mais necessário | Remover dicionário e método `_instantiate_controller` |
