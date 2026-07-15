# SerPleno Desktop

Aplicativo desktop para gestão escolar, desenvolvido com Python e CustomTkinter. Suporta operação online (MySQL) e offline (SQLite) com sincronização bidirecional.

## Funcionalidades

- Autenticação de usuários
- Dashboard com KPIs e notificações
- Gestão de estudantes
- Agenda de atendimentos
- Registro de bem-estar e humor
- Triagens e orientações
- Quadro de avisos e comunicação interna
- Relatórios e exportação
- Configurações de usuário

## Stack

- **Linguagem:** Python >= 3.11
- **UI:** CustomTkinter 5.2+
- **Banco de dados:** MySQL (online) + SQLite (offline/local)
- **Testes:** pytest (166 testes)

## Arquitetura

```
Presentation (views + components)
    ↓
Controllers (mediação explícita)
    ↓
Services (lógica de negócio + fallback API/local)
    ↓
Repositories (MySQL com fallback SQLite)
```

Documentação detalhada em `docs/desenvolvimento.md`.

## Execução

```powershell
python app.py
```

## Testes

```powershell
pytest -v --tb=short
```

## Build

Consulte `BUILD_DESKTOP.md` para gerar o executável.

## Documentação

- `docs/desenvolvimento.md` — Guia do desenvolvedor e convenções
- `docs/arquitetura-planejamento.md` — Histórico de reestruturação
- `docs/adr/` — Architecture Decision Records
