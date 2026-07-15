# ADR-001: Repository Pattern com fallback offline-first

**Data:** 2026-07-15  
**Status:** Aceito  
**Decisores:** Equipe SerPleno  

---

## Contexto

O desktop SerPleno precisa funcionar de forma confiável em dois cenários:
1. **Conectado:** com acesso à API SerPleno Web e MySQL
2. **Offline:** sem conexão, usando apenas banco local SQLite

Além disso, o sistema deve sincronizar dados automaticamente quando a conexão for restaurada.

O problema original era que o SQL estava espalhado diretamente nos Services, sem uma camada de abstração para trocar a fonte de dados.

---

## Decisão

Adotar o **Repository Pattern** como camada de acesso a dados, com fallback automático MySQL → SQLite.

### Implementação

1. **Repository como camada intermediária** entre Services e banco de dados
2. **MySQL como fonte primária** — conexão via `ser_pleno.config.db_config`
3. **SQLite como fallback automático** — via `ser_pleno.infrastructure.local.local_cache`
4. **Decorator `with_local_fallback`** — intercepta erros de conexão MySQL e redireciona para métodos `_local_*`
5. **`write_with_fallback`** — grava local + enfileira para sync quando MySQL indisponível
6. **IDs locais negativos** — gerados automaticamente para entidades criadas offline

### Código de exemplo

```python
from ser_pleno.repositories.base import with_local_fallback

class EstudanteRepository:
    @with_local_fallback("_local_listar")
    def listar(self, busca: str = "") -> list:
        query = "SELECT * FROM students WHERE nome LIKE %s"
        return fetch_all(query, (f"%{busca}%",))

    def _local_listar(self, busca: str = "") -> list:
        # Fallback SQLite
        return self._local_cache.listar_estudantes(busca)
```

---

## Consequências

### Positivas

- **Funcionamento offline garantido:** O desktop funciona sem API ou MySQL
- **Desacoplamento:** Services não sabem qual fonte de dados está sendo usada
- **Testabilidade:** Repositories podem ser mockados facilmente nos testes
- **Sync automática:** `write_with_fallback` enfileira operações para sync posterior

### Negativas

- **Complexidade adicional:** Cada repository precisa de métodos `_local_*` duplicados
- **IDs locais negativos:** Precisam ser tratados no sync para evitar conflitos
- **Duplicação de queries:** SQL escrito duas vezes (MySQL + SQLite)

---

## Alternativas consideradas

| Alternativa | Razão de rejeição |
|-------------|-------------------|
| SQLAlchemy ORM | Over-engineering para escala atual; SQL raw funciona |
| API-only (sem offline) | Quebra requisito de funcionamento offline |
| Local-first (SQLite primário) | MySQL é a fonte de verdade institucional |

---

## Referências

- `src/ser_pleno/repositories/base.py` — decorators e helpers
- `src/ser_pleno/infrastructure/local/local_cache.py` — fallback SQLite
- `docs/desenvolvimento.md` — seção "Padrões existentes"
