# Alterações na Comunicação Interna - Desktop Ser Pleno

## Descrição das Alterações
Implementação de funcionalidades para garantir que a comunicação interna exiba apenas usuários com permissões admin/staff e que permita conversas em tempo real como chat.

## Arquivos Modificados

### 1. services/comunicacao.py
- **Método `listar_contatos()`**: Melhorou a lógica de atribuição de roles para garantir que apenas usuários com roles `admin`, `analista`, `coordenador` ou `suporte` sejam retornados.
  - Prioridade de roles: admin > coordenador > analista > suporte
  - Filtra contatos para evitar roles não autorizadas
- **Método `enviar_mensagem()`**: Altered signature para receber `id_usuario_logado` como parâmetro (removido hardcode de ID 5)

### 2. views/comunicacao_interna.py
- **Método `carregar_contatos()`**: Adicionou filtro para exibir apenas contatos com roles permitidas
- **Método `get_avatar_por_papel()`**: Ajustado para incluir apenas roles permitidas
- **Método `atualizar_mensagens_periodicamente()`**: Reduzido intervalo de atualização para 2 segundos (feeling real-time)
- **Método `enviar_mensagem()`**: Adicionado feedback visual com botão desabilitado durante envio
- **Método `criar_chat_area()`**: Armazenado referência do botão de enviar como atributo de instância

### 3. test_comunicacao.py
- **Atualizado para nova assinatura do método enviar_mensagem()**: Passando `id_usuario_logado` como primeiro parâmetro

### 4. test_final.py
- **Atualizado para nova assinatura do método enviar_mensagem()**: Passando `id_usuario_logado` como primeiro parâmetro

### 5. setup_groups.py (Novo Arquivo)
- Script para criar e configurar grupos necessários (`Gestores`, `Profissionais`, `Suporte`)
- Adiciona usuários coordenadores aos grupos correspondentes

## Funcionalidades Implementadas

### 1. Exibição de Contatos Apropriados
A lista de contatos now mostra **apenas usuários com roles admin, analista, coordenador ou suporte**.

### 2. Chat em Tempo Real
- **Atualização de mensagens**: A cada 2 segundos
- **Feedback visual**: Botão desabilitado durante envio com texto "Enviando..."
- **Envio rápido**: Mensagens são carregadas imediatamente após envio

### 3. Roles Permitidas
- **admin**: Superusuários do sistema
- **coordenador**: Usuários no grupo "Gestores"
- **analista**: Usuários no grupo "Profissionais" ou com is_staff=True
- **suporte**: Usuários no grupo "Suporte"

## Testes Realizados

### Teste de Integração
1. Conexão com banco de dados: Passou
2. Listagem de contatos: Passou (retorna 5 contatos com roles permitidas)
3. Envio de mensagem: Passou (ID de mensagem 20)
4. Recebimento de mensagem: Passou (3 mensagens no histórico)
5. Atribuição de roles:
   - admin: OK
   - coord.teste: coordenador
   - coord: coordenador
   - analista.teste: analista
   - analista: analista

## Como Verificar as Alterações

### Pré-requisitos
1. Banco de dados MySQL com a base de dados `ser_pleno` configurada
2. Script `setup_groups.py` executado para criar grupos e atribuir usuários

### Execução dos Testes
```bash
cd desktop_serpleno/ser_pleno

# Configurar grupos
python setup_groups.py

# Executar testes básicos
python -m pytest test_comunicacao.py -v

# Executar teste completo de integração
python test_final.py
```

## Observações
- O sistema ainda usa `self.usuario_logado_id = 1` como placeholder para o ID do usuário logado
- A funcionalidade de busca de contatos continua operando com os contatos filtrados
- A thread de atualização de mensagens é iniciada automaticamente ao carregar a tela
