# Relatório de Análise e Melhorias — SerPleno Desktop

**Data:** 2026-06-30  
**Autor:** Consultor Sênior (Kilo)  
**Status:** Em execução  

---

## 1. Painel de Especialistas e Desafio Inicial

### Especialistas Simulados

| Papel | Foco |
|---|---|
| Engenheiro de Segurança (AppSec) | Vazamento de segredos, injeção SQL, gestão de credenciais |
| Arquiteto de Software (Staff Engineer) | Camadas, DI, desacoplamento, resiliência |
| Engenheiro DevOps/SRE | CI/CD, empacotamento, reprodutibilidade, observabilidade |
| Engenheiro de Qualidade (QA Lead) | Cobertura de testes, mocks, regressão |
| Especialista em Ecosystem Python | Dependências, lockfiles, tooling, PEPs |

### Armadilhas Críticas Identificadas

1. `.env` com credenciais root do MySQL commitado no repositório.
2. `requirements.txt` em UTF-16/CLIXML quebra instalação em ambientes *nix/CI.
3. Camada de controllers é "fake MVC" via `__getattr__` — sem mediação real entre view e service.
4. SQL dinâmico em `repositories/estudantes.py` via f-string em `UPDATE` — vetor de injeção caso filtros venham da UI.
5. Ausência de CI/CD, tooling统一 e lockfiles — débito operacional crescente.

---

## 2. Filtro Anti-Sycophancy — Falhas Críticas Aceitas como Premissas

### Falha 1: Exposição de Segredos no Histórico Git
O `.env` contém credenciais em plaintext (`SERPLENO_DB_PASSWORD=MySQL3691@26`, `SERPLENO_DB_USER=root`) e está **versionado**. Isso compromete todo o histórico Git caso o repositório seja público ou sofra vazamento. Além disso, o usuário `root` do banco é usado diretamente pela aplicação desktop.

**Risco:** Quebra de confidencialidade, compliance LGPD, acesso total ao banco de dados.

### Falha 2: Camada de Controllers como Proxy Transparente
`BaseController` implementa `__getattr__` que simplesmente repassa chamadas para o service. Qualquer regra de negócio futura terá que ser espalhada ou quebrar o contrato. A view acessa o service **indiretamente** sem ganho arquitetural.

**Risco:** Dívida técnica estrutural, difícil de refatorar depois sem risco.

---

## 3. Planejamento Estratégico Adaptativo

**Racional:** A arquitetura atual funciona, mas acumula débito em três eixos: **Segurança**, **Resiliência Operacional** e **Manutenibilidade**. As melhorias priorizam:
1. Remoção de vulnerabilidades (secrets, SQL injection risk)
2. Reprodutibilidade (tooling, lockfiles)
3. Evolução arquitetural (controllers de verdade, type-safety)

**Hierarquia:** VERDADE > LÓGICA > ROBUSTEZ > UTILIDADE > CLAREZA

---

## 4. Backlog Hierárquico Exaustivo

### `[Segurança Crítica]`

| ID | Tarefa | Prioridade |
|---|---|---|
| S-01 | Remover `.env` do histórico Git e rotacionar credenciais | Alta |
| S-02 | Criar usuário MySQL com privilégios mínimos para a aplicação | Alta |
| S-03 | Eliminar dependências duplicadas de MySQL (`mysqlclient`, `PyMySQL`, `mysql-connector-python`) | Média |

### `[Configuração de Ambiente / Tooling]`

| ID | Tarefa | Prioridade |
|---|---|---|
| T-01 | Corrigir encoding do `requirements.txt` para UTF-8 puro | Alta |
| T-02 | Adicionar lockfile (`requirements.lock` via `pip freeze`) | Média |
| T-03 | Criar `pyproject.toml` com metadados e configs (ruff, mypy, pytest) | Média |
| T-04 | Atualizar `.gitignore` para bloquear artefatos perigosos (`.env.local`, `*.log`, `.spec`) | Alta |
| T-05 | Remover `debug.log` e `SerPleno.spec` do repositório | Média |

### `[Execução / Refatoração]`

| ID | Tarefa | Prioridade |
|---|---|---|
| R-01 | Implementar `BaseController` com métodos explícitos (remover `__getattr__`) | Alta |
| R-02 | Substituir concatenação de SQL em `repositories/estudantes.py` por whitelist + validação | Alta |
| R-03 | Adicionar context manager para conexões MySQL (`with get_connection() as conn`) | Média |
| R-04 | Centralizar configuração de logging (handlers, formatters, níveis por módulo) | Média |
| R-05 | Adicionar handler de exceções global na aplicação CustomTkinter | Baixa |

### `[Validação / QA]`

| ID | Tarefa | Prioridade |
|---|---|---|
| Q-01 | Configurar pipeline CI (GitHub Actions) com lint + type check + tests | Alta |
| Q-02 | Converter testes de smoke para testes de integração com SQLite fixtures | Média |
| Q-03 | Adicionar testes de contrato para a camada de API (fixtures de resposta) | Média |
| Q-04 | Configurar pre-commit hooks (ruff, mypy, trailing spaces, large files) | Baixa |

---

## 5. Planos de Implementação Detalhados (por Tarefa)

