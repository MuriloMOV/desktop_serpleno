# Modo Independente do Desktop SerPleno

## Visão Geral

O Desktop SerPleno agora pode funcionar de forma **plenamente independente** sem precisar que o serpleno_web esteja rodando, mantendo a capacidade de comunicação quando ambos estiverem disponíveis.

## Modos de Operação

### 1. Modo Independente (`independent`)
- Funciona totalmente offline
- Usa apenas o banco de dados local MySQL
- Não tenta conectar ao serpleno_web
- Ideal para uso em ambientes sem conexão com o servidor web

### 2. Modo Híbrido (`hybrid`) - Padrão
- Funciona de forma independente
- Tenta sincronizar com serpleno_web quando disponível
- Mantém fila de operações para sincronização posterior
- Ideal para uso normal do sistema

### 3. Modo Conectado (`connected`)
- Requer conexão com serpleno_web
- Modo legado para compatibilidade
- Fallback para banco local em caso de falha

## Configuração

### Arquivo de Configuração

O arquivo `operation_config.json` (criado automaticamente) contém:

```json
{
    "mode": "hybrid",
    "api_base_url": "http://127.0.0.1:8000",
    "api_timeout": 5,
    "sync_interval": 300,
    "auto_sync": true,
    "last_sync": null,
    "api_available": false
}
```

### Alterando o Modo de Operação

```python
from config.operation_mode import get_operation_config, OperationMode

config = get_operation_config()

# Mudar para modo independente
config.set_mode(OperationMode.INDEPENDENT)

# Mudar para modo híbrido
config.set_mode(OperationMode.HYBRID)

# Verificar modo atual
if config.is_independent():
    print("Sistema em modo independente")
```

## Arquitetura

### Componentes Principais

1. **[`config/operation_mode.py`](config/operation_mode.py)**
   - Gerencia o modo de operação
   - Persiste configurações em arquivo JSON
   - Fornece flags para controle de fluxo

2. **[`services/sync_service.py`](services/sync_service.py)**
   - Serviço de sincronização com serpleno_web
   - Fila de operações pendentes
   - Sincronização em background

3. **Serviços Atualizados**
   - [`services/api.py`](services/api.py) - Cliente API com suporte a modo offline
   - [`services/estudantes.py`](services/estudantes.py) - Prioriza banco local
   - [`services/orientacoes.py`](services/orientacoes.py) - Fallback local completo
   - [`services/autenticacao.py`](services/autenticacao.py) - Login local independente

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop SerPleno                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Views     │───>│  Services   │───>│   MySQL     │     │
│  │  (UI/CTK)   │    │  (Local)    │    │  (Local)    │     │
│  └─────────────┘    └──────┬──────┘    └─────────────┘     │
│                            │                                │
│                            │ (se API disponível)            │
│                            ▼                                │
│                    ┌─────────────┐                          │
│                    │Sync Service │                          │
│                    └──────┬──────┘                          │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                             │ (HTTP/REST)
                             ▼
                    ┌─────────────────┐
                    │   Serpleno Web  │
                    │   (Django API)  │
                    └─────────────────┘
```

## Funcionalidades por Serviço

### Autenticação
- Login local verificando senha no banco MySQL
- Suporte a hashes Django (PBKDF2, bcrypt, argon2)
- Sessão opcional com serpleno_web

### Estudantes
- Listagem, busca e filtros no banco local
- CRUD completo independente
- Sincronização quando disponível

### Agendamentos
- Criação e gerenciamento local
- Verificação de disponibilidade local
- Sincronização bidirecional

### Orientações
- CRUD completo no banco local
- Presets de modelos rápidos
- Anexos armazenados localmente

### Comunicação Interna
- Mensagens entre usuários
- Chat em grupo
- Alertas e notificações

### Bem-Estar
- Registro de humor
- Check-ins de bem-estar
- Estudantes em atenção

## Sincronização

### Fila de Operações

Quando em modo híbrido, operações que falharam ao sincronizar são enfileiradas:

```python
from services.sync_service import get_sync_service, queue_sync

# Adicionar operação à fila
queue_sync('create', 'students', 123, {'name': 'João', ...})

# Verificar status
sync = get_sync_service()
status = sync.get_status()
print(f"Pendentes: {status['pending_items']}")
```

### Sincronização Manual

```python
from services.sync_service import get_sync_service

sync = get_sync_service()
result = sync.sync_now()

print(f"Sincronizados: {result['items_synced']}")
print(f"Pendentes: {result['items_pending']}")
```

### Sincronização Automática

```python
from services.sync_service import get_sync_service

sync = get_sync_service()

# Iniciar sincronização em background
sync.start_background_sync()

# Parar sincronização
sync.stop_background_sync()
```

## Banco de Dados

### Tabelas Principais

O sistema utiliza as seguintes tabelas do banco MySQL:

- `auth_user` - Usuários e autenticação
- `aluno` - Estudantes
- `agendamento` - Agendamentos
- `desktop_orientation` - Orientações
- `desktop_message` - Mensagens
- `desktop_alert` - Alertas
- `desktop_screening` - Triagens
- `desktop_moodentry` - Registros de humor
- `desktop_wellnesscheckin` - Check-ins de bem-estar
- `desktop_intervention` - Intervenções
- `mural_posts` - Quadro de avisos

### Script de Criação

O arquivo [`sql/ser_pleno.sql`](sql/ser_pleno.sql) contém o script completo para criação do banco.

## Migração de Dados

Para migrar dados do serpleno_web para o desktop:

1. Exporte os dados do servidor web:
   ```bash
   python manage.py dumpdata > dados_export.json
   ```

2. Importe no banco do desktop:
   ```bash
   mysql -u root -p ser_pleno < dados_export.json
   ```

## Solução de Problemas

### Erro de Conexão com Banco

Verifique as configurações em [`config/db_config.py`](config/db_config.py):

```python
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'sua_senha',
    'database': 'ser_pleno',
    'port': 3306
}
```

### Sistema Lento

1. Verifique se há muitas operações pendentes na fila
2. Considere mudar para modo independente
3. Limpe a fila de sincronização antiga

### Dados Não Sincronizam

1. Verifique se o serpleno_web está rodando
2. Verifique a URL da API nas configurações
3. Execute sincronização manual para verificar erros

## Logs

Os logs do sistema são registrados via módulo `logging` do Python. Configure o nível de log:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Próximos Passos

1. Implementar sincronização bidirecional completa
2. Adicionar resolução de conflitos
3. Criar interface para configuração de modo
4. Implementar backup automático local
