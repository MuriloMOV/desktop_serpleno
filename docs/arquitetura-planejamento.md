# Documentação Arquitetural — SerPleno Desktop

**Data:** 2026-07-06
**Contexto:** Projeto `ser_pleno` — Desktop Application (CustomTkinter) com backend Django/MySQL
**Status:** Estrutura reorganizada e validação verde

---

## 1. Estrutura de Pastas Atual

```
desktop_serpleno/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── REORGANIZACAO_PLANO.md
├── BUILD_DESKTOP.md
├── src/ser_pleno/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── config/
│   ├── ui/
│   ├── domain/
│   ├── infrastructure/
│   │   └── api/
│   ├── application/
│   │   ├── services/
│   │   └── controllers/
│   ├── presentation/
│   │   ├── views/
│   │   └── components/
│   ├── repositories/
│   ├── utils/
│   └── scripts/
├── tests/
│   ├── unit/
│   ├── ui/
│   ├── integration/
│   └── fixtures/
├── user_data/
├── build/
├── dist/
└── docs/
    └── arquitetura-planejamento.md
```

## 2. Arquitetura

O projeto segue Clean Architecture simplificada:
- `presentation/` → views e components
- `application/controllers` → orquestração
- `application/services` → casos de uso e regras de negócio
- `repositories/` → acesso a dados
- `infrastructure/` → HTTP, MySQL, SO
- `domain/` → entidades puras
- `config/` → configurações gerais
- `ui/` → Design System
- `utils/` → utilidades transversais

## 3. Checklist de Implementação

### Concluído
- [x] Estrutura `src/` layout com pacote `ser_pleno/`
- [x] Ponto de entrada `__main__.py`
- [x] `pyproject.toml` com dependências e pytest
- [x] Reorganização em camadas
- [x] Controllers implementados
- [x] Repository layer implementada
- [x] Services refatorados para usar repositories
- [x] Componentes reutilizáveis de UI
- [x] Design System centralizado
- [x] Testes organizados: 20 passed
- [x] Encoding UTF-8 sem BOM
- [x] Pasta `tkclaude/` removida

### Futuro
- [ ] Adotar tipagem stricter (mypy)
- [ ] Considerar SQLAlchemy 2.0
- [ ] DI simples / Event Bus
- [ ] Testes de integração para repositories

## 4. Critérios de Sucesso

| Item | Métrica | Status |
|---|---|---|
| Estrutura `src/` | Código em `src/ser_pleno/` | ✅ |
| Ponto de entrada | `python -m ser_pleno` | ✅ |
| Repository layer | SQL isolado em repositories | ✅ |
| Testes | `pytest tests` passa | ✅ 20 passed |
| Encoding | UTF-8 sem BOM | ✅ |

---

*Documento atualizado em 2026-07-06*
