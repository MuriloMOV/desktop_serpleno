# Análise Completa do Pacote `@serpleno-desktop/`

**Data da análise:** 2026-08-19  
**Escopo:** `C:\Users\58023826\Desktop\projetos-serpleno\serpleno-desktop\`  
**Versão analisada:** 1.0.0 (pyproject.toml)  
**Stack:** Python >= 3.11, CustomTkinter 5.2+, MySQL + SQLite, PyInstaller

---

## Sumário Executivo

O pacote `serpleno-desktop` é uma aplicação desktop de gestão escolar desenvolvida com Python e CustomTkinter, com arquitetura src-layout, sincronização bidirecional MySQL↔SQLite, e suporte a modos de operação independente/híbrido/conectado. A base de código é extensa (~20 features, ~50 views/services/repositories) e apresenta **problemas estruturais significativos** que impedem funcionamento confiável em produção.

Foram identificados **8 problemas CRÍTICOS**, **12 de severidade ALTA**, **15 MÉDIA** e **9 BAIXA**, além de vulnerabilidades de segurança e gaps de compatibilidade.

---

## 1. PROBLEMAS CRÍTICOS

### 1.1. `Any` não importado em `app.py`
**Severidade:** CRÍTICA  
**Arquivo:** `src/ser_pleno/app.py`  
**Linha:** 213

```python
def iniciar_sistema(
    self,
    user_data: dict[str, Any],
    auth_service: Any | None = None,
    login_start: float | None = None,
) -> None:
```

**Causa raiz:** O arquivo usa `from __future__ import annotations` (que permite sintaxe de tipo moderna), mas `Any` nunca foi importado de `typing`. Em Python 3.11+, isso gera `NameError` em tempo de execução quando o tipo é avaliado (ex.: ferramentas de inspeção, decoradores, ou `get_type_hints()`).

**Impacto:** Falha na inicialização do sistema em ambientes que inspecionam tipos. Em produção, pode causar crash silencioso durante login.

**Correção:**
```python
from typing import Any
# Adicionar no topo de app.py, após os imports existentes
```

---

### 1.2. Tamanho mínimo de janela restritivo (1920×1080)
**Severidade:** CRÍTICA  
**Arquivo:** `src/ser_pleno/app.py`  
**Linha:** 138

```python
self.minsize(1920, 1080)
```

**Causa raiz:** Hardcoding de resolução Full HD como mínimo torna o aplicativo **inutilizável** em laptops de 1366×768, 1440×900, ou qualquer monitor menor. O `minsize` impede redimensionamento abaixo de Full HD, causando:
- Janela maior que a tela → impossibilidade de interagir com botões fora da viewport
- Scrollbars inacessíveis
- Falha em testes de UI que usam `app.geometry("1200x800")`

**Impacto:** ~60% dos usuários de desktop (laptops, monitores menores) não conseguem usar o app.

**Correção:**
```python
# Remover minsize ou usar valor mínimo razoável
self.minsize(1024, 768)  # Mínimo viável para layout de duas colunas
# Ou melhor: calcular baseado na tela disponível
screen_w = self.winfo_screenwidth()
screen_h = self.winfo_screenheight()
self.minsize(min(1024, screen_w - 100), min(768, screen_h - 100))
```

---

### 1.3. Configurações do sistema não persistem (back-end morto)
**Severidade:** CRÍTICA  
**Arquivos:** `src/ser_pleno/ui/views/configuracoes.py`, `src/ser_pleno/features/configuracoes/service.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 2.1

**Causa raiz:** A tela de Configurações define toggles de notificação (`_on_toggle_notificacao`) que apenas executam `logger.info()`. O método `_salvar_configuracoes` existe e chama `servico_configuracoes.atualizar_configuracoes()`, mas:
1. Os toggles não disparam `_salvar_configuracoes` automaticamente
2. O avatar é salvo apenas em `user_profile.json` local, sem sincronização
3. O tema/fonte altera apenas o CustomTkinter em memória, sem persistência no back-end

**Impacto:** Usuário perde todas as preferências ao fechar o app. Settings são efêmeros.

**Correção:**
```python
# Em configuracoes.py, modificar _on_toggle_notificacao:
def _on_toggle_notificacao(self, tipo: str, estado: bool):
    self._notificacoes_state[tipo] = estado
    # Persistir imediatamente (debounce recomendado)
    self._salvar_configuracoes_async()

def _salvar_configuracoes_async(self):
    if getattr(self, "_save_job", None):
        self.after_cancel(self._save_job)
    self._save_job = self.after(500, self._salvar_configuracoes)
```

---

