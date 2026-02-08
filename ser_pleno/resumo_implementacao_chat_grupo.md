# Resumo da Implementação do Chat em Grupo para o Sistema de Comunicação Interna

## Descrição do Problema
O sistema de comunicação interna do desktop_serpleno exibia apenas contatos com permissões admin/staff (admin, analista, coordenador e suporte), mas não permitia comunicação com todos os usuários em um único chat de conversa real (chat em grupo).

## Objetivos
1. Permitir que usuários com permissões admin/staff se comuniquem em um único chat de grupo.
2. Exibir o chat em grupo como um contato na lista de conversas.
3. Permitir enviar e receber mensagens no chat em grupo.
4. Exibir o nome dos remetentes nas mensagens de grupo.

## Alterações Realizadas

### Arquivo `services/comunicacao.py`
- Adicionado método `enviar_mensagem_grupo(id_usuario_logado, conteudo)`: Envia mensagens para o chat em grupo.
- Adicionado método `obter_mensagens_grupo()`: Obtém todas as mensagens do chat em grupo.

### Arquivo `views/comunicacao_interna.py`
- Modificado o `__init__`: Inicializa o serviço de comunicação e define o ID do usuário logado (admin - ID 5).
- Modificado `carregar_contatos()`: Carrega contatos com permissões admin/staff e adiciona o chat em grupo "Todos" como primeiro contato.
- Modificado `filtrar_contatos(event)`: Ajustado para filtrar contatos, incluindo o chat em grupo.
- Modificado `selecionar_conversa(contato)`: Atualiza o cabeçalho da conversa para exibir informações do chat em grupo.
- Modificado `carregar_mensagens()`: Carrega mensagens do chat em grupo se a conversa ativa for o grupo.
- Modificado `enviar_mensagem()`: Envia mensagens para o chat em grupo se a conversa ativa for o grupo.
- Modificado `criar_chat_area()`: Cria a área de chat com os atributos `lbl_chat_nome`, `lbl_chat_status`, `entry_mensagem` e `btn_enviar`.
- Adicionado `atualizar_area_mensagens()`: Atualiza a área de mensagens com as mensagens carregadas do chat em grupo.
- Adicionado `criar_mensagem(msg)`: Cria uma mensagem na interface com suporte a exibição do nome do remetente para mensagens de grupo.
- Adicionado `obter_nome_remetente(id_remetente)`: Obtém o nome do remetente com base no ID, verificando na lista de contatos.
- Adicionado `get_avatar_por_papel(papel)`: Retorna o avatar correspondente ao papel do usuário, incluindo avatar para grupo.

### Banco de Dados
- Modificada a coluna `recipient_id` na tabela `desktop_message` para permitir valores NULL, indicando que a mensagem é destinada ao chat em grupo.

### Arquivo `test_chat_grupo.py`
Criado arquivo de teste para verificar a funcionalidade do chat em grupo.

## Funcionalidades Implementadas
1. **Listagem de Contatos**: Exibe apenas usuários com permissões admin, analista, coordenador ou suporte.
2. **Chat em Grupo**: Adiciona um contato "Todos" como chat em grupo.
3. **Envio de Mensagens**: Permite enviar mensagens para o chat em grupo.
4. **Recebimento de Mensagens**: Carrega e exibe mensagens do chat em grupo.
5. **Nome do Remetente**: Exibe o nome do remetente nas mensagens de grupo.
6. **Atualização da Interface**: Ajusta o cabeçalho e a área de mensagens para o chat em grupo.

## Testes
Executado o `test_chat_grupo.py` para verificar a funcionalidade, que mostrou:
- 5 contatos carregados (admin, analista.teste, coord.teste, analista, coord)
- 4 mensagens enviadas com sucesso para o chat em grupo
- Mensagens recebidas corretamente

## Resultado
A funcionalidade de chat em grupo foi implementada com sucesso, permitindo que todos os usuários com permissões admin/staff se comuniquem em uma única conversa. A interface foi ajustada para exibir o nome dos remetentes nas mensagens de grupo e o contato "Todos" é adicionado como primeiro item na lista de contatos.