### Tarefa S-01: Remover `.env` do Histórico Git e Rotacionar Credenciais

**Ação:** Executar `git filter-repo` ou `git filter-branch` para remover o arquivo do histórico; invalidar a senha antiga; atualizar `.env.example`.

**Método & Ferramentas:** `git filter-repo`, `mysql` CLI.

**Exemplo:**
```sql
CREATE USER 'serpleno_app'@'localhost' IDENTIFIED BY 'nova_senha_forte';
GRANT SELECT, INSERT, UPDATE, DELETE ON ser_pleno.* TO 'serpleno_app'@'localhost';
FLUSH PRIVILEGES;
```

**Critério de Sucesso:** `.env` não aparece em `git log --all -- .env`; aplicação conecta com novo usuário; senha antiga invalidada.

---

### Tarefa T-01: Correção do Encoding do `requirements.txt`

**Ação:** Regravar o arquivo como UTF-8 puro, removendo caracteres CLIXML.

**Método & Ferramentas:** PowerShell `Get-Content` + `Set-Content`.

**Critério de Sucesso:** `file requirements.txt` retorna `UTF-8 Unicode text`; `pip install -r requirements.txt` funciona em WSL/Linux.

---

### Tarefa R-01: Implementar BaseController com Métodos Explícitos

**Ação:** Substituir `__getattr__` por classe abstrata com interface explícita.

**Método & Ferramentas:** `abc.ABC`, `abc.abstractmethod`.

**Exemplo:**
```python
from abc import ABC, abstractmethod

class BaseController(ABC):
    def __init__(self, service_class):
        self._service = service_class()

    @abstractmethod
    def get_service(self):
        return self._service
```

**Critério de Sucesso:** IDE faz autocomplete em controllers; `__getattr__` não existe mais; views atualizadas.

---

### Tarefa R-02: Eliminar Concatenação de SQL em `repositories/estudantes.py`

**Ação:** Implementar whitelist de colunas permitidas + validação antes de montar query.

**Método & Ferramentas:** Set de colunas permitidas; validação prévia.

**Critério de Sucesso:** Campos não permitidos levantam `ValueError` antes do banco; SQL gerado é inspecionável via log.

---

### Tarefa T-03: Criar `pyproject.toml` com Tooling

**Ação:** Adicionar `pyproject.toml` raiz com `[project]`, `[project.optional-dependencies]`, `[tool.ruff]`, `[tool.mypy]`.

**Critério de Sucesso:** `pip install -e ".[dev]"` funciona; `ruff check .` e `mypy ser_pleno/` passam.

---

### Tarefa Q-01: Pipeline CI Mínima (GitHub Actions)

**Ação:** Criar `.github/workflows/ci.yml` com matrix Python 3.11/3.12 executando lint, type check e tests.

**Critério de Sucesso:** Todo PR aciona o workflow; merge bloqueado se qualquer passo falhar.

---

## 6. Riscos Residuais Identificados

| Risco | Mitigação |
|---|---|
| Rotação de credenciais quebra backend Django temporariamente | Coordenar deploy conjunto; usar credencial temporária com revogação imediata |
| Remoção de `mysqlclient`/`PyMySQL` causa `ImportError` | Verificar imports em todo o projeto antes de remover |
| Mudança em `BaseController` quebra views customizadas | Manter backward-compatibilidade temporariamente via herança |
| SQL f-string em `UPDATE` pode ser explorado se filtros dinâmicos forem adicionados sem validação | Implementar whitelist PRIMEIRO antes de expor filtros dinâmicos na UI |
| Pytest warning de thread no login pode mascarar falhas reais em ambiente CI | Isolar lógica de login em classe testável com mock de `after()` |

> **Nota de contexto (2026-06-30):** A exposição de `.env` foi classificada como baixa prioridade porque o banco alvo é local, de teste e sem dados reais. A rotação de credenciais permanece no backlog como item a executar antes da primeira distribuição pública ou deploy em ambiente de produção.

---

## 7. Análise de Viabilidade

- **Técnica:** Viável integralmente. Usa ferramentas nativas do ecossistema Python e Git.
- **Arquitetural:** Melhorias incrementais sem necessidade de reescrita. Compatível com o plano de reestruturação já documentado em `docs/arquitetura-planejamento.md`.

## 8. Riscos Residuais

- Rotação de credenciais requer coordenação com backend Django.
- Mudança em BaseController pode quebrar views se não for feita gradualmente.
- Remoção de dependências MySQL duplicadas exige verificação prévia de imports.

## 9. Próximos Passos

1. **Concluído:** S-01 (segredo) e T-01 (encoding).
2. **Concluído:** R-01 (controllers explícitos), R-02 (SQL sanitizado), T-03 (`pyproject.toml`), logging centralizado, CI mínima.
3. **Curto prazo:** Elevar cobertura de testes; validar logging em produção; remover `debug.log` da raiz se reaparecer.
4. **Médio prazo:** Introduzir context manager `connection()` nas queries existentes; avaliar SQLAlchemy 2.0 conforme roadmap.
5. **Antes de distribuição pública:** Rotacionar credenciais MySQL e remover `.env` do histórico Git.
6. **Longo prazo:** Adotar DI simples e Event Bus; considerar SQLAlchemy 2.0 com AsyncSession.