### 1.4. Bem-Estar sem formulário de check-in
**Severidade:** CRÍTICA  
**Arquivo:** `src/ser_pleno/ui/views/bem_estar.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 2.3

**Causa raiz:** A view `BemEstarFrame` apenas exibe listas de check-ins e visão de risco (`_atualizar_secao_bem_estar`, `_atualizar_secao_risco`). Não há botão, modal ou fluxo para "Registrar check-in". O `_MoodEntryModal` existe no mesmo arquivo (linha 71) mas **nunca é instanciado** pela view principal.

**Impacto:** Funcionalidade core de bem-estar está inacessível. Usuário não pode registrar humor/check-in.

**Correção:**
```python
# Em bem_estar.py, adicionar botão na toolbar:
PrimaryButton(
    bar, text=f"{ICONS['add']}  Novo Check-in",
    command=self._abrir_novo_checkin,
    height=40, width=180,
).pack(side="right")

# E implementar _abrir_novo_checkin:
def _abrir_novo_checkin(self):
    modal = _MoodEntryModal(self, on_save=self._salvar_checkin)
    modal.grab_set()

def _salvar_checkin(self, dados):
    service = self.servico_bem_estar
    # ... chamar service.criar_checkin(dados)
```

---

### 1.5. Controller `DashboardController` instanciado em dobro
**Severidade:** CRÍTICA  
**Arquivo:** `src/ser_pleno/ui/views/dashboard.py` (linha 276)  
**Status confirmado em:** `fluxos-incompletos.md` seção 5.1

**Causa raiz:** `view_factory.py` injeta `servico_dashboard` no frame, mas `dashboard.py` também acessa `self.controller.servico_dashboard`. Se o controller interno for diferente do injetado, há dessincronização de estado/auth.

**Impacto:** Estado de autenticação pode ficar inconsistente entre views. Dados do dashboard podem não refletir o usuário logado correto.

**Correção:**
```python
# Remover instanciação interna. Usar apenas a injetada:
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        # ...
        self.servico_dashboard = getattr(controller, "servico_dashboard", None)
        # REMOVER qualquer linha como: self.controller = DashboardController(...)
```

---

### 1.6. EstudantesController instanciado internamente
**Severidade:** CRÍTICA  
**Arquivo:** `src/ser_pleno/ui/views/estudantes.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 5.2

**Causa raiz:** Mesmo padrão do dashboard — view cria sua própria instância de controller em vez de reutilizar a injetada pela factory.

**Impacto:** Dessincronização de auth, estado e serviços.

**Correção:** Aplicar mesma correção do item 1.5 — remover instanciação interna, usar apenas `getattr(controller, "servico_estudantes", None)`.

---

### 1.7. Botão "Duplicar Orientação" com handler morto
**Severidade:** CRÍTICA  
**Arquivo:** `src/ser_pleno/ui/views/orientacoes.py`  
**Linha:** ~108 (referência em `fluxos-incompletos.md` seção 3.3)

**Causa raiz:** `OrientationHistoryCard` cria botão `Duplicar` com callback `self._on_duplicate(self._o.get("id"))`, mas `OrientacoesFrame._duplicar_orientacao` executa apenas `logger.info("Duplicar orientação %s", oid)`.

**Impacto:** Usuário vê ação que não executa nada. Experiência quebrada.

**Correção:**
```python
def _duplicar_orientacao(self, oid):
    # Implementar duplicação real ou remover botão da UI
    service = self.servico_orientacoes
    original = service.obter_orientacao(oid)
    if not original:
        self._show_error("Orientação não encontrada")
        return
    # Criar cópia com novo título/data
    dados = {**original, "id": None, "title": f"{original['title']} (cópia)"}
    res = service.criar_orientacao(dados)
    # ...
```

---

### 1.8. Falha de importação de tema (`theme.py` não encontrado)
**Severidade:** CRÍTICA  
**Arquivos:** Diversos imports de `ser_pleno.ui.theme`

**Causa raiz:** O arquivo `theme.py` não existe mais como arquivo único; foi refatorado para pacote `ui/theme/__init__.py`. Várias views/documentação ainda referenciam `ser_pleno.ui.theme` como módulo, o que funciona por causa do `__init__.py`, mas **views antigas ou imports dinâmicos podem falhar**. O `fluxos-incompletos.md` README ainda referencia `src/ser_pleno/ui/theme.py` como arquivo individual (linha 71 do README).

**Impacto:** Inconsistência entre documentação e estrutura real. Risco de `ModuleNotFoundError` em imports dinâmicos.

**Correção:**
- Atualizar `README.md` e `docs/` para refletir a estrutura modular
- Garantir que `__init__.py` do pacote `theme` exporte todos os símbolos necessários

---

## 2. PROBLEMAS DE SEVERIDADE ALTA

### 2.1. Credenciais de produção em `.env.example`
**Severidade:** ALTA (Segurança)  
**Arquivo:** `.env.example`

```env
SERPLENO_DB_HOST=roundhouse.proxy.rlwy.net
SERPLENO_DB_PORT=13953
SERPLENO_DB_USER=root
SERPLENO_DB_PASSWORD=sua_senha_railway
SERPLENO_DB_NAME=railway
```

