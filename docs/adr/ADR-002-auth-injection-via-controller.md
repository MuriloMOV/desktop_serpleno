# ADR-002: Injeção de auth_service via controller

**Data:** 2026-07-15  
**Status:** Aceito  
**Decisores:** Equipe SerPleno  

---

## Contexto

Originalmente, o estado de autenticação (`_auth_service`) era armazenado como variável global em módulos como:
- `src/ser_pleno/infrastructure/api/api.py` — `_auth_service`, `set_auth_service()`, `get_auth_service()`
- `src/ser_pleno/application/services/agendamentos.py` — mesmo padrão
- `src/ser_pleno/presentation/views/login.py:746` — chamada `set_auth_service()` após login

Esse padrão criava **acoplamento oculto** entre módulos distantes, dificultando:
- Testes unitários (necessário mockar estado global)
- Manutenção (difícil rastrear quem modifica o estado)
- Reutilização (services dependem de estado global existente)

---

## Decisão

Remover o estado global de `auth_service` e propagá-lo explicitamente via **injeção de dependência** no construtor.

### Implementação

1. **Remover globais:** `_auth_service`, `set_auth_service()`, `get_auth_service()` de `api.py`, `mural.py`, `services/agendamentos.py`
2. **Injeção via `__init__`:** Services recebem `auth_service` como parâmetro opcional
3. **Controllers como fachada:** `AutenticacaoController` expõe `auth_service` como propriedade
4. **App orquestra:** `App.iniciar_sistema()` injeta `auth_service` nos controllers

### Código de exemplo

```python
# Controller
class AutenticacaoController(BaseController):
    def __init__(self, auth_service=None):
        super().__init__(ServicoAutenticacao, auth_service=auth_service)

    @property
    def auth_service(self):
        return self.get_service()

# Service
class ServicoAutenticacao:
    def __init__(self, auth_service=None):
        self._auth_service = auth_service
        self._api = ClienteAPI(auth_service=auth_service)

# App
def iniciar_sistema(self, user_data, auth_service=None):
    self.auth_service = auth_service
    # Controllers recebem auth_service via __init__
```

---

## Consequências

### Positivas

- **Acoplamento explícito:** Dependências visíveis na assinatura do construtor
- **Testabilidade:** `ServicoAutenticacao(auth_service=mock)` — sem estado global
- **Instanciação independente:** Services podem ser criados sem estado global pré-existente
- **Type safety:** IDEs conseguem inferir tipos e detectar erros

### Negativas

- **Boilerplate:** `__init__` de services/controllers precisa receber `auth_service`
- **`__getattr__` mantido:** `BaseController` mantém fallback deprecated para compatibilidade
- **Propagação manual:** `App.iniciar_sistema()` precisa injetar `auth_service` em cada controller

---

## Alternativas consideradas

| Alternativa | Razão de rejeição |
|-------------|-------------------|
| DI Container (ex.: `dependency_injector`) | Over-engineering para ~10 telas |
| Singleton pattern | Mesmo problema de acoplamento oculto |
| Event Bus para auth | Nenhum fluxo de eventos complexo identificado |

---

## Referências

- `src/ser_pleno/application/controllers/base.py` — `BaseController.__init__`
- `src/ser_pleno/utils/service_helpers.py` — `with_api_fallback`
- `docs/desenvolvimento.md` — seção "Padrões existentes"
