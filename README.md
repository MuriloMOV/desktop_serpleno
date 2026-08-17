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
- **Testes:** pytest

## Estrutura de Pastas

```
desktop_serpleno/
├── src/ser_pleno/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── application/
│   │   ├── controllers/
│   │   └── services/
│   ├── config/
│   │   ├── config.py
│   │   ├── db_config.py
│   │   ├── operation_mode.py
│   │   └── paths.py
│   ├── domain/
│   │   └── models/
│   ├── features/
│   │   ├── agenda/
│   │   ├── alertas/
│   │   ├── analytics/
│   │   ├── audit_logs/
│   │   ├── avisos/
│   │   ├── bem_estar/
│   │   ├── compartilhamento/
│   │   ├── comunicacao/
│   │   ├── configuracoes/
│   │   ├── dashboard/
│   │   ├── estudantes/
│   │   ├── metas/
│   │   ├── notificacoes/
│   │   ├── orientacoes/
│   │   ├── pedidos_ajuda/
│   │   ├── relatorio/
│   │   ├── report_template/
│   │   └── triagem/
│   ├── infrastructure/
│   │   ├── api/
│   │   ├── db/
│   │   ├── desktop/
│   │   └── local/
│   ├── repositories/
│   ├── ui/
│   │   ├── components/
│   │   ├── theme/
│   │   ├── navigation.py
│   │   ├── theme_manager.py
│   │   ├── view_factory.py
│   │   └── views/
│   └── utils/
├── assets/
├── config/
├── data/
├── docs/
├── sql/
├── tests/
└── uploads/
```

## Execução

```powershell
python -m ser_pleno
```

## Testes

```powershell
pytest -v --tb=short
```

## Build

Consulte `BUILD_DESKTOP.md` para gerar o executável.

### Build automatizado

```powershell
python scripts/build_exe.py --name SerPleno --onefile --windowed
```

O executável será gerado em `dist/`.

## Release

### Via script (local)

```powershell
.\scripts\release.ps1 -Version 1.0.1
```

O script irá:
1. Executar `pytest tests/`
2. Executar `ruff check src/ser_pleno tests`
3. Executar `mypy src/ser_pleno`
4. Gerar o executável
5. Criar `releases/<versao>/` com o executável e assets necessários

Para pular testes:

```powershell
.\scripts\release.ps1 -Version 1.0.1 -SkipTests
```

### Via GitHub Actions

Crie uma tag e push para gerar release automaticamente:

```powershell
git tag v1.0.1
git push origin v1.0.1
```

O workflow `.github/workflows/release.yml` dispara em tags `v*` e publica a release com o executável como asset.

## Como Contribuir

1. Crie uma branch a partir de `main`:
   ```powershell
   git checkout -b feat/nome-da-feature
   ```
2. Implemente a mudança seguindo a organização por feature (`src/ser_pleno/features/<nome_feature>/`).
3. Garanta que os testes passam:
   ```powershell
   pytest -v --tb=short
   ```
4. Abra um Pull Request descrevendo a mudança.

## Documentação

- `docs/plano-reestruturacao.md` — Histórico e status da reestruturação arquitetural
- `docs/desenvolvimento.md` — Guia do desenvolvedor e convenções
- `docs/MODO_INDEPENDENTE.md` — Configuração para operação offline
- `BUILD_DESKTOP.md` — Instruções de build e distribuição