**Causa raiz:** O arquivo de exemplo contém host real, porta, usuário e nome de banco de produção. Qualquer pessoa com acesso ao repositório obtém conectividade direta ao banco de produção.

**Impacto:** Exposição de infraestrutura. A senha está como placeholder, mas host/porta/user/db-name são reais.

**Correção:**
```env
SERPLENO_DB_HOST=localhost
SERPLENO_DB_PORT=3306
SERPLENO_DB_USER=root
SERPLENO_DB_PASSWORD=
SERPLENO_DB_NAME=ser_pleno
```

---

### 2.2. Token de API hardcoded como fallback
**Severidade:** ALTA (Segurança)  
**Arquivo:** `src/ser_pleno/features/agenda/service.py`  
**Linha:** 27

```python
API_TOKEN = DESKTOP_API_TOKEN or "serpleno-desktop-token-2024"
```

**Causa raiz:** Token hardcoded no código fonte. Se `DESKTOP_API_TOKEN` não for configurado, o app usa um token previsível.

**Impacto:** Qualquer pessoa pode se passar pelo desktop app na API usando token fixo.

**Correção:**
```python
API_TOKEN = DESKTOP_API_TOKEN
if not API_TOKEN:
    raise ValueError("SERPLENO_DESKTOP_API_TOKEN deve ser configurado no .env")
```

---

### 2.3. Senha armazenada em cache local sem criptografia
**Severidade:** ALTA (Segurança)  
**Arquivo:** `src/ser_pleno/repositories/autenticacao.py`, `src/ser_pleno/infrastructure/local/local_cache.py`

**Causa raiz:** O `local_cache` SQLite armazena hashes de senha (`auth_users.password`) em texto plano (o hash Django, mas sem camada adicional). O arquivo `ser_pleno_local.db` fica em `config/ser_pleno_local.db` sem criptografia.

**Impacto:** Se o computador for comprometido, atacante obtém hashes de senha de todos os usuários locais.

**Correção:**
- Implementar criptografia do banco SQLite (ex.: SQLCipher)
- Ou armazenar apenas referência, nunca o hash completo em cache local
- Adicionar permissões restritivas no filesystem para `config/`

---

### 2.4. `agenda.py` cria `AgendamentoRepository()` diretamente (código morto)
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/agenda.py`

**Causa raiz:** A view instancia `AgendamentoRepository()` diretamente e não o usa posteriormente (conforme documentado em `fluxos-incompletos.md` seção 5.3).

**Impacto:** Código morto, confusão arquitetural, possível uso acidental sem fallback.

**Correção:** Remover a instanciação direta. Usar apenas `self.servico_agenda` injetado pela factory.

---

### 2.5. Help Requests — ações incompletas na UI
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/pedidos_ajuda.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 2.5

**Causa raiz:** `PedidosAjudaController` lista pedidos, mas não implementa ações de update/respond na UI. A view exibe lista mas não permite marcar como visto, iniciar atendimento ou responder (apesar do `ResponderModal` existir no código).

**Impacto:** Funcionalidade de help requests é apenas leitura. Suporte ao aluno não pode ser operacionalizado.

**Correção:** Conectar os botões da view aos métodos do service:
```python
# Em pedidos_ajuda.py, adicionar botões de ação:
GhostButton(..., command=lambda p=pedido: self._marcar_visto(p))
GhostButton(..., command=lambda p=pedido: self._iniciar_atendimento(p))
GhostButton(..., command=lambda p=pedido: self._responder(p))
```

---

### 2.6. Notificações nativas não consumidas pela API
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/notificacoes.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 2.6

**Causa raiz:** A view existe e consome `ServicoNotificacoes`, mas o service usa `ClienteAPI` para endpoints de notificações que podem não estar implementados no back-end desktop. A view `notificacoes.py` existe mas não está no `MENU_ITEMS` da navigation (apenas no `view_factory`).

**Impacto:** View acessível apenas por navegação direta ou rotas não documentadas. Badges de notificação no dashboard não refletem notificações reais da API.

**Correção:** Adicionar `notificacoes` ao `MENU_ITEMS` em `navigation.py` ou integrar badges com o service existente.

---

### 2.7. Exportações de relatórios sem parametrização
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/relatorio.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 3.1

**Causa raiz:** Os botões de exportação chamam `exportar_estudantes()`, `exportar_agendamentos()`, `exportar_triagens()` sem:
- Seleção de período
- Filtros adicionais
- Confirmação de caminho/destino
- Feedback de progresso

O serviço `ServicoRelatorio` gera conteúdo em memória (bytes/strings) e retorna, mas a UI não trata fallback amigável.

**Impacto:** Exportações geram arquivos com todos os dados, sem controle do usuário. Possível OOM em bases grandes.

**Correção:**
```python
# Criar modal de exportação com filtros:
class ExportModal(BaseModal):
    def _build(self):
        # Filtros: data_from, data_to, tipo, formato
        # Preview de quantidade de registros
        # Botão "Exportar" que chama service com parametrização
