# Implementação do Chat em Grupo para o Sistema de Comunicação Interna

## Descrição da Funcionalidade
Adicionada funcionalidade de chat em grupo para o Sistema de Comunicação Interna do projeto desktop_serpleno. O chat em grupo permite que todos os usuários com permissões admin/staff se comuniquem em uma única conversa.

## Arquivos Modificados

### 1. services/comunicacao.py
- **`enviar_mensagem_grupo(id_usuario_logado, conteudo)`**: Método para enviar mensagens para o chat em grupo.
- **`obter_mensagens_grupo()`**: Método para obter todas as mensagens do chat em grupo.

### 2. views/comunicacao_interna.py
- **`__init__`**: Inicializa o serviço de comunicação e define o ID do usuário logado (admin - ID 5).
- **`carregar_contatos()`**: Carrega contatos com permissões admin/staff e adiciona o chat em grupo "Todos" como primeiro contato.
- **`filtrar_contatos(event)`**: Ajustado para filtrar contatos, incluindo o chat em grupo.
- **`selecionar_conversa(contato)`**: Atualiza o cabeçalho da conversa para exibir informações do chat em grupo.
- **`carregar_mensagens()`**: Carrega mensagens do chat em grupo se a conversa ativa for o grupo.
- **`enviar_mensagem()`**: Envia mensagens para o chat em grupo se a conversa ativa for o grupo.
- **`criar_chat_area()`**: Cria a área de chat com os atributos `lbl_chat_nome`, `lbl_chat_status`, `entry_mensagem` e `btn_enviar`.
- **`atualizar_area_mensagens()`**: Atualiza a área de mensagens com as mensagens carregadas do chat em grupo.
- **`criar_mensagem(msg)`**: Cria uma mensagem na interface com suporte a exibição do nome do remetente para mensagens de grupo.
- **`obter_nome_remetente(id_remetente)`**: Obtém o nome do remetente com base no ID, verificando na lista de contatos.
- **`get_avatar_por_papel(papel)`**: Retorna o avatar correspondente ao papel do usuário, incluindo avatar para grupo.

### 3. teste_chat_grupo.py
Arquivo de teste criado para verificar a funcionalidade do chat em grupo.

## Banco de Dados
- **Alteração na tabela `desktop_message`**: Coluna `recipient_id` modificada para permitir valores NULL.

## Funcionalidades Implementadas
1. **Listagem de Contatos**: Exibe apenas usuários com permissões admin, analista, coordenador ou suporte.
2. **Chat em Grupo**: Adiciona um contato "Todos" como chat em grupo.
3. **Envio de Mensagens**: Permite enviar mensagens para o chat em grupo.
4. **Recebimento de Mensagens**: Carrega e exibe mensagens do chat em grupo.
5. **Nome do Remetente**: Exibe o nome do remetente nas mensagens de grupo.
6. **Atualização da Interface**: Ajusta o cabeçalho e a área de mensagens para o chat em grupo.

## Testes
Executado o teste_chat_grupo.py para verificar a funcionalidade, que mostrou:
- 5 contatos carregados (admin, analista.teste, coord.teste, analista, coord)
- 3 mensagens enviadas com sucesso para o chat em grupo
- Mensagens recebidas corretamente

## Resultado
A funcionalidade de chat em grupo foi implementada com sucesso, permitindo que todos os usuários com permissões admin/staff se comuniquem em uma única conversa. A interface foi ajustada para exibir o nome dos remetentes nas mensagens de grupo e o contato "Todos" é adicionado como primeiro item na lista de contatos.
