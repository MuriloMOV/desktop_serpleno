**Objetivo**: Fornecer instruções curtas e práticas para agentes de codificação entenderem rapidamente a arquitetura, convenções e pontos de integração deste projeto GUI Tkinter.

**Visão Geral**:
- **Tipo de app**: Aplicação desktop GUI construída com `customtkinter` (wrapper estilizado sobre Tk/Tkinter).
- **Orquestrador**: `app.py` é o ponto de entrada; cria a janela principal, gerencia autenticação (mock) e navegação entre telas.
- **Views**: Cada tela é um `CTkFrame` em `views/` (ex.: [views/login.py](views/login.py#L1-L200), [views/dashboard.py](views/dashboard.py#L1-L200)).

**Como rodar (dev)**:
- Instale dependências (ex.: `customtkinter`) no ambiente Python.
- Execute: `python app.py` — abre a janela principal e inicia o fluxo de login.

**Padrões e convenções do projeto**:
- **Frames como módulos**: Cada arquivo em `views/` define uma subclasse de `ctk.CTkFrame` que recebe `(parent, controller)` na maioria dos casos. Exemplos:
  - `LoginFrame(parent, controller)` em [views/login.py](views/login.py#L1-L200)
  - `EstudantesFrame(parent, controller)` em [views/estudantes.py](views/estudantes.py#L1-L200)
- **Controlador / App**: O objeto `App` (em [app.py](app.py#L1-L400)) atua como controller — frames chamam métodos do controller (ex.: `controller.iniciar_sistema()`, `controller.trocar_frame(...)`).
- **Navegação**: `app.py` mantém `content` e usa `trocar_frame(FrameClasse)` para trocar telas; para adicionar rota, importar o Frame e adicionar um método `mostrar_<nome>` que chama `trocar_frame`.
- **Layouts**: Mistura de `pack()` e `grid()` — tenha cuidado ao modificar containers que já usam um geometry manager.

**Padrões notáveis / armadilhas**:
- **Assinaturas inconsistentes**: A maioria dos frames usa `(parent, controller)`, mas `AgendaFrame` usa `(parent, app)` e `AnaliseTriagemFrame` usa `(master, controller)`. Quando adicionar/editar frames, siga a assinatura predominante `(parent, controller)` para consistência.
- **Estado e dados**: Não há camada de persistência (DB) visível — dados atuais são _mocked_ direto nas views (listas estáticas em [views/estudantes.py](views/estudantes.py#L1-L200), [views/dashboard.py](views/dashboard.py#L1-L200)). Integrações com APIs/DB devem ser adicionadas centralmente (p.ex., um serviço em `services/`), mantendo as views apenas para renderização e chamadas ao controller.

**Como acrescentar uma nova tela (passo a passo rápido)**:
- Criar `views/nova_tela.py` com `class NovaTelaFrame(ctk.CTkFrame): def __init__(self, parent, controller): ...`.
- Importar em `app.py` e adicionar um botão na `criar_sidebar()` chamando `self.botao_sidebar("Nome", self.mostrar_nova_tela)`.
- Adicionar método `def mostrar_nova_tela(self): self.trocar_frame(NovaTelaFrame)`.

**Estilo e UI**:
- Paleta e tamanhos são definidos diretamente nos frames (cores hex usadas consistentemente). Reutilize os estilos existentes para manter a aparência uniforme.

**Debug / fluxo de desenvolvimento**:
- Uso rápido: execute `python app.py` e interaja com a UI.
- Logs: não há logger configurado; para depurar, adicione `print()` ou configure `logging` no `App`.

**Dependências e integrações**:
- Principal dependência visível: `customtkinter`.
- Nenhuma integração externa (web/API/DB) detectada; procurar por serviços adicionais antes de introduzir chamadas de rede.

**Arquivos chave para referência**:
- [app.py](app.py#L1-L400) — inicialização, navegação, sidebar
- [views/login.py](views/login.py#L1-L200) — fluxo de login e transição para `iniciar_sistema()`
- [views/dashboard.py](views/dashboard.py#L1-L200) — layout de painel e componentes reutilizáveis
- [views/estudantes.py](views/estudantes.py#L1-L200) — padrão lista + detalhes

Se algo aqui estiver incompleto ou você quiser que eu inclua exemplos de alteração (p.ex. adicionar uma tela real com conexão a dados), diga qual área quer que eu detalhe e eu ajusto o arquivo. 

*** Fim das instruções para agentes ***