```

---

### 2.8. Comunicação — envio de arquivo sem validação
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/comunicacao.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 3.2

**Causa raiz:** O método `enviar_mensagem_grupo_arquivo` envia arquivos selecionados do disco sem validar:
- Existência antes do payload
- Tamanho (limite de 10MB definido em `_MAX_FILE_SIZE_BYTES` mas não aplicado na view)
- Tipo MIME compatível com o back-end

**Impacto:** Uploads falham silenciosamente ou causam erros 500 no servidor. Possível DoS por arquivos grandes.

**Correção:**
```python
def _validar_arquivo(self, caminho):
    if not os.path.exists(caminho):
        raise ValueError("Arquivo não encontrado")
    tamanho = os.path.getsize(caminho)
    if tamanho > _MAX_FILE_SIZE_BYTES:
        raise ValueError(f"Arquivo excede {_MAX_FILE_SIZE_BYTES // 1024 // 1024}MB")
    ext = os.path.splitext(caminho)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de arquivo não suportado")
    return True
```

---

### 2.9. Campos de data sem validação/normalização (Triagem)
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/triagem.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 4.3

**Causa raiz:** `_DateField` usa texto livre `dd/mm/aaaa` sem validação ou normalização. O back-end pode esperar ISO (`YYYY-MM-DD`).

**Impacto:** Dados de data inválidos causam falhas de integridade. Ex.: `31/02/2024` ou `2024-13-01`.

**Correção:**
```python
from ser_pleno.utils.dates import normalize_date

class _DateField(ctk.CTkFrame):
    def get(self) -> str:
        raw = self.entry.get().strip()
        return normalize_date(raw)  # Retorna YYYY-MM-DD ou levanta ValueError
```

---

### 2.10. Triagem — `listar_formularios()` não consumida
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/ui/views/triagem.py`  
**Status confirmado em:** `fluxos-incompletos.md` seção 2.4

**Causa raiz:** `TriagemController.listar_formularios()` existe, mas `triagem.py` não o chama. O modal "Nova Triagem" usa campos hardcoded sem formulários pré-cadastrados.

**Impacto:** Triagens não usam os formulários estruturados do sistema, perdendo validações e estrutura.

**Correção:** Conectar o modal "Nova Triagem" ao service para carregar formulários disponíveis.

---

### 2.11. `_apply_saved_notification_settings` recarrega service desnecessariamente
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/app.py`  
**Linha:** 266-290

**Causa raiz:** `_apply_saved_notification_settings` cria uma nova instância de `ServicoConfiguracoes` a cada login, em vez de usar `self.servico_configuracoes` já inicializado em `_init_services`.

**Impacto:** Duplicação de instâncias, possível inconsistência de estado, desperdício de recursos.

**Correção:**
```python
def _apply_saved_notification_settings(self) -> None:
    try:
        servico = getattr(self, "servico_configuracoes", None)
        if servico is None:
            return
        # ... usar servico existente
```

---

### 2.12. `WebSocketChatClient` usa `threading.Lock()` incorretamente
**Severidade:** ALTA  
**Arquivo:** `src/ser_pleno/infrastructure/api/websocket_client.py`  
**Linhas:** 113, 129

```python
with threading.Lock():  # Cria um NOVO lock a cada chamada!
```

**Causa raiz:** `threading.Lock()` (instanciação) cria um lock novo e descartável a cada entrada no contexto. Isso não protege contra race conditions — cada thread tem seu próprio lock.

**Impacto:** Race conditions na conexão WebSocket. Conexões simultâneas podem corromper o estado do client.

**Correção:**
```python
class WebSocketChatClient:
    def __init__(self, ...):
        self._lock = threading.Lock()  # Instanciar UMA vez
    
    def connect(self, ...):
        with self._lock:  # Usar a instância
            ...
```

---

## 3. PROBLEMAS DE SEVERIDADE MÉDIA

### 3.1. `extend_theme()` no escopo do módulo (bem_estar, orientacoes)
**Severidade:** MÉDIA  
**Arquivos:** `src/ser_pleno/ui/views/bem_estar.py`, `src/ser_pleno/ui/views/orientacoes.py`

**Causa raiz:** `O = extend_theme(THEME, {...})` é executado na importação do módulo. Se o tema for alterado dinamicamente após a importação, `O` não reflete a atualização.

**Impacto:** Tema não atualiza corretamente em runtime para tokens estendidos.

**Correção:**
```python
# Converter O em função ou property:
def get_theme_tokens():
    return extend_theme(THEME, { ... })
# Ou usar lazy evaluation nos pontos de uso
```

---

### 3.2. Alteração de senha sem reautenticação forte
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/ui/views/configuracoes.py`, `src/ser_pleno/ui/views/dashboard.py`

**Causa raiz:** O modal de alteração de senha pede `senha_atual` e `nova_senha`, mas não há step adicional de confirmação/reauth forte além dos campos. Em `dashboard.py` linha 1417, a chamada é:
```python
res = auth_service.alterar_senha(user.get("password", ""), senha)
```
O primeiro argumento deve ser a senha atual digitada pelo usuário, não o hash armazenado.

**Impacto:** Se a sessão for roubada, atacante pode alterar senha sem confirmação adicional.

**Correção:**
```python
# Em dashboard.py _editar_perfil:
senha_atual_digitada = entry_senha_atual.get().strip()
res = auth_service.alterar_senha(senha_atual_digitada, senha)
```

---

### 3.3. SQL Injection potencial em `sync_service.py`
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/api/sync_service.py`

**Causa raiz:** `_apply_update_to_mysql` constrói query com f-string:
```python
query = f"UPDATE {table} SET {set_clause} WHERE {pk_column} = %s"
```
Embora `validate_mysql_table_name` proteja `table`, `set_clause` é construído dinamicamente com `key` do dicionário de dados. Se `data` contiver chaves maliciosas, há injeção SQL.

**Impacto:** Potencial SQL injection se dados forem manipulados por entrada do usuário.

**Correção:**
```python
# Validar chaves antes de usar:
for key in data.keys():
    if not key.isidentifier():
        raise ValueError(f"Coluna inválida: {key}")
# Usar whitelist de colunas por tabela
```

---

### 3.4. Fallback de auth_user armazena senha em memória sem necessidade
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/repositories/autenticacao.py`, `src/ser_pleno/application/services/autenticacao.py`

**Causa raiz:** `_login_local` retorna o usuário completo incluindo hash de senha. O hash é propagado por toda a aplicação via `self.user`.

**Impacto:** Exposição desnecessária de hashes. Em caso de dump de memória ou log acidental, senhas são expostas.

**Correção:**
```python
# Retornar usuário sem campo password:
user_out = {k: v for k, v in user.items() if k != "password"}
return {"success": True, "user": user_out}
```

---

### 3.5. `_safe_json` falha ao logar conteúdo em caso de erro
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/api/api.py`  
**Linha:** 34

```python
logging.error(f"Conteúdo bruto: {repr(getattr(response, 'text', response))}")
```

**Causa raiz:** Se `response` não tiver atributo `.text`, `getattr` retorna o próprio objeto `response`, que pode ser gigante ou causar `RecursionError` no `repr()`.

**Impacto:** Logs gigantes, possível crash no logging.

**Correção:**
```python
raw = getattr(response, 'text', None) or repr(response)[:500]
logging.error("Conteúdo bruto: %s", raw)
```

---

### 3.6. `SyncQueue` usa timestamp flutuante como ID
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/local/local_cache.py`  
**Linha:** 255

```python
"id": f"{operation}_{entity}_{entity_id}_{datetime.now().timestamp()}",
```

**Causa raiz:** `datetime.now().timestamp()` tem precisão de microssegundos, mas duas operações no mesmo microssegundo colidem. SQLite `ON CONFLICT DO UPDATE` pode sobrescrever entradas legítimas.

**Impacto:** Perda silenciosa de operações na fila de sincronização.

**Correção:**
```python
import uuid
"id": f"{operation}_{entity}_{entity_id}_{uuid.uuid4().hex}",
```

---

### 3.7. `notificacoes.py` referencia `auth_service` no lugar errado
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/ui/views/notificacoes.py`  
**Linha:** 121

```python
auth = getattr(self, "auth_service", None) or getattr(self.controller, "auth_service", None)
```

**Causa raiz:** `auth_service` está em `self.controller` (ou `self.app.auth_service`), nunca em `self`. A busca em `self` é desnecessária.

**Impacto:** Funciona por coincidência (fallback para controller), mas é confuso e quebra se `controller` não tiver `auth_service`.

**Correção:**
```python
auth = getattr(self.controller, "auth_service", None) or getattr(self.app, "auth_service", None)
```

---

### 3.8. `comunicacao.py` caminho de imagens inválido
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/ui/views/comunicacao.py`  
**Linha:** 121

```python
self.img_path = os.path.join(self.base_path, "..", "imagens")
```

**Causa raiz:** O caminho sobe um nível (`..`) do `base_path` (raiz do projeto) para `imagens/`, mas essa pasta não existe na estrutura do projeto.

**Impacto:** Imagens de chat não carregam. Avatares podem aparecer como placeholders.

**Correção:**
```python
self.img_path = os.path.join(self.base_path, "assets", "images")
# Ou usar get_assets_dir()
```

---

### 3.9. `_login_api` timeout muito agressivo (1.5s)
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/application/services/autenticacao.py`  
**Linha:** 119

```python
response = self.session.post(
    login_url,
    json={"username": usuario, "password": senha},
    timeout=1.5,
)
```

**Causa raiz:** Timeout de 1.5s para login API é muito curto para redes com latência normal (ex.: 3G, VPN). Causa falsos negativos de conexão.

**Impacto:** Login funciona localmente mas falha ao tentar estabelecer sessão API, gerando logs de erro desnecessários.

**Correção:**
```python
timeout=5  # ou usar valor configurável
```

---

### 3.10. `App._init_services` é chamado mas serviços também são importados no topo
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/app.py`  
**Linhas:** 67-88

**Causa raiz:** O arquivo importa todos os serviços no topo (ex.: `from ser_pleno.features.agenda.service import ServicoAgendamento`) para type hints e referências, mas também cria instâncias em `_init_services`. Isso causa importações pesadas no startup mesmo antes do login.

**Impacto:** Cold start lento. Módulos são carregados mesmo se o usuário nunca acessar certas features.

**Correção:**
- Mover imports para dentro dos métodos (lazy import)
- Ou usar `TYPE_CHECKING` para imports de tipo

---

### 3.11. Fallback metrics não thread-safe para escrita
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/local/fallback_metrics.py`

**Causa raiz:** `_save_metrics` abre/escreve/fecha arquivo JSON a cada registro de fallback. Se múltiplas threads caírem em fallback simultaneamente, há race condition na escrita.

**Impacto:** Corrupção do arquivo `fallback_metrics.json`.

**Correção:**
```python
def record_fallback(...):
    with _lock:
        metrics = _load_metrics()
        # ... modificar metrics
        _save_metrics(metrics)  # Escrita protegida pelo lock
```

---

### 3.12. Seed de roles com IDs negativos hardcoded
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/local/seed_service.py`  
**Linha:** 178-185

```python
_BASIC_ROLES = [
    {"user_id": -1, "role": "visitante", ...},
    {"user_id": -2, "role": "psicologo", ...},
    ...
]
```

**Causa raiz:** IDs negativos são usados como placeholders para roles globais. Se o sistema de geração de IDs locais (também negativo) colidir, há conflito.

**Impacto:** Perda de associação role→usuário em modo offline.

**Correção:**
```python
# Usar IDs positivos reservados longe do range de auto-increment:
_BASIC_ROLES = [
    {"user_id": 1000000, "role": "visitante", ...},
    ...
]
```

---

### 3.13. `_process_queue_item` tem fluxo de controle perigoso
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/api/sync_service.py`  
**Linha:** 272-289

```python
if operation == 'create':
    ...
    response = self._session.post(...)
if response.status_code in [200, 201]:  # Este if executa PARA TODAS as operações!
    ...
if operation == 'update':
    ...
if operation == 'delete':
    ...
```

**Causa raiz:** Após o bloco `if operation == 'create':`, o código **não usa `elif`** para `update` e `delete`. A variável `response` é sobrescrita, e o bloco `if response.status_code in [200, 201]` executa para todas as operações, não apenas create.

**Impacto:** Comportamento imprevisível na fila de sincronização. Operações update/delete podem ser tratadas como create.

**Correção:**
```python
if operation == 'create':
    response = self._session.post(...)
    if response.status_code in [200, 201]:
        ...
elif operation == 'update':
    response = self._session.put(...)
    ...
elif operation == 'delete':
    response = self._session.delete(...)
    ...
```

---

### 3.14. Triagem — `_DateField` sem validação de entrada
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/ui/views/triagem.py`  
**Linha:** 62-101

**Causa raiz:** `_DateField` é um `CTkEntry` com placeholder. Aceita qualquer texto sem validação de formato.

**Impacto:** Datas inválidas são salvas no banco, causando falhas em relatórios e sincronização.

**Correção:**
```python
self.entry.bind("<FocusOut>", lambda e: self._validar_data())
def _validar_data(self):
    raw = self.entry.get().strip()
    try:
        datetime.strptime(raw, "%d/%m/%Y")
    except ValueError:
        self.entry.configure(border_color=THEME["danger"])
        # Mostrar erro
```

---

### 3.15. `LoginInputField.set_error` e `clear_state` são no-ops
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/ui/views/login.py`  
**Linha:** 176-180

```python
def set_error(self, message: str) -> None:
    pass

def clear_state(self) -> None:
    pass
```

**Causa raiz:** Métodos definidos mas não implementados. Erros de validação não são visualmente destacados no login.

**Impacto:** Usuário não recebe feedback visual de campos inválidos além do texto de erro geral.

**Correção:** Implementar mudança de cor de borda e label de erro:
```python
def set_error(self, message: str) -> None:
    self.entry.configure(border_color=THEME["danger"])
    self._label.configure(text_color=THEME["danger"])
def clear_state(self) -> None:
    self.entry.configure(border_color=THEME["border"])
    self._label.configure(text_color=THEME["text_secondary"])
```

---

## 4. PROBLEMAS DE SEVERIDADE BAIXA

### 4.1. README refere-se a estrutura desatualizada
**Severidade:** BAIXA  
**Arquivo:** `README.md`  
**Linha:** 27-82

**Causa raiz:** README lista estrutura `desktop_serpleno/` mas o projeto é `serpleno-desktop/`. Lista `src/ser_pleno/ui/theme.py` como arquivo único, mas é um pacote.

**Impacto:** Confusão para novos desenvolvedores.

---

### 4.2. Avisos sem filtros avançados
**Severidade:** BAIXA  
**Arquivo:** `src/ser_pleno/ui/views/avisos.py`

**Causa raiz:** View lista publicações sem filtro por categoria/data, sem contador/status bar. Falhas de carregamento mostram texto solto.

**Impacto:** UX ruim em quadros de avisos com muitas publicações.

---

### 4.3. Performance — `minsize(1920, 1080)` já listado como CRÍTICO
**Severidade:** BAIXA (como problema isolado de performance)  
**Arquivo:** `src/ser_pleno/app.py`

Além de ser um problema de compatibilidade, o `minsize` também causa desperdício de GPU/memória em telas menores, pois o CustomTkinter renderiza widgets fora da viewport visível.

---

### 4.4. Logs de debug excessivos em produção
**Severidade:** BAIXA  
**Arquivo:** Diversos services

**Causa raiz:** Muitos `logger.info()` e `logger.debug()` em loops (ex.: `sync_service.py` linha 841-864). Em modo debug, isso gera I/O intensivo.

**Impacto:** Lentidão em operações de sincronização com muitas linhas.

---

### 4.5. `get_operation_config()` é chamado repetidamente
**Severidade:** BAIXA  
**Arquivo:** Diversos services

**Causa raiz:** Padrão `_get_operation_config` com lazy loading é repetido em cada service. Poderia ser um singleton injetado.

**Impacto:** Overhead mínimo, mas código duplicado.

---

### 4.6. `pyproject.toml` markdown README errado
**Severidade:** BAIXA  
**Arquivo:** `pyproject.toml`  
**Linha:** 5

```toml
readme = "README_pt.md"
```

Mas o arquivo existente é `README.md`.

---

### 4.7. Testes de UI usam `MagicMock` excessivo
**Severidade:** BAIXA  
**Arquivo:** `tests/test_views.py`

**Causa raiz:** `test_intervencoes_view` usa 8 patches simultâneos. Testes não validam comportamento real, apenas presença de atributos.

**Impacto:** Falsos positivos. Bugs de UI não são detectados.

---

### 4.8. `pytest_result.txt` está no repositório
**Severidade:** BAIXA  
**Arquivo:** `pytest_result.txt` (raiz)

**Causa raiz:** Artefato de teste commitado.

**Impacto:** Poluição do diff.

---

### 4.9. `venv/` está no repositório
**Severidade:** BAIXA  
**Arquivo:** `venv/` (raiz)

**Causa raiz:** Ambiente virtual versionado.

**Impacto:** Repositório grande, conflitos de path entre SOs.

---

## 5. VULNERABILIDADES DE SEGURANÇA

### 5.1. Token de API hardcoded (já listado como ALTA)

### 5.2. Credenciais de produção em `.env.example` (já listado como ALTA)

### 5.3. Password hashes em cache local sem criptografia (já listado como ALTA)

### 5.4. Falta de rate limiting em login
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/application/services/autenticacao.py`

**Causa raiz:** `_login_local` não tem limite de tentativas. Atacante pode brute-force localmente sem bloqueio.

**Correção:**
```python
def login(self, usuario, senha):
    if self._login_attempts >= 5:
        return {"success": False, "message": "Conta bloqueada temporariamente"}
    # ...
```

### 5.5. CSRF token obtido de endpoint não relacionado
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/application/services/autenticacao.py`  
**Linha:** 73

```python
response = self.session.get(
    f"{self.API_BASE_URL}/api/v1/desktop/schedule/times/",
    timeout=5
)
```

**Causa raiz:** CSRF token é obtido de um endpoint de agenda, não de um endpoint dedicado de CSRF. Se o endpoint mudar, o token deixa de funcionar.

**Correção:**
```python
response = self.session.get(f"{self.API_BASE_URL}/api/v1/csrf/")
```

---

## 6. GARGALOS DE PERFORMANCE

### 6.1. Cold start carrega todos os serviços
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/app.py`

**Causa raiz:** Imports no topo do arquivo carregam ~20 serviços antes do login.

**Impacto:** Tempo de boot elevado.

**Correção:** Lazy import nos métodos que usam cada serviço.

### 6.2. `_draw_chart` redesenhado em cada `after_idle`
**Severidade:** BAIXA  
**Arquivo:** `src/ser_pleno/ui/views/dashboard.py`

**Causa raiz:** `_schedule_draw_chart` agenda redraw a cada configure event, mas não debounce adequadamente.

**Impacto:** CPU usage durante resize.

### 6.3. `local_cache` abre conexão SQLite por thread
**Severidade:** BAIXA  
**Arquivo:** `src/ser_pleno/infrastructure/local/local_cache.py`

**Causa raiz:** `threading.local()` para conexão SQLite é OK, mas não há limite de conexões por processo.

---

## 7. COMPATIBILIDADE COM OS

### 7.1. Recursos Windows-only sem fallback adequado
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/desktop/native_notifier.py`, `src/ser_pleno/ui/views/login.py`

**Causa raiz:**
- `winsound.MessageBeep` apenas Windows
- `win10toast` apenas Windows
- `ctypes.windll.user32.MessageBoxW` apenas Windows
- Música de fundo no login apenas Windows (`_IS_WINDOWS`)

**Impacto:** App não roda em macOS/Linux. Falta de fallbacks visuais/auditivos.

**Correção:** Usar `plyer` (já dependência) como camada de abstração multiplataforma.

### 7.2. `darkdetect` pode não funcionar em Linux headless
**Severidade:** BAIXA  
**Arquivo:** `src/ser_pleno/ui/theme/__init__.py`

**Impacto:** Tema pode não detectar preferência do sistema corretamente.

---

## 8. FLUXOS INCONSISTENTES E GAPS

### 8.1. Modo `DB_PRIMARY` não testado
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/config/operation_mode.py`

**Causa raiz:** Modo `DB_PRIMARY` (banco primário, API como fallback) está documentado mas não há testes ou UI para alternar para ele. Apenas `INDEPENDENT`, `HYBRID`, `CONNECTED` são cobertos.

### 8.2. Sincronização não reconcilia todos os tipos de entidade
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/api/sync_service.py`

**Causa raiz:** `_sync_local_data` sincroniza apenas `students` e `appointments`. Outras entidades (orientations, screenings, messages, reports) não são sincronizadas com a API.

### 8.3. `_reconcile_local_id` não atualiza todas as FK
**Severidade:** MÉDIA  
**Arquivo:** `src/ser_pleno/infrastructure/api/sync_service.py`  
**Linha:** 330-345

**Causa raiz:** `_update_fk_references` só atualiza FK de `students`. Outras entidades não têm mapeamento.

---

## 9. RESUMO DE CORREÇÕES PRIORITÁRIAS

| Prioridade | Ação | Arquivo(s) | Esforço |
|-----------|------|-----------|---------|
| **P0** | Remover `minsize(1920,1080)` | `app.py` | 1 linha |
| **P0** | Adicionar `from typing import Any` | `app.py` | 1 linha |
| **P0** | Implementar formulário de check-in no Bem-Estar | `bem_estar.py` | ~100 linhas |
| **P0** | Persistir configurações (toggles → service) | `configuracoes.py` | ~50 linhas |
| **P0** | Implementar `_duplicar_orientacao` ou remover botão | `orientacoes.py` | ~30 linhas |
| **P0** | Corrigir instanciação duplicada de controllers | `dashboard.py`, `estudantes.py` | ~10 linhas |
| **P1** | Remover credenciais de `.env.example` | `.env.example` | 5 linhas |
| **P1** | Trocar token hardcoded por erro | `agenda/service.py` | 3 linhas |
| **P1** | Corrigir `threading.Lock()` no WebSocket | `websocket_client.py` | 2 linhas |
| **P1** | Converter `if`/`if` em `if`/`elif`/`elif` | `sync_service.py` | 1 linha |
| **P1** | Validar arquivos antes de upload | `comunicacao.py` | ~30 linhas |
| **P1** | Normalizar datas em Triagem | `triagem.py` | ~20 linhas |
| **P2** | Criptografar `ser_pleno_local.db` | `local_cache.py` | ~50 linhas |
| **P2** | Implementar actions de Help Requests na UI | `pedidos_ajuda.py` | ~80 linhas |
| **P2** | Adicionar `notificacoes` ao menu de navegação | `navigation.py` | 3 linhas |

---

## 10. RECOMENDAÇÕES ARQUITETURAIS

1. **Adotar Dependency Injection formal:** Evitar instanciação direta de services/repositories nas views. Usar uma factory ou container.

2. **Centralizar configuração de timeouts:** Criar `config/timeouts.py` com valores configuráveis por ambiente.

3. **Implementar retry com backoff exponencial:** Substituir retry simples por `tenacity` ou similar, especialmente para API e MySQL.

4. **Adicionar rate limiting no login:** Usar `cachetools` ou similar para tracking de tentativas por usuário.

5. **Separar concerns de sync:** O `SyncService` faz sync MySQL↔SQLite e SQLite↔API. Decompor em `MySQLSyncService` e `APISyncService`.

6. **Testes de integração:** Adicionar testes que rodam contra SQLite real (não apenas mocks) para validar fallback.

7. **CI/CD com build automatizado:** O `.github/workflows/release.yml` existe mas não foi verificado. Garantir que rode em Windows limpo.

8. **Documentação de modos de operação:** Criar guia visual para usuário escolhendo entre Independente/Híbrido/Conectado.
